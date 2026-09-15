import random

import simpy

from classes import Equipe, Paciente
from enums import Suspeita

pacientes: list[Paciente] = []


def paciente(env, paciente: Paciente, equipe: Equipe):
    chegada = env.now
    # print(f"{paciente.id} chegou em {chegada:.2f}")

    profissional = yield equipe.request()
    try:
        espera = env.now - chegada
        # print(
        #     f"Paciente {paciente.id} com suspeita de {paciente.suspeita} "
        #     f"começou atendimento com {profissional} após esperar {espera:.2f}"
        # )

        # TODO: Alterar para 60 minutos fixo
        tempo_avaliacao = random.uniform(30, 60)
        inicio_atendimento = env.now

        yield env.timeout(tempo_avaliacao)

        profissional.registrar_atendimento(inicio_atendimento, env.now)
    finally:
        equipe.release(profissional)

    # print(f"Paciente {paciente.id} terminou em {env.now:.2f}")


def chegada_pacientes(env, equipe: Equipe):
    while True:
        suspeita = random.choice(list(Suspeita))
        p = Paciente(suspeita)
        pacientes.append(p)
        env.process(paciente(env, p, equipe))

        intervalo = random.expovariate(1 / 20)
        yield env.timeout(intervalo)


if __name__ == "__main__":
    env = simpy.Environment()
    equipe = Equipe(
        env,
        nomes=["Fulano", "Beltrano", "Ciclano"],
    )
    equipe.monitorar(intervalo=1)
    env.process(chegada_pacientes(env, equipe))
    env.run(until=480)  # 480 minutos = 8 horas

    resumos = equipe.resumos()
    total_atendidos = sum(resumo["pacientes_atendidos"] for resumo in resumos)
    print(f"\n=== Resumo da simulação ===")
    print(f"Pacientes que chegaram: {len(pacientes)}")
    print(f"Pacientes atendidos: {total_atendidos}")
    print(f"Pacientes ainda não atendidos: {len(pacientes) - total_atendidos}")

    for resumo in resumos:
        print(f"\n=== Métricas de {resumo['nome']} ===")
        print(f"Pacientes atendidos: {resumo['pacientes_atendidos']}")
        print(
            f"Tempo médio de atendimento: {resumo['tempo_medio_atendimento']:.2f} min"
        )
        print(f"Tempo ocioso: {resumo['tempo_ocioso']:.2f} min")
        print(f"Taxa de ocupação: {resumo['taxa_ocupacao']:.2%}")
        print(f"Amostras da série temporal: {len(resumo['serie_temporal'])}")
