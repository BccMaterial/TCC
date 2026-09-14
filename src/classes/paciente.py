import uuid

from enums.suspeitas import Suspeita


class Paciente:
    """
    Representa um paciente para ser utilizado no SimPy

    Os atributos são usados pelo simulador para controlar o fluxo de triagem e avaliações.

    Atributos:
        id: UUID
            ID de identificação do paciente
        suspeita : Suspeita
            Nome do transtorno que o paciente apresenta.
        num_avaliacoes : int, default=0
            Número de avaliações já realizadas para esse paciente.
        triagem_feita : bool, default=False
            Indica se a triagem foi concluída.
    """

    def __init__(
        self, suspeita: Suspeita, num_avaliacoes: int = 0, triagem_feita: bool = False
    ) -> None:
        self.id: uuid.UUID = uuid.uuid4()
        self.suspeita: Suspeita = suspeita
        self.num_avaliacoes: int = num_avaliacoes
        self.triagem_feita: bool = triagem_feita
