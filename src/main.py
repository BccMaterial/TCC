import random

import simpy

from classes import Paciente
from enums.suspeitas import Suspeita


def paciente(env, paciente: Paciente, profissional):
    chegada = env.now
    print(f"{paciente.id} chegou em {chegada:.2f}")

    with profissional.request() as request:
        yield request

        espera = env.now - chegada
        print(
            f"Paciente {paciente.id} com suspeita de {paciente.suspeita} começou atendimento após esperar {espera:.2f}"
        )
        tempo_avaliacao = random.uniform(30, 60)

        yield env.timeout(tempo_avaliacao)

    print(f"Paciente {paciente.id} terminou em {env.now:.2f}")


def chegada_pacientes(env, profissional):
    while True:
        suspeita = random.choice(list(Suspeita))
        p = Paciente(suspeita)
        env.process(paciente(env, p, profissional))

        intervalo = random.expovariate(1 / 20)
        yield env.timeout(intervalo)


if __name__ == "__main__":
    env = simpy.Environment()
    profissional = simpy.Resource(env, capacity=1)
    env.process(chegada_pacientes(env, profissional))
    env.run(until=480)  # 480 minutos = 8 horas
