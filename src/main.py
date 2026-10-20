import simpy

from classes import Equipe, Simulador

if __name__ == "__main__":
    env = simpy.Environment()
    equipe = Equipe(
        env,
        nomes=["Fulano", "Beltrano", "Ciclano"],
    )
    simulador = Simulador(equipe)
    simulador.iniciar()
    simulador.resumo()
