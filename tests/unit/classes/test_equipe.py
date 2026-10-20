import pytest
import simpy

from classes import Equipe, Profissional


def test_when_creating_team_with_quantity_only():
    """
    It should create the object with the requested number of professionals.
    """
    equipe = Equipe(simpy.Environment(), quantidade=3)

    assert len(equipe.profissionais) == 3
    assert all(
        profissional.nome.startswith("Profissional ")
        for profissional in equipe.profissionais
    )


def test_when_creating_team_with_names_only():
    """
    It should create the object with one professional for each name.
    """
    nomes = ["Fulano", "Beltrano", "Ciclano"]

    equipe = Equipe(simpy.Environment(), nomes=nomes)

    assert len(equipe.profissionais) == len(nomes)
    assert [profissional.nome for profissional in equipe.profissionais] == nomes


def test_when_quantity_differs_from_names_length():
    """
    It should raise a ValueError when quantity differs from the number of names.
    """
    with pytest.raises(ValueError):
        Equipe(simpy.Environment(), quantidade=2, nomes=["Fulano"])


def test_when_quantity_is_same_as_names_length():
    """
    It should create the object when quantity equals the number of names.
    """
    nomes = ["Fulano", "Beltrano"]

    equipe = Equipe(simpy.Environment(), quantidade=2, nomes=nomes)

    assert len(equipe.profissionais) == 2
    assert [profissional.nome for profissional in equipe.profissionais] == nomes


@pytest.mark.parametrize(
    ("quantidade", "nomes"),
    [
        (None, None),
        (0, None),
    ],
)
def test_when_team_is_created_without_professionals(quantidade, nomes):
    with pytest.raises(ValueError):
        Equipe(simpy.Environment(), quantidade=quantidade, nomes=nomes)


def test_when_requesting_and_releasing_a_professional():
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)

    requisicao = equipe.request()
    env.run(until=requisicao)
    profissional = requisicao.value

    assert profissional is equipe.profissionais[0]

    liberacao = equipe.release(profissional)
    env.run(until=liberacao)
    nova_requisicao = equipe.request()
    env.run(until=nova_requisicao)

    assert nova_requisicao.value is profissional


def test_when_releasing_a_professional_not_in_the_team():
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)
    profissional = Profissional(env)

    with pytest.raises(ValueError, match="não pertence"):
        equipe.release(profissional)


def test_when_monitoring_team():
    env = simpy.Environment()
    equipe = Equipe(env, quantidade=1)

    equipe.monitorar(intervalo=1)
    env.run(until=3)

    assert equipe.profissionais[0]._amostras == [(0, 0), (1, 0), (2, 0)]


def test_when_getting_team_summaries():
    equipe = Equipe(simpy.Environment(), quantidade=2)

    resumos = equipe.resumos()

    assert resumos == [profissional.resumo() for profissional in equipe.profissionais]
