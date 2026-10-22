from pathlib import Path

import simpy

from classes import Equipe, Parametros, Simulador

if __name__ == "__main__":
    arquivo_agenda = Path(__file__).parent.parent / "data" / "teste.csv"
    parametros = Parametros.carregar(arquivo_agenda)
    parametros.imprimir_parametros()
    ids_profissionais = list(parametros.probabilidades_profissionais)
    nomes_profissionais = [
        parametros.nomes_profissionais.get(id_profissional, id_profissional)
        for id_profissional in ids_profissionais
    ]
    env = simpy.Environment()
    equipe = Equipe(
        env,
        nomes=nomes_profissionais,
        ids=ids_profissionais,
    )
    simulador = Simulador(equipe, parametros=parametros)
    simulador.iniciar(duracao=480)
    simulador.resumo()
