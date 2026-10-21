import csv
import json
import random
from pathlib import Path

from enums import Suspeita

from .equipe import Equipe
from .paciente import Paciente
from .parametros import Parametros


class Simulador:
    """Executa e apresenta os resultados de uma simulação de atendimentos."""

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
        if parametros is not None:
            if parametros.probabilidade_no_show is None:
                raise ValueError(
                    "É necessário ao menos um status 'Falta' ou 'Concluída' "
                    "para estimar a probabilidade de no-show."
                )
            ids_equipe = {str(profissional.id) for profissional in equipe.profissionais}
            ids_ausentes = set(parametros.probabilidades_profissionais) - ids_equipe
            if ids_ausentes:
                raise ValueError(
                    "A equipe deve incluir profissionais com os IDs dos dados: "
                    + ", ".join(sorted(ids_ausentes))
                )

    def iniciar(self, duracao: float = 480) -> None:
        """Inicia a chegada de pacientes e executa a simulação."""
        self.equipe.monitorar(intervalo=1)
        processo = (
            self._chegada_parametrizada()
            if self.parametros is not None
            else self._chegada_pacientes()
        )
        self.equipe.env.process(processo)
        self.equipe.env.run(until=duracao)

    def _paciente(self, paciente: Paciente, id_profissional: str | None = None):
        env = self.equipe.env
        if id_profissional is None:
            profissional = yield self.equipe.request()
            requisicao = None
        else:
            profissional = next(
                item
                for item in self.equipe.profissionais
                if str(item.id) == str(id_profissional)
            )
            requisicao = profissional.resource.request()
            yield requisicao
        try:
            tempo_avaliacao = random.uniform(*self.tempo_avaliacao)
            inicio_atendimento = env.now
            yield env.timeout(tempo_avaliacao)
            profissional.registrar_atendimento(inicio_atendimento, env.now)
        finally:
            if requisicao is None:
                self.equipe.release(profissional)
            else:
                profissional.resource.release(requisicao)

    def _chegada_pacientes(self):
        env = self.equipe.env
        while True:
            paciente = Paciente(random.choice(list(Suspeita)))
            self.pacientes.append(paciente)
            env.process(self._paciente(paciente))

            intervalo = random.expovariate(1 / 20)
            yield env.timeout(intervalo)

    def _chegada_parametrizada(self):
        env = self.equipe.env
        parametros = self.parametros
        if parametros is None:
            return

        while True:
            minuto_agenda = parametros.minuto_inicio_simulacao + env.now
            hora_total = int(minuto_agenda // 60)
            proxima_hora = (hora_total + 1) * 60 - parametros.minuto_inicio_simulacao
            dia = hora_total // 24
            dia_semana = (parametros.dia_semana_inicial + dia) % 7
            hora = hora_total % 24
            taxa_horaria = parametros.taxa_agendamentos_por_hora.get(
                (dia_semana, hora), 0
            )
            if taxa_horaria <= 0:
                yield env.timeout(proxima_hora - env.now)
                continue
            while env.now < proxima_hora:
                intervalo = random.expovariate(taxa_horaria / 60)
                if env.now + intervalo >= proxima_hora:
                    yield env.timeout(proxima_hora - env.now)
                    break
                yield env.timeout(intervalo)
                self.agendamentos_simulados += 1
                if random.random() < parametros.probabilidade_no_show:
                    self.nao_compareceram += 1
                    continue
                paciente = Paciente(parametros.amostrar_suspeita())
                self.pacientes.append(paciente)
                env.process(
                    self._paciente(paciente, parametros.amostrar_profissional())
                )

    def resumo(self) -> list[dict[str, float | int | str]]:
        """Exibe o resumo da simulação e retorna as métricas dos profissionais."""
        resumos = self.equipe.resumos()
        total_atendidos = sum(resumo["pacientes_atendidos"] for resumo in resumos)
        print("\n=== Resumo da simulação ===")
        print(f"Pacientes que chegaram: {len(self.pacientes)}")
        if self.parametros is not None:
            print(f"Agendamentos gerados: {self.agendamentos_simulados}")
            print(f"Não compareceram: {self.nao_compareceram}")
        print(f"Pacientes atendidos: {total_atendidos}")
        print(
            f"Pacientes ainda não atendidos: "
            f"{len(self.pacientes) - total_atendidos}"
        )

        for resumo in resumos:
            print(f"\n=== Métricas de {resumo['nome']} ===")
            print(f"Pacientes atendidos: {resumo['pacientes_atendidos']}")
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
