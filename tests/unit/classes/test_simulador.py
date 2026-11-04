from datetime import datetime

import simpy

from classes import Equipe, Paciente, Parametros, RegistroAgenda, Simulador
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
    assert profissional.tempo_jornada == 8 * 60 + 31
    assert profissional.taxa_ocupacao == 60 / (8 * 60 + 31)


def test_atendimento_pausa_no_almoco_e_continua_apos_intervalo():
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)
    simulador = Simulador(equipe, tempo_avaliacao=(60, 60))
    paciente = Paciente(Suspeita.AUTISMO)

    def iniciar_atendimento_antes_do_almoco():
        yield env.timeout(2 * 60 + 30)
        yield env.process(simulador._paciente(paciente))

    env.process(iniciar_atendimento_antes_do_almoco())
    env.run(until=4 * 60 + 31)

    profissional = equipe.profissionais[0]
    assert profissional.num_pacientes_atendidos == 1
    assert profissional.tempo_total_atendimento == 60
    assert profissional.tempo_jornada == 3 * 60 + 31


def test_paciente_realiza_todos_os_exames_antes_da_conclusao():
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)
    simulador = Simulador(equipe, tempo_avaliacao=(30, 30))
    paciente = Paciente(Suspeita.AUTISMO, num_avaliacoes_necessarias=2)

    env.process(simulador._paciente(paciente))
    env.run(until=61)

    assert paciente.num_avaliacoes == 2
    assert paciente.diagnostico_concluido is True
    assert equipe.profissionais[0].num_pacientes_atendidos == 2


def test_simulador_parametrizado_usa_fila_unica_com_multiplos_canais(monkeypatch):
    inicio = datetime.fromisoformat("2026-10-19T09:00:00-03:00")
    parametros = Parametros(
        [
            RegistroAgenda(
                "p1",
                "prof1",
                inicio,
                inicio.replace(hour=10),
                Suspeita.AUTISMO,
                "Concluída",
            ),
            RegistroAgenda(
                "p2",
                "prof2",
                inicio,
                inicio.replace(hour=10),
                Suspeita.AUTISMO,
                "Concluída",
            ),
        ]
    )
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=2)
    simulador = Simulador(equipe, parametros=parametros, tempo_avaliacao=(10, 10))
    pacientes = [Paciente(Suspeita.AUTISMO) for _ in range(3)]
    monkeypatch.setattr(
        parametros,
        "amostrar_profissional",
        lambda: (_ for _ in ()).throw(
            AssertionError("profissional não deve ser sorteado")
        ),
    )
    monkeypatch.setattr("classes.simulador.random.uniform", lambda *_: 10)

    for paciente in pacientes:
        env.process(simulador._paciente(paciente))
    env.run(until=21)

    assert all(paciente.diagnostico_concluido for paciente in pacientes)
    assert sorted(
        profissional.num_pacientes_atendidos for profissional in equipe.profissionais
    ) == [1, 2]
    assert (
        sum(
            profissional.tempo_total_atendimento
            for profissional in equipe.profissionais
        )
        == 30
    )
