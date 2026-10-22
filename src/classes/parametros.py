import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from enums import Suspeita

FaixaHorario = tuple[int, int]

_OBRIGATORIAS = {
    "ID do Paciente",
    "ID do Profissional",
    "Início da agenda",
    "Fim da agenda",
    "Suspeita do paciente",
    "Status da agenda",
}
_OPCIONAIS = {"ID de Agendamento", "Nome do Paciente", "Nome do Profissional"}
_STATUS = {"pendente": "Pendente", "falta": "Falta", "concluida": "Concluída"}
_ACENTOS = str.maketrans("áàãâéêíóôõúç", "aaaaeeiooouc")


def _normalizar(valor: str) -> str:
    return valor.strip().casefold().translate(_ACENTOS)


@dataclass(frozen=True)
class RegistroAgenda:
    id_paciente: str
    id_profissional: str
    inicio: datetime
    fim: datetime
    suspeita: Suspeita
    status: str
    id_agendamento: str | None = None
    nome_paciente: str | None = None
    nome_profissional: str | None = None


class Parametros:
    """Importa agenda CSV/XLSX e estima distribuições para a simulação."""

    def __init__(self, registros: list[RegistroAgenda]) -> None:
        if not registros:
            raise ValueError("O arquivo não contém registros de agenda.")
        self.registros = tuple(registros)

        dados = pd.DataFrame(
            {
                "data": [registro.inicio.date() for registro in registros],
                "dia_semana": [registro.inicio.weekday() for registro in registros],
                "hora": [registro.inicio.hour for registro in registros],
                "profissional": [registro.id_profissional for registro in registros],
                "suspeita": [registro.suspeita for registro in registros],
                "paciente": [registro.id_paciente for registro in registros],
                "status": [registro.status for registro in registros],
            }
        )
        total = len(dados)
        por_faixa = dados.groupby(["dia_semana", "hora"]).size()
        self.distribuicao_horarios: dict[FaixaHorario, float] = {
            (int(dia), int(hora)): float(quantidade / total)
            for (dia, hora), quantidade in por_faixa.items()
        }

        datas = pd.date_range(
            start=dados["data"].min(), end=dados["data"].max(), freq="D"
        )
        por_hora = dados.groupby("hora").size()
        self.taxa_agendamentos_por_hora: dict[int, float] = {
            int(hora): float(quantidade / len(datas))
            for hora, quantidade in por_hora.items()
        }
        self.probabilidades_profissionais: dict[str, float] = {
            profissional: float(probabilidade)
            for profissional, probabilidade in dados["profissional"]
            .value_counts(normalize=True)
            .items()
        }
        self.probabilidades_suspeitas: dict[Suspeita, float] = {
            suspeita: float(probabilidade)
            for suspeita, probabilidade in dados["suspeita"]
            .value_counts(normalize=True)
            .items()
        }
        nomes = pd.Series(
            [
                registro.nome_profissional
                for registro in registros
                if registro.nome_profissional
            ],
            index=[
                registro.id_profissional
                for registro in registros
                if registro.nome_profissional
            ],
        )
        self.nomes_profissionais: dict[str, str] = nomes.to_dict()
        desfechos = dados.loc[dados["status"] != "Pendente", "status"].value_counts()
        total_desfechos = int(desfechos.sum())
        self.probabilidade_no_show = (
            float(desfechos.get("Falta", 0) / total_desfechos)
            if total_desfechos
            else None
        )
        self.pacientes_com_multiplos_agendamentos = int(
            (dados["paciente"].value_counts() > 1).sum()
        )
        primeiro_dia = dados["data"].min()
        self.dia_semana_inicial = primeiro_dia.weekday()
        self.minuto_inicio_simulacao = min(
            registro.inicio.hour * 60 + registro.inicio.minute for registro in registros
        )

    @classmethod
    def carregar(cls, arquivo: str | Path) -> "Parametros":
        """Lê e valida arquivo CSV/XLSX com o esquema da agenda."""
        caminho = Path(arquivo)
        if caminho.suffix.casefold() == ".csv":
            tabela = pd.read_csv(
                caminho,
                sep=None,
                engine="python",
                header=None,
                encoding="utf-8-sig",
                dtype=object,
                keep_default_na=False,
            )
        elif caminho.suffix.casefold() == ".xlsx":
            tabela = pd.read_excel(
                caminho, header=None, dtype=object, engine="calamine"
            )
        else:
            raise ValueError("Formato não suportado. Use um arquivo .csv ou .xlsx.")

        if tabela.empty:
            raise ValueError(
                "A planilha não contém cabeçalho."
                if caminho.suffix.casefold() == ".xlsx"
                else "O arquivo CSV não contém cabeçalho."
            )
        nomes = [
            str(valor).strip() if pd.notna(valor) and str(valor).strip() else ""
            for valor in tabela.iloc[0].tolist()
        ]
        if tabela.shape[1] > len(nomes):
            nomes.extend([""] * (tabela.shape[1] - len(nomes)))
        if len(nomes) != len(set(nomes)):
            raise ValueError("O arquivo contém nomes de coluna duplicados.")
        if "" in nomes:
            raise ValueError("O arquivo contém coluna sem nome ou dados extras.")
        dados = tabela.iloc[1:].copy()
        dados.columns = nomes
        dados = dados.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
        linhas = (
            dados.astype(object).where(pd.notna(dados), None).to_dict(orient="records")
        )
        if not linhas:
            raise ValueError("O arquivo não contém registros de agenda.")
        colunas = set(nomes)
        faltantes = _OBRIGATORIAS - colunas
        if faltantes:
            raise ValueError(
                "Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes))
            )
        desconhecidas = colunas - _OBRIGATORIAS - _OPCIONAIS
        if desconhecidas:
            raise ValueError(
                "Colunas não reconhecidas: " + ", ".join(sorted(desconhecidas))
            )

        registros = []
        for numero, linha in enumerate(linhas, start=2):
            try:
                registros.append(cls._interpretar_linha(linha))
            except (TypeError, ValueError) as erro:
                raise ValueError(f"Linha {numero}: {erro}") from erro
        return cls(registros)

    def imprimir_parametros(self) -> None:
        """Imprime os resultados estimados para a parametrização."""
        dias = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")
        print("=== Resultados da parametrização ===")
        print(f"Registros de agenda: {len(self.registros)}")
        print("Distribuição de horários:")
        for (dia, hora), probabilidade in sorted(self.distribuicao_horarios.items()):
            print(f"  {dias[dia]} às {hora:02d}h: {probabilidade:.2%}")
        print("Taxa média de agendamentos por hora:")
        for hora, taxa in sorted(self.taxa_agendamentos_por_hora.items()):
            print(f"  às {hora:02d}h: {taxa:.2f}")
        print(f"Probabilidades por profissional: {self.probabilidades_profissionais}")
        print(f"Probabilidades por suspeita: {self.probabilidades_suspeitas}")
        print(f"Probabilidade de no-show: {self.probabilidade_no_show}")
        print(
            "Pacientes com múltiplos agendamentos: "
            f"{self.pacientes_com_multiplos_agendamentos}"
        )

    @staticmethod
    def _interpretar_linha(linha: dict[str, object]) -> RegistroAgenda:
        def campo(nome: str, obrigatorio: bool = True) -> str | None:
            valor = linha.get(nome)
            if valor is None or not str(valor).strip():
                if obrigatorio:
                    raise ValueError(f"o campo '{nome}' é obrigatório.")
                return None
            if isinstance(valor, float) and valor.is_integer():
                return str(int(valor))
            return str(valor).strip()

        inicio = Parametros._interpretar_data(campo("Início da agenda"))
        fim = Parametros._interpretar_data(campo("Fim da agenda"))
        if fim <= inicio:
            raise ValueError("o fim da agenda deve ser posterior ao início.")

        suspeita_texto = campo("Suspeita do paciente")
        suspeita = next(
            (
                item
                for item in Suspeita
                if _normalizar(item.value) == _normalizar(suspeita_texto)
                or _normalizar(item.name) == _normalizar(suspeita_texto)
            ),
            None,
        )
        if suspeita is None:
            raise ValueError(f"suspeita desconhecida: '{suspeita_texto}'.")
        status_texto = _normalizar(campo("Status da agenda"))
        status = _STATUS.get(status_texto)
        if status is None:
            raise ValueError(f"status desconhecido: '{status_texto}'.")

        return RegistroAgenda(
            id_paciente=campo("ID do Paciente"),
            id_profissional=campo("ID do Profissional"),
            inicio=inicio,
            fim=fim,
            suspeita=suspeita,
            status=status,
            id_agendamento=campo("ID de Agendamento", obrigatorio=False),
            nome_paciente=campo("Nome do Paciente", obrigatorio=False),
            nome_profissional=campo("Nome do Profissional", obrigatorio=False),
        )

    @staticmethod
    def _interpretar_data(valor: str | None) -> datetime:
        try:
            data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as erro:
            raise ValueError("timestamp deve estar no formato ISO 8601.") from erro
        if data.tzinfo is None or data.utcoffset() is None:
            raise ValueError("timestamp ISO 8601 deve conter fuso horário.")
        return data

    def amostrar_suspeita(self) -> Suspeita:
        itens = list(self.probabilidades_suspeitas)
        pesos = [self.probabilidades_suspeitas[item] for item in itens]
        return random.choices(itens, weights=pesos, k=1)[0]

    def amostrar_profissional(self) -> str:
        itens = list(self.probabilidades_profissionais)
        pesos = [self.probabilidades_profissionais[item] for item in itens]
        return random.choices(itens, weights=pesos, k=1)[0]
