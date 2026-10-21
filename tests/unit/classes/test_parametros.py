from datetime import datetime

import pytest
import simpy
from openpyxl import Workbook

from classes import Equipe, Parametros, RegistroAgenda, Simulador
from enums import Suspeita

CABECALHO = [
    "ID do Paciente",
    "ID do Profissional",
    "ID de Agendamento",
    "Nome do Paciente",
    "Nome do Profissional",
    "Início da agenda",
    "Fim da agenda",
    "Suspeita do paciente",
    "Status da agenda",
]


def _linha(
    paciente: str = "p1",
    profissional: str = "prof1",
    inicio: str = "2026-10-19T09:00:00-03:00",
    fim: str = "2026-10-19T10:00:00-03:00",
    status: str = "Concluída",
) -> list[str]:
    return [
        paciente,
        profissional,
        "",
        "",
        "",
        inicio,
        fim,
        "Autismo",
        status,
    ]


def test_carregar_csv_estima_distribuicoes_e_exclui_pendentes_no_no_show(tmp_path):
    arquivo = tmp_path / "agenda.csv"
    arquivo.write_text(
        ",".join(CABECALHO)
        + "\n"
        + ",".join(_linha(status="Falta"))
        + "\n"
        + ",".join(_linha(paciente="p2", status="Pendente"))
        + "\n",
        encoding="utf-8",
    )

    parametros = Parametros.carregar(arquivo)

    assert len(parametros.registros) == 2
    assert parametros.probabilidade_no_show == 1
    assert parametros.probabilidades_profissionais == {"prof1": 1}
    assert parametros.probabilidades_suspeitas == {Suspeita.AUTISMO: 1}
    assert parametros.taxa_agendamentos_por_hora == {(0, 9): 2}
    assert parametros.registros[0].inicio.utcoffset().total_seconds() == -10800


def test_taxa_horaria_considera_outras_datas_observadas_do_mesmo_dia():
    primeira = datetime.fromisoformat("2026-10-19T09:00:00-03:00")
    segunda = datetime.fromisoformat("2026-10-26T10:00:00-03:00")
    parametros = Parametros(
        [
            RegistroAgenda(
                "p1",
                "prof1",
                primeira,
                primeira.replace(hour=10),
                Suspeita.AUTISMO,
                "Concluída",
            ),
            RegistroAgenda(
                "p2",
                "prof1",
                segunda,
                segunda.replace(hour=11),
                Suspeita.AUTISMO,
                "Concluída",
            ),
        ]
    )

    assert parametros.taxa_agendamentos_por_hora[(0, 9)] == 0.5
    assert parametros.taxa_agendamentos_por_hora[(0, 10)] == 0.5


def test_carregar_xlsx_sem_colunas_opcionais(tmp_path):
    arquivo = tmp_path / "agenda.xlsx"
    workbook = Workbook()
    planilha = workbook.active
    colunas = [
        nome
        for nome in CABECALHO
        if nome not in {"ID de Agendamento", "Nome do Paciente", "Nome do Profissional"}
    ]
    planilha.append(colunas)
    planilha.append(
        [
            "p1",
            "prof1",
            "2026-10-19T09:00:00Z",
            "2026-10-19T10:00:00Z",
            "TDAH",
            "Falta",
        ]
    )
    workbook.save(arquivo)

    parametros = Parametros.carregar(arquivo)

    assert parametros.registros[0].id_agendamento is None
    assert parametros.registros[0].suspeita is Suspeita.TDAH
    assert parametros.probabilidade_no_show == 1


@pytest.mark.parametrize(
    ("inicio", "fim", "mensagem"),
    [
        ("2026-10-19T09:00:00", "2026-10-19T10:00:00-03:00", "fuso"),
        ("2026-10-19T10:00:00-03:00", "2026-10-19T09:00:00-03:00", "posterior"),
    ],
)
def test_carregar_rejeita_intervalos_invalidos(tmp_path, inicio, fim, mensagem):
    arquivo = tmp_path / "agenda.csv"
    arquivo.write_text(
        ",".join(CABECALHO) + "\n" + ",".join(_linha(inicio=inicio, fim=fim)) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=mensagem):
        Parametros.carregar(arquivo)


def test_no_show_sem_resultados_observados_nao_e_inventado():
    data = datetime.fromisoformat("2026-10-19T09:00:00-03:00")
    parametros = Parametros(
        [
            RegistroAgenda(
                "p1", "prof1", data, data.replace(hour=10), Suspeita.AUTISMO, "Pendente"
            )
        ]
    )

    assert parametros.probabilidade_no_show is None
    with pytest.raises(ValueError, match="ao menos um status"):
        Simulador(Equipe(simpy.Environment(), ids=["prof1"]), parametros=parametros)


def test_simulador_parametrizado_gera_agendamentos(monkeypatch):
    data = datetime.fromisoformat("2026-10-19T09:00:00-03:00")
    parametros = Parametros(
        [
            RegistroAgenda(
                "p1",
                "prof1",
                data,
                data.replace(hour=10),
                Suspeita.AUTISMO,
                "Concluída",
            )
        ]
    )
    env = simpy.Environment()
    equipe = Equipe(env, ids=["prof1"])
    simulador = Simulador(equipe, parametros=parametros, tempo_avaliacao=(30, 30))
    monkeypatch.setattr("classes.simulador.random.expovariate", lambda _: 30)
    monkeypatch.setattr("classes.simulador.random.random", lambda: 0)

    simulador.iniciar(duracao=61)

    assert simulador.agendamentos_simulados == 1
    assert simulador.nao_compareceram == 0
    assert len(simulador.pacientes) == 1
    assert equipe.profissionais[0].num_pacientes_atendidos == 1


def test_simulador_parametrizado_aplica_no_show(monkeypatch):
    data = datetime.fromisoformat("2026-10-19T09:00:00-03:00")
    parametros = Parametros(
        [
            RegistroAgenda(
                "p1",
                "prof1",
                data,
                data.replace(hour=10),
                Suspeita.AUTISMO,
                "Falta",
            )
        ]
    )
    env = simpy.Environment()
    equipe = Equipe(env, ids=["prof1"])
    simulador = Simulador(equipe, parametros=parametros)
    monkeypatch.setattr("classes.simulador.random.expovariate", lambda _: 30)
    monkeypatch.setattr("classes.simulador.random.random", lambda: 0)

    simulador.iniciar(duracao=61)

    assert simulador.agendamentos_simulados == 1
    assert simulador.nao_compareceram == 1
    assert simulador.pacientes == []
