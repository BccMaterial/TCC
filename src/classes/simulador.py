import csv
import json
import random
from pathlib import Path

from enums import Suspeita

from .equipe import Equipe
from .horario_trabalho import HorarioTrabalho
from .paciente import Paciente
from .parametros import Parametros


class Simulador:
    """Executa e apresenta os resultados de uma simulação de atendimentos."""

    equipe: Equipe
    pacientes: list[Paciente]
    parametros: Parametros | None
    tempo_avaliacao: tuple[float, float]
    agendamentos_simulados: int
    nao_compareceram: int

    def __init__(
        self,
        equipe: Equipe,
        pacientes: list[Paciente] | None = None,
        parametros: Parametros | None = None,
        tempo_avaliacao: tuple[float, float] = (30, 60),
    ) -> None:
        if (
            len(tempo_avaliacao) != 2
            or tempo_avaliacao[0] <= 0
            or tempo_avaliacao[1] < tempo_avaliacao[0]
        ):
            raise ValueError("Informe um intervalo válido para a duração da avaliação.")

        self.equipe = equipe
        self.pacientes = pacientes if pacientes is not None else []
        self.parametros = parametros
        self.tempo_avaliacao = tempo_avaliacao
        self.agendamentos_simulados = 0
        self.nao_compareceram = 0
        self.horario_trabalho = HorarioTrabalho(
            dia_semana_inicial=(
                parametros.dia_semana_inicial if parametros is not None else 0
            ),
            minuto_inicio=(
                parametros.minuto_inicio_simulacao
                if parametros is not None
                else HorarioTrabalho.INICIO_EXPEDIENTE
            ),
        )
        for profissional in equipe.profissionais:
            profissional.horario_trabalho = self.horario_trabalho

        if parametros is not None:
            if parametros.probabilidade_no_show is None:
                raise ValueError(
                    "É necessário ao menos um status 'Falta' ou 'Concluída' "
                    "para estimar a probabilidade de no-show."
                )

    def iniciar(self, duracao: float = 480) -> None:
        """Inicia a chegada de pacientes e executa a simulação."""
        if self.parametros is not None:
            duracao = self.parametros.duracao_simulacao
        if duracao <= 0:
            raise ValueError("A duração da simulação deve ser maior que zero.")

        self.equipe.monitorar(intervalo=1)
        processo = (
            self._chegada_parametrizada()
            if self.parametros is not None
            else self._chegada_pacientes()
        )
        self.equipe.env.process(processo)
        self.equipe.env.run(until=duracao)

    def _paciente(self, paciente: Paciente):
        env = self.equipe.env
        while not paciente.diagnostico_concluido:
            profissional = yield self.equipe.request()
            try:
                tempo_restante = random.uniform(*self.tempo_avaliacao)
                tempo_trabalhado = 0.0
                while tempo_restante > 0:
                    if not self.horario_trabalho.em_expediente(env.now):
                        profissional.em_atendimento = False
                        espera = self.horario_trabalho.minutos_ate_proximo_expediente(
                            env.now
                        )
                        yield env.timeout(espera)
                        continue

                    duracao_trecho = min(
                        tempo_restante,
                        self.horario_trabalho.minutos_ate_fechamento(env.now),
                    )
                    profissional.em_atendimento = True
                    yield env.timeout(duracao_trecho)
                    profissional.em_atendimento = False
                    tempo_trabalhado += duracao_trecho
                    tempo_restante -= duracao_trecho

                profissional.registrar_atendimento(tempo_trabalhado)
                paciente.registrar_avaliacao()
            finally:
                profissional.em_atendimento = False
                self.equipe.release(profissional)

    def _chegada_pacientes(self):
        env = self.equipe.env
        while True:
            if not self.horario_trabalho.em_expediente(env.now):
                espera = self.horario_trabalho.minutos_ate_proximo_expediente(env.now)
                yield env.timeout(espera)
                continue

            intervalo = random.expovariate(1 / 20)
            ate_fechamento = self.horario_trabalho.minutos_ate_fechamento(env.now)
            if intervalo >= ate_fechamento:
                yield env.timeout(ate_fechamento)
                continue
            yield env.timeout(intervalo)
            paciente = Paciente(
                random.choice(list(Suspeita)),
                num_avaliacoes_necessarias=(
                    self.parametros.amostrar_quantidade_avaliacoes()
                    if self.parametros is not None
                    else 1
                ),
            )
            self.pacientes.append(paciente)
            env.process(self._paciente(paciente))

    def _chegada_parametrizada(self):
        env = self.equipe.env
        parametros = self.parametros
        if parametros is None:
            return

        while True:
            if not self.horario_trabalho.em_expediente(env.now):
                espera = self.horario_trabalho.minutos_ate_proximo_expediente(env.now)
                yield env.timeout(espera)
                continue

            minuto_agenda = parametros.minuto_inicio_simulacao + env.now
            hora_total = int(minuto_agenda // 60)
            proxima_hora = (hora_total + 1) * 60 - parametros.minuto_inicio_simulacao
            hora = hora_total % 24
            taxa_horaria = parametros.taxa_agendamentos_por_hora.get(hora, 0)
            limite_intervalo = min(
                proxima_hora,
                env.now + self.horario_trabalho.minutos_ate_fechamento(env.now),
            )
            if taxa_horaria <= 0:
                yield env.timeout(limite_intervalo - env.now)
                continue
            while env.now < limite_intervalo:
                intervalo = random.expovariate(taxa_horaria / 60)
                if env.now + intervalo >= limite_intervalo:
                    yield env.timeout(limite_intervalo - env.now)
                    break
                yield env.timeout(intervalo)
                self.agendamentos_simulados += 1
                if random.random() < parametros.probabilidade_no_show:
                    self.nao_compareceram += 1
                    continue
                paciente = Paciente(
                    parametros.amostrar_suspeita(),
                    num_avaliacoes_necessarias=(
                        parametros.amostrar_quantidade_avaliacoes()
                    ),
                )
                self.pacientes.append(paciente)
                env.process(self._paciente(paciente))

    def resumo(self) -> list[dict[str, float | int | str]]:
        """Exibe o resumo da simulação e retorna as métricas dos profissionais."""
        resumos = self.equipe.resumos()
        print("\n=== Resumo da simulação ===")
        print(f"Pacientes que chegaram: {len(self.pacientes)}")
        if self.parametros is not None:
            print(f"Agendamentos gerados: {self.agendamentos_simulados}")
            print(f"Não compareceram: {self.nao_compareceram}")
        exames_concluidos = sum(paciente.num_avaliacoes for paciente in self.pacientes)
        pacientes_diagnosticados = sum(
            paciente.diagnostico_concluido for paciente in self.pacientes
        )
        print(f"Exames concluídos: {exames_concluidos}")
        print(f"Pacientes com ciclo concluído: {pacientes_diagnosticados}")
        print(
            "Pacientes com ciclo incompleto: "
            f"{len(self.pacientes) - pacientes_diagnosticados}"
        )

        for resumo in resumos:
            print(f"\n=== Métricas de {resumo['nome']} ===")
            print(f"Atendimentos concluídos: {resumo['pacientes_atendidos']}")
            print(
                "Tempo médio de atendimento: "
                f"{resumo['tempo_medio_atendimento']:.2f} min"
            )
            print(f"Tempo ocioso: {resumo['tempo_ocioso']:.2f} min")
            print(f"Taxa de ocupação: {resumo['taxa_ocupacao']:.2%}")
            print(f"Amostras da série temporal: " f"{len(resumo['serie_temporal'])}")

        return resumos

    def exportar(self) -> Path:
        """Exporta os resumos profissionais para `./output/data.csv`."""
        destino = Path("output/data.csv")
        destino.parent.mkdir(parents=True, exist_ok=True)
        resumos = self.equipe.resumos()
        colunas = [
            "nome",
            "pacientes_atendidos",
            "tempo_total_atendimento",
            "tempo_medio_atendimento",
            "tempo_ocioso",
            "taxa_ocupacao",
            "serie_temporal",
        ]

        with destino.open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=colunas)
            escritor.writeheader()
            for resumo in resumos:
                linha = resumo.copy()
                linha["serie_temporal"] = json.dumps(linha["serie_temporal"])
                escritor.writerow(linha)

        return destino
