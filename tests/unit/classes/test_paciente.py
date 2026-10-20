import uuid

from classes import Paciente
from enums import Suspeita


def test_when_creating_patient_with_default_values():
    paciente = Paciente(Suspeita.AUTISMO)

    assert isinstance(paciente.id, uuid.UUID)
    assert paciente.suspeita is Suspeita.AUTISMO
    assert paciente.num_avaliacoes == 0
    assert paciente.triagem_feita is False


def test_when_creating_patient_with_custom_values():
    paciente = Paciente(Suspeita.TDAH, num_avaliacoes=2, triagem_feita=True)

    assert paciente.suspeita is Suspeita.TDAH
    assert paciente.num_avaliacoes == 2
    assert paciente.triagem_feita is True
