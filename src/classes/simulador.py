import csv
import json
import random
from pathlib import Path

from enums import Suspeita

from .equipe import Equipe
from .paciente import Paciente


class Simulador:
    """Executa e apresenta os resultados de uma simulação de atendimentos."""

    def __init__(self, equipe: Equipe, pacientes: list[Paciente] | None = None) -> None:
        self.equipe = equipe
        self.pacientes = pacientes if pacientes is not None else []

    def iniciar(self, duracao: float = 480) -> None:
        """Inicia a chegada de pacientes e executa a simulação."""
        self.equipe.monitorar(intervalo=1)
        self.equipe.env.process(self._chegada_pacientes())
        self.equipe.env.run(until=duracao)

    def _paciente(self, paciente: Paciente):
        env = self.equipe.env
        profissional = yield self.equipe.request()
        try:
            tempo_avaliacao = random.uniform(30, 60)
            inicio_atendimento = env.now
            yield env.timeout(tempo_avaliacao)
            profissional.registrar_atendimento(inicio_atendimento, env.now)
        finally:
            self.equipe.release(profissional)

    def _chegada_pacientes(self):
        env = self.equipe.env
        while True:
            paciente = Paciente(random.choice(list(Suspeita)))
            self.pacientes.append(paciente)
            env.process(self._paciente(paciente))

            intervalo = random.expovariate(1 / 20)
            yield env.timeout(intervalo)

    def resumo(self) -> list[dict[str, float | int | str]]:
        """Exibe o resumo da simulação e retorna as métricas dos profissionais."""
        resumos = self.equipe.resumos()
        total_atendidos = sum(resumo["pacientes_atendidos"] for resumo in resumos)
        print("\n=== Resumo da simulação ===")
        print(f"Pacientes que chegaram: {len(self.pacientes)}")
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
