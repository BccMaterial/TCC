import csv
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

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

        por_faixa: Counter[FaixaHorario] = Counter()
        por_profissional: Counter[str] = Counter()
        por_suspeita: Counter[Suspeita] = Counter()
        por_data_faixa: Counter[tuple[date, FaixaHorario]] = Counter()
        datas_observadas_por_dia: dict[int, set[date]] = defaultdict(set)
        desfechos = Counter()
        pacientes = Counter()
        self.nomes_profissionais: dict[str, str] = {}

        for registro in registros:
            faixa = (registro.inicio.weekday(), registro.inicio.hour)
            data = registro.inicio.date()
            por_faixa[faixa] += 1
            por_profissional[registro.id_profissional] += 1
            por_suspeita[registro.suspeita] += 1
            por_data_faixa[(data, faixa)] += 1
            datas_observadas_por_dia[faixa[0]].add(data)
            pacientes[registro.id_paciente] += 1
            if registro.nome_profissional:
                self.nomes_profissionais[registro.id_profissional] = (
                    registro.nome_profissional
                )
            if registro.status != "Pendente":
                desfechos[registro.status] += 1

        total = len(registros)
        self.distribuicao_horarios: dict[FaixaHorario, float] = {
            faixa: quantidade / total for faixa, quantidade in por_faixa.items()
        }
        # Condicional às datas com pelo menos um registro daquele dia da semana.
        self.taxa_agendamentos_por_hora: dict[FaixaHorario, float] = {
            faixa: sum(
                por_data_faixa[(data, faixa)]
                for data in datas_observadas_por_dia[faixa[0]]
            )
            / len(datas_observadas_por_dia[faixa[0]])
            for faixa in por_faixa
        }
        self.probabilidades_profissionais = {
            profissional: quantidade / total
            for profissional, quantidade in por_profissional.items()
        }
        self.probabilidades_suspeitas = {
            suspeita: quantidade / total
            for suspeita, quantidade in por_suspeita.items()
        }
        total_desfechos = sum(desfechos.values())
        self.probabilidade_no_show = (
            desfechos["Falta"] / total_desfechos if total_desfechos else None
        )
        self.pacientes_com_multiplos_agendamentos = sum(
            quantidade > 1 for quantidade in pacientes.values()
        )
        primeiro_dia = min(registro.inicio.date() for registro in registros)
        self.dia_semana_inicial = primeiro_dia.weekday()
        self.minuto_inicio_simulacao = min(
            registro.inicio.hour * 60 + registro.inicio.minute for registro in registros
        )

    @classmethod
    def carregar(cls, arquivo: str | Path) -> "Parametros":
        """Lê e valida arquivo CSV/XLSX com o esquema da agenda."""
        caminho = Path(arquivo)
        if caminho.suffix.casefold() == ".csv":
            with caminho.open(encoding="utf-8-sig", newline="") as fonte:
                amostra = fonte.read(4096)
                fonte.seek(0)
                try:
                    dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
                except csv.Error:
                    dialeto = csv.excel
                leitor = csv.DictReader(fonte, dialect=dialeto)
                cabecalhos = leitor.fieldnames
                if not cabecalhos:
                    raise ValueError("O arquivo CSV não contém cabeçalho.")
                nomes = [nome.strip() if nome else "" for nome in cabecalhos]
                if len(nomes) != len(set(nomes)):
                    raise ValueError("O arquivo contém nomes de coluna duplicados.")
                linhas = [
                    {
                        (chave.strip() if chave else ""): valor
                        for chave, valor in linha.items()
                    }
                    for linha in leitor
                ]
        elif caminho.suffix.casefold() == ".xlsx":
            workbook = load_workbook(caminho, read_only=True, data_only=True)
            try:
                valores = workbook.active.iter_rows(values_only=True)
                cabecalhos = next(valores, None)
                if cabecalhos is None:
                    raise ValueError("A planilha não contém cabeçalho.")
                nomes = [
                    str(valor).strip() if valor is not None else ""
                    for valor in cabecalhos
                ]
                if len(nomes) != len(set(nomes)):
                    raise ValueError("O arquivo contém nomes de coluna duplicados.")
                linhas = [
                    dict(zip(nomes, linha))
                    for linha in valores
                    if any(valor is not None for valor in linha)
                ]
            finally:
                workbook.close()
        else:
            raise ValueError("Formato não suportado. Use um arquivo .csv ou .xlsx.")

        if not linhas:
            raise ValueError("O arquivo não contém registros de agenda.")
        colunas = set(linhas[0])
        if "" in colunas or None in colunas:
            raise ValueError("O arquivo contém coluna sem nome ou dados extras.")
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
