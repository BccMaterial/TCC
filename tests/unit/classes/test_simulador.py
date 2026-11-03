import simpy

from classes import Equipe, Paciente, Simulador
from enums import Suspeita


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


def test_simulador_sem_parametros_preserva_geracao_de_chegadas(monkeypatch):
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)
    simulador = Simulador(equipe)
    monkeypatch.setattr("classes.simulador.random.expovariate", lambda _: 10)

    simulador.iniciar(duracao=30)

    assert simulador.parametros is None
    assert len(simulador.pacientes) == 2


def test_atendimento_pausa_no_fechamento_e_continua_no_proximo_dia_util():
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)
    simulador = Simulador(equipe, tempo_avaliacao=(60, 60))
    paciente = Paciente(Suspeita.AUTISMO)

    def iniciar_atendimento_no_fim_do_expediente():
        yield env.timeout(8 * 60 + 30)
        yield env.process(simulador._paciente(paciente))

    env.process(iniciar_atendimento_no_fim_do_expediente())
    env.run(until=24 * 60 + 31)

    profissional = equipe.profissionais[0]
    assert profissional.num_pacientes_atendidos == 1
    assert profissional.tempo_total_atendimento == 60
    assert profissional.tempo_jornada == 9 * 60 + 31
    assert profissional.taxa_ocupacao == 60 / (9 * 60 + 31)
