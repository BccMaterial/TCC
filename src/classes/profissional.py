import uuid
from collections.abc import Generator

import simpy

from .horario_trabalho import HorarioTrabalho


class Profissional:
    """
    Representa um profissional que atende pacientes no SimPy.

    Encapsula um simpy.Resource e coleta métricas do atendimento,
    como número de pacientes atendidos, tempo ocupado e a série
    temporal da ocupação ao longo da simulação.

    Atributos:
        id: UUID
            ID de identificação do profissional
        nome : str
            Nome de exibição do profissional
        capacidade : int, default=1
            Quantidade de atendimentos simultâneos do profissional.
        resource: simpy.Resource
            Recurso SimPy responsável pela fila de atendimento.
        num_pacientes_atendidos : int, default=0
            Quantidade de pacientes atendidos pelo profissional.
        tempo_total_atendimento : float, default=0.0
            Tempo total (em minutos) ocupado com atendimentos.
    """

    def __init__(
        self,
        env: simpy.Environment,
        nome: str | None = None,
        id_profissional: str | None = None,
    ) -> None:
        if id_profissional is not None and not id_profissional.strip():
            raise ValueError("O ID do profissional não pode ser vazio.")
        self.id: uuid.UUID | str = (
            id_profissional if id_profissional is not None else uuid.uuid4()
        )
        self.nome: str = nome or f"Profissional {str(self.id)[:8]}"
        self.env: simpy.Environment = env
        self.resource: simpy.Resource = simpy.Resource(env, capacity=1)
        self.horario_trabalho = HorarioTrabalho()

        self.num_pacientes_atendidos: int = 0
        self.tempo_total_atendimento: float = 0.0
        self.em_atendimento = False
        self._amostras: list[tuple[float, int]] = []

    def request(self) -> simpy.Request:
        """Solicita o recurso do profissional (usado com `with`)."""
        return self.resource.request()

    def registrar_atendimento(self, duracao: float) -> None:
        """Registra o tempo efetivamente trabalhado em um atendimento concluído."""
        self.num_pacientes_atendidos += 1
        self.tempo_total_atendimento += duracao

    def monitorar(self, intervalo: float = 1.0) -> Generator[simpy.Event, None, None]:
        """
        Processo do SimPy que amostra a ocupação do profissional.

        Coleta o número de recursos ocupados em `self._amostras` a cada
        `intervalo` minutos, formando a série temporal da ocupação.
        """
        while True:
            self._amostras.append((self.env.now, int(self.em_atendimento)))
            yield self.env.timeout(intervalo)

    @property
    def tempo_simulado(self) -> float:
        """Tempo total da simulação até o momento atual."""
        return self.env.now

    @property
    def taxa_ocupacao(self) -> float:
        """Fração do tempo em que o profissional esteve ocupado."""
        if self.tempo_jornada == 0:
            return 0.0
        return self.tempo_total_atendimento / self.tempo_jornada

    @property
    def tempo_ocioso(self) -> float:
        """Tempo útil em que o profissional ficou sem atender pacientes."""
        return max(self.tempo_jornada - self.tempo_total_atendimento, 0.0)

    @property
    def tempo_jornada(self) -> float:
        """Tempo de expediente ocorrido até o momento atual da simulação."""
        return self.horario_trabalho.minutos_uteis(0, self.tempo_simulado)

    @property
    def tempo_medio_atendimento(self) -> float:
        """Duração média dos atendimentos realizados."""
        if self.num_pacientes_atendidos == 0:
            return 0.0
        return self.tempo_total_atendimento / self.num_pacientes_atendidos

    def resumo(self) -> dict[str, float | int | str]:
        """Resumo das métricas do profissional."""
        return {
            "nome": self.nome,
            "pacientes_atendidos": self.num_pacientes_atendidos,
            "tempo_total_atendimento": self.tempo_total_atendimento,
            "tempo_medio_atendimento": self.tempo_medio_atendimento,
            "tempo_ocioso": self.tempo_ocioso,
            "taxa_ocupacao": self.taxa_ocupacao,
            "serie_temporal": self._amostras,
        }

    def __str__(self) -> str:
        return self.nome
