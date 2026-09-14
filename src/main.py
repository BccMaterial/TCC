import random

import simpy

from classes import Paciente, Profissional
from enums import Suspeita


def paciente(env, paciente: Paciente, profissional: Profissional):
    chegada = env.now
    print(f"{paciente.id} chegou em {chegada:.2f}")

    with profissional.request() as request:
        yield request

        espera = env.now - chegada
        print(
            f"Paciente {paciente.id} com suspeita de {paciente.suspeita} começou atendimento após esperar {espera:.2f}"
        )
        tempo_avaliacao = random.uniform(30, 60)
        inicio_atendimento = env.now

        yield env.timeout(tempo_avaliacao)

        fim_atendimento = env.now
        profissional.registrar_atendimento(inicio_atendimento, fim_atendimento)

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
    profissional = Profissional(env, nome="Fulano de tal")
    env.process(profissional.monitorar(intervalo=1))
    env.process(chegada_pacientes(env, profissional))
    env.run(until=480)  # 480 minutos = 8 horas

    resumo = profissional.resumo()
    print("\n=== Métricas do profissional ===")
    print(f"Nome: {resumo['nome']}")
    print(f"Pacientes atendidos: {resumo['pacientes_atendidos']}")
    print(f"Tempo médio de atendimento: {resumo['tempo_medio_atendimento']:.2f} min")
    print(f"Tempo ocioso: {resumo['tempo_ocioso']:.2f} min")
    print(f"Taxa de ocupação: {resumo['taxa_ocupacao']:.2%}")
    print(f"Amostras da série temporal: {len(resumo['serie_temporal'])}")
