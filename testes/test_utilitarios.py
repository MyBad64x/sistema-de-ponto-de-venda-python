import pytest

from pdv.terminal import utilitarios
from pdv.terminal.utilitarios import cortar, dinheiro, ler_decimal, ler_inteiro


def _digitar(monkeypatch, *respostas):
    """Simula o usuário digitando cada resposta em sequência."""
    respostas = iter(respostas)
    monkeypatch.setattr("builtins.input", lambda _mensagem="": next(respostas))


def test_ler_decimal_aceita_virgula(monkeypatch):
    _digitar(monkeypatch, "12,50")
    assert ler_decimal("Preço: ") == 12.5


def test_ler_decimal_repete_ate_valor_valido(monkeypatch, capsys):
    _digitar(monkeypatch, "abc", "-1", "3.5")
    assert ler_decimal("Preço: ", minimo=0) == 3.5

    saida = capsys.readouterr().out
    assert "Digite um número válido" in saida
    assert "não pode ser negativo" in saida


def test_ler_inteiro_com_minimo_e_maximo(monkeypatch):
    _digitar(monkeypatch, "0", "9", "2")
    assert ler_inteiro("Opção: ", minimo=1, maximo=4) == 2


def test_enter_mantem_valor_padrao(monkeypatch):
    _digitar(monkeypatch, "")
    assert ler_decimal("Preço: ", padrao=7.0) == 7.0


def test_escolher_devolve_item_da_lista(monkeypatch):
    _digitar(monkeypatch, "2")
    assert utilitarios.escolher("Escolha: ", ("Dinheiro", "PIX")) == "PIX"


@pytest.mark.parametrize("valor, esperado", [
    (0, "R$ 0,00"),
    (12.5, "R$ 12,50"),
    (1234.5, "R$ 1.234,50"),
    (-40, "R$ -40,00"),
])
def test_dinheiro(valor, esperado):
    assert dinheiro(valor) == esperado


def test_cortar():
    assert cortar("curto", 10) == "curto"
    assert cortar("um nome de produto bem longo", 10) == "um nome d…"
