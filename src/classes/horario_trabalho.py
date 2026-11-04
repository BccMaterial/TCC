import math


class HorarioTrabalho:
    """Calcula os períodos úteis a partir do calendário da simulação."""

    INICIO_EXPEDIENTE = 9 * 60
    INICIO_ALMOCO = 12 * 60
    FIM_ALMOCO = 13 * 60
    FIM_EXPEDIENTE = 18 * 60
    MINUTOS_DIA = 24 * 60

    def __init__(
        self, dia_semana_inicial: int = 0, minuto_inicio: int = 9 * 60
    ) -> None:
        self.dia_semana_inicial = dia_semana_inicial
        self.minuto_inicio = minuto_inicio

    def _dia_e_minuto(self, tempo: float) -> tuple[int, float, int]:
        minutos = self.minuto_inicio + tempo
        deslocamento_dias = math.floor(minutos / self.MINUTOS_DIA)
        minuto_do_dia = minutos % self.MINUTOS_DIA
        dia_semana = (self.dia_semana_inicial + deslocamento_dias) % 7
        return dia_semana, minuto_do_dia, deslocamento_dias

    def em_expediente(self, tempo: float) -> bool:
        dia_semana, minuto, _ = self._dia_e_minuto(tempo)
        return (
            dia_semana < 5
            and self.INICIO_EXPEDIENTE <= minuto < self.FIM_EXPEDIENTE
            and not self.INICIO_ALMOCO <= minuto < self.FIM_ALMOCO
        )

    def minutos_ate_proximo_expediente(self, tempo: float) -> float:
        dia_semana, minuto, deslocamento_dias = self._dia_e_minuto(tempo)
        if dia_semana < 5 and self.INICIO_ALMOCO <= minuto < self.FIM_ALMOCO:
            return self.FIM_ALMOCO - minuto
        if self.em_expediente(tempo):
            return 0

        for deslocamento in range(8):
            dia = (self.dia_semana_inicial + deslocamento_dias + deslocamento) % 7
            if dia >= 5:
                continue
            inicio = (
                (deslocamento_dias + deslocamento) * self.MINUTOS_DIA
                + self.INICIO_EXPEDIENTE
                - self.minuto_inicio
            )
            if inicio >= tempo:
                return inicio - tempo
        raise RuntimeError("Não foi possível encontrar o próximo dia útil.")

    def minutos_ate_fechamento(self, tempo: float) -> float:
        if not self.em_expediente(tempo):
            return 0
        _, minuto, _ = self._dia_e_minuto(tempo)
        limite = (
            self.INICIO_ALMOCO if minuto < self.INICIO_ALMOCO else self.FIM_EXPEDIENTE
        )
        return limite - minuto

    def minutos_uteis(self, inicio: float, fim: float) -> float:
        if fim <= inicio:
            return 0

        primeiro_dia = math.floor((self.minuto_inicio + inicio) / self.MINUTOS_DIA)
        ultimo_dia = math.floor((self.minuto_inicio + fim) / self.MINUTOS_DIA)
        total = 0.0
        for deslocamento in range(primeiro_dia, ultimo_dia + 1):
            dia_semana = (self.dia_semana_inicial + deslocamento) % 7
            if dia_semana >= 5:
                continue
            inicio_expediente = (
                deslocamento * self.MINUTOS_DIA
                + self.INICIO_EXPEDIENTE
                - self.minuto_inicio
            )
            fim_expediente = (
                deslocamento * self.MINUTOS_DIA
                + self.FIM_EXPEDIENTE
                - self.minuto_inicio
            )
            total += max(
                0,
                min(fim, fim_expediente) - max(inicio, inicio_expediente),
            )
            inicio_almoco = (
                deslocamento * self.MINUTOS_DIA
                + self.INICIO_ALMOCO
                - self.minuto_inicio
            )
            fim_almoco = (
                deslocamento * self.MINUTOS_DIA + self.FIM_ALMOCO - self.minuto_inicio
            )
            total -= max(0, min(fim, fim_almoco) - max(inicio, inicio_almoco))
        return total
