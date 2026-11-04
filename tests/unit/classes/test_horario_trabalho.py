import pytest

from classes.horario_trabalho import HorarioTrabalho


def test_horario_de_trabalho_segue_dias_uteis_e_limites_do_expediente():
    horario = HorarioTrabalho()

    assert horario.em_expediente(0)
    assert horario.em_expediente(8 * 60 + 59)
    assert not horario.em_expediente(3 * 60)
    assert horario.minutos_ate_proximo_expediente(3 * 60) == 60
    assert not horario.em_expediente(9 * 60)
    assert horario.minutos_ate_proximo_expediente(9 * 60) == 15 * 60
    assert horario.minutos_ate_proximo_expediente(5 * 24 * 60) == 2 * 24 * 60
    assert horario.minutos_ate_fechamento(2 * 60 + 30) == 30


def test_horario_calcula_minutos_uteis_sem_contar_noites_e_fins_de_semana():
    horario = HorarioTrabalho()

    assert horario.minutos_uteis(0, 7 * 24 * 60) == 5 * 8 * 60


def test_minutos_uteis_incluem_inicio_parcial_do_expediente():
    horario = HorarioTrabalho(dia_semana_inicial=0, minuto_inicio=14 * 60)

    assert horario.minutos_uteis(0, 24 * 60) == 8 * 60
