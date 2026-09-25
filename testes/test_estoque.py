import pytest

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.estoque import ajustar_estoque, entrada_estoque
from pdv.movimentacoes import listar_movimentacoes
from pdv.produtos import buscar_produto
from pdv.vendas import finalizar_venda


def test_entrada_soma_ao_estoque_e_registra(coca):
    resultado = entrada_estoque(coca, 10, "Fornecedor")

    assert (resultado.estoque_anterior, resultado.estoque_atual) == (5, 15)
    assert buscar_produto(coca)["estoque"] == 15

    ultima = listar_movimentacoes()[0]
    assert (ultima["tipo"], ultima["quantidade"], ultima["observacao"]) == ("ENTRADA", 10, "Fornecedor")


@pytest.mark.parametrize("quantidade", [0, -3])
def test_entrada_recusa_quantidade_zero_ou_negativa(coca, quantidade):
    with pytest.raises(ErroPDV):
        entrada_estoque(coca, quantidade)
    assert buscar_produto(coca)["estoque"] == 5


def test_entrada_em_produto_inexistente():
    with pytest.raises(ErroPDV, match="não encontrado"):
        entrada_estoque(999, 1)


def test_ajuste_registra_a_diferenca(coca):
    resultado = ajustar_estoque(coca, 2, "Quebra")

    assert (resultado.estoque_anterior, resultado.estoque_atual) == (5, 2)
    assert listar_movimentacoes()[0]["quantidade"] == -3


def test_ajuste_sem_diferenca(coca):
    with pytest.raises(ErroPDV, match="nenhum ajuste"):
        ajustar_estoque(coca, 5)


def test_ajuste_negativo_recusado(coca):
    with pytest.raises(ErroPDV):
        ajustar_estoque(coca, -1)


def test_historico_sempre_bate_com_o_estoque(caixa, carrinho, coca, bala):
    """A soma das movimentações de cada produto deve ser igual ao estoque dele."""
    entrada_estoque(coca, 10)
    ajustar_estoque(bala, 90)
    carrinho.adicionar(coca, 4)
    carrinho.adicionar(bala, 7)
    finalizar_venda(carrinho, "PIX")

    with conexao() as conn:
        linhas = conn.execute("""
            SELECT p.estoque, SUM(m.quantidade) AS soma
            FROM produtos p JOIN movimentacoes_estoque m ON m.produto_id = p.id
            GROUP BY p.id
        """).fetchall()

    assert len(linhas) == 2
    for linha in linhas:
        assert linha["estoque"] == linha["soma"]
