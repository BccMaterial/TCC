import uuid

from enums import Suspeita


class Paciente:
    """
    Representa um paciente para ser utilizado no SimPy

    Os atributos são usados pelo simulador para controlar o fluxo de triagem e avaliações.

    Atributos:
        id: UUID
            ID de identificação do paciente
        suspeita : Suspeita
            Suspeita inicial registrada para esse paciente.
        num_avaliacoes : int, default=0
            Número de avaliações já realizadas para esse paciente.
        num_avaliacoes_necessarias : int, default=1
            Número de avaliações necessárias antes da conclusão diagnóstica.
        diagnostico_concluido : bool
            Indica se todas as avaliações necessárias foram concluídas.
        triagem_feita : bool, default=False
            Indica se a triagem foi concluída.
    """

    def __init__(
        self,
        suspeita: Suspeita,
        num_avaliacoes: int = 0,
        triagem_feita: bool = False,
        num_avaliacoes_necessarias: int = 1,
    ) -> None:
        if num_avaliacoes_necessarias <= 0:
            raise ValueError("O paciente deve precisar de ao menos uma avaliação.")
        if num_avaliacoes < 0 or num_avaliacoes > num_avaliacoes_necessarias:
            raise ValueError(
                "O número de avaliações realizadas deve estar entre zero "
                "e o número necessário."
            )

        self.id: uuid.UUID = uuid.uuid4()
        self.suspeita: Suspeita = suspeita
        self.num_avaliacoes: int = num_avaliacoes
        self.num_avaliacoes_necessarias: int = num_avaliacoes_necessarias
        self.diagnostico_concluido: bool = num_avaliacoes == num_avaliacoes_necessarias
        self.triagem_feita: bool = triagem_feita

    def registrar_avaliacao(self) -> None:
        """Registra uma avaliação concluída e atualiza o estado diagnóstico."""
        if self.diagnostico_concluido:
            raise ValueError("Todas as avaliações necessárias já foram concluídas.")
        self.num_avaliacoes += 1
        if self.num_avaliacoes == self.num_avaliacoes_necessarias:
            self.diagnostico_concluido = True
