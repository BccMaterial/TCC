import uuid

from classes import Paciente
from enums import Suspeita


def test_when_creating_patient_with_default_values():
    paciente = Paciente(Suspeita.AUTISMO)

    assert isinstance(paciente.id, uuid.UUID)
    assert paciente.suspeita is Suspeita.AUTISMO
    assert paciente.num_avaliacoes == 0
    assert paciente.num_avaliacoes_necessarias == 1
    assert paciente.diagnostico_concluido is False
    assert paciente.triagem_feita is False


def test_when_creating_patient_with_custom_values():
    paciente = Paciente(
        Suspeita.TDAH,
        num_avaliacoes=2,
        triagem_feita=True,
        num_avaliacoes_necessarias=3,
    )

    assert paciente.suspeita is Suspeita.TDAH
    assert paciente.num_avaliacoes == 2
    assert paciente.num_avaliacoes_necessarias == 3
    assert paciente.diagnostico_concluido is False
    assert paciente.triagem_feita is True


def test_when_completing_required_evaluations_patient_is_diagnosed():
    paciente = Paciente(Suspeita.TDAH, num_avaliacoes_necessarias=2)

    paciente.registrar_avaliacao()
    assert paciente.num_avaliacoes == 1
    assert paciente.diagnostico_concluido is False

    paciente.registrar_avaliacao()
    assert paciente.num_avaliacoes == 2
    assert paciente.diagnostico_concluido is True
