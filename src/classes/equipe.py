import simpy

from .profissional import Profissional


class Equipe:
    """
    Gerencia uma equipe de profissionais que compartilha uma fila de pacientes.

    Cada profissional continua tendo seu próprio recurso e suas próprias
    métricas. O simpy.Store mantém os profissionais disponíveis para que cada
    paciente use o primeiro profissional livre.
    """

    def __init__(
        self,
        env: simpy.Environment,
        quantidade: int | None = None,
        nomes: list[str] | None = None,
    ) -> None:
        if quantidade is None:
            quantidade = len(nomes) if nomes else 0

        if quantidade < 1:
            raise ValueError(
                "Informe uma quantidade maior que zero ou uma lista de nomes."
            )
        if nomes and len(nomes) != quantidade:
            raise ValueError(
                "A quantidade de nomes deve ser igual à quantidade de profissionais."
            )

        self.env = env
        self.profissionais = [
            Profissional(
                env,
                nome=nomes[indice] if nomes else None,
            )
            for indice in range(quantidade)
        ]
        self._disponiveis = simpy.Store(env, capacity=quantidade)
        for profissional in self.profissionais:
            self._disponiveis.put(profissional)

    def request(self) -> simpy.Event:
        """Aguarda e retorna um profissional livre."""
        return self._disponiveis.get()

    def release(self, profissional: Profissional) -> simpy.Event:
        """Devolve um profissional à equipe após o atendimento."""
        if profissional not in self.profissionais:
            raise ValueError("O profissional não pertence a esta equipe.")
        return self._disponiveis.put(profissional)

    def monitorar(self, intervalo: float = 1.0) -> None:
        """Inicia o monitoramento de todos os profissionais da equipe."""
        for profissional in self.profissionais:
            self.env.process(profissional.monitorar(intervalo))

    def resumos(self) -> list[dict[str, float | int | str]]:
        """Retorna as métricas individuais de todos os profissionais."""
        return [profissional.resumo() for profissional in self.profissionais]
