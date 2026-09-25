import pytest

from pdv.caixa import abrir_caixa, caixa_aberto, fechar_caixa, resumo_caixa_aberto
from pdv.erros import ErroPDV
from pdv.vendas import finalizar_venda


def test_abrir_caixa():
    assert caixa_aberto() is None
    id_caixa = abrir_caixa(100)
    assert caixa_aberto()["id"] == id_caixa


def test_nao_abre_dois_caixas(caixa):
    with pytest.raises(ErroPDV, match="Já existe"):
        abrir_caixa(50)


def test_valor_inicial_negativo():
    with pytest.raises(ErroPDV):
        abrir_caixa(-1)


def test_fechar_sem_caixa_aberto():
    with pytest.raises(ErroPDV, match="Nenhum caixa"):
        fechar_caixa()


def test_status_sem_caixa_aberto():
    with pytest.raises(ErroPDV, match="Nenhum caixa"):
        resumo_caixa_aberto()


def test_fechar_caixa_sem_vendas(caixa):
    """Antes: OperationalError no such column: caixa_id."""
    resumo = fechar_caixa()

    assert resumo.total_vendas == 0
    assert resumo.saldo == 100
    assert caixa_aberto() is None


def test_fechamento_conta_so_as_vendas_do_proprio_caixa(carrinho, coca):
    abrir_caixa(100)
    carrinho.adicionar(coca, 1)
    finalizar_venda(carrinho, "Dinheiro")
    fechar_caixa()

    abrir_caixa(50)
    carrinho.adicionar(coca, 2)
    finalizar_venda(carrinho, "PIX")

    resumo = resumo_caixa_aberto()
    assert resumo.quantidade_vendas == 1
    assert resumo.total_vendas == 25.0

    resumo = fechar_caixa()
    assert resumo.saldo == 75.0
