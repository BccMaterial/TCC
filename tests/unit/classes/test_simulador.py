import simpy

from classes import Equipe, Simulador


def test_when_creating_simulator_with_team_and_patients():
    equipe = Equipe(simpy.Environment(), quantidade=1)
    pacientes = []

    simulador = Simulador(equipe, pacientes)

    assert simulador.equipe is equipe
    assert simulador.pacientes is pacientes


def test_when_creating_simulator_without_patients():
    equipe = Equipe(simpy.Environment(), quantidade=1)

    simulador = Simulador(equipe)

    assert simulador.equipe is equipe
    assert simulador.pacientes == []
