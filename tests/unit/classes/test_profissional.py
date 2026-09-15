import pytest
import simpy

from classes import Equipe


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
