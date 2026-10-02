import pytest

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.estoque import (
    ajustar_estoque,
    ajustar_estoque_em_lote,
    definir_custo_inicial,
    entrada_estoque,
    registrar_compra,
)
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


def test_definir_custo_inicial_registra_historico(coca):
    assert definir_custo_inicial(coca, 8.50) == 8.5
    produto = buscar_produto(coca)

    assert produto["custo_medio"] == 8.5
    with conexao() as conn:
        movimentacao = conn.execute(
            "SELECT tipo, quantidade, custo_unitario FROM movimentacoes_estoque "
            "WHERE produto_id = ? ORDER BY id DESC LIMIT 1",
            (coca,),
        ).fetchone()

    assert tuple(movimentacao) == ("CUSTO_INICIAL", 0, 8.5)


def test_custo_inicial_nao_pode_ser_informado_duas_vezes(coca):
    definir_custo_inicial(coca, 8.5)

    with pytest.raises(ErroPDV, match="já possui custo médio"):
        definir_custo_inicial(coca, 9)


def test_custo_inicial_negativo_e_recusado(coca):
    with pytest.raises(ErroPDV, match="não pode ser negativo"):
        definir_custo_inicial(coca, -1)


def test_registrar_compra_atualiza_custo_medio_ponderado(coca):
    definir_custo_inicial(coca, 10)

    id_compra = registrar_compra(
        [(coca, 3, 14)],
        fornecedor="Distribuidora",
        referencia="REC-123",
        observacao="Compra semanal",
    )

    produto = buscar_produto(coca)
    assert (produto["estoque"], produto["custo_medio"]) == (8, 11.5)

    with conexao() as conn:
        compra = conn.execute("SELECT * FROM compras WHERE id = ?", (id_compra,)).fetchone()
        movimentacao = conn.execute(
            "SELECT compra_id, custo_unitario, data_movimentacao "
            "FROM movimentacoes_estoque WHERE compra_id = ?",
            (id_compra,),
        ).fetchone()

    assert (compra["fornecedor"], compra["referencia"], compra["observacao"]) == (
        "Distribuidora", "REC-123", "Compra semanal"
    )
    assert movimentacao["compra_id"] == id_compra
    assert movimentacao["custo_unitario"] == 14
    assert movimentacao["data_movimentacao"] == compra["data_compra"]


def test_primeira_compra_define_custo_para_produto_sem_estoque():
    from pdv.produtos import cadastrar_produto

    id_produto = cadastrar_produto("Produto novo", 20, 0)
    registrar_compra([(id_produto, 4, 8.25)])

    produto = buscar_produto(id_produto)
    assert (produto["estoque"], produto["custo_medio"]) == (4, 8.25)


def test_compra_exige_custo_inicial_quando_estoque_existente_e_desconhecido(coca):
    with pytest.raises(ErroPDV, match="Informe o custo inicial"):
        registrar_compra([(coca, 2, 9)])

    produto = buscar_produto(coca)
    assert (produto["estoque"], produto["custo_medio"]) == (5, None)
    with conexao() as conn:
        assert conn.execute("SELECT COUNT(*) FROM compras").fetchone()[0] == 0


def test_compra_pode_informar_custo_inicial_na_mesma_transacao(coca):
    id_compra = registrar_compra(
        [(coca, 3, 14)],
        custos_iniciais={coca: 10},
    )

    produto = buscar_produto(coca)
    assert (produto["estoque"], produto["custo_medio"]) == (8, 11.5)
    with conexao() as conn:
        movimentacoes = conn.execute(
            "SELECT tipo, quantidade, custo_unitario, compra_id "
            "FROM movimentacoes_estoque WHERE compra_id = ? ORDER BY id",
            (id_compra,),
        ).fetchall()

    assert [tuple(movimentacao) for movimentacao in movimentacoes] == [
        ("CUSTO_INICIAL", 0, 10, id_compra),
        ("ENTRADA", 3, 14, id_compra),
    ]


def test_compra_com_item_invalido_faz_rollback_completo(coca):
    definir_custo_inicial(coca, 10)

    with pytest.raises(ErroPDV, match="não encontrado"):
        registrar_compra([(coca, 2, 12), (999, 1, 5)])

    produto = buscar_produto(coca)
    assert (produto["estoque"], produto["custo_medio"]) == (5, 10)
    with conexao() as conn:
        assert conn.execute("SELECT COUNT(*) FROM compras").fetchone()[0] == 0


@pytest.mark.parametrize(
    "itens",
    [
        [],
        [(1, 0, 5)],
        [(1, 1, -1)],
        [(1, 1, 5), (1, 2, 6)],
    ],
)
def test_compra_recusa_dados_invalidos(itens):
    with pytest.raises(ErroPDV):
        registrar_compra(itens)


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


def test_ajuste_em_lote_registra_diferencas_e_ignora_estoque_inalterado(coca, bala):
    resultados = ajustar_estoque_em_lote({coca: 3, bala: 100})

    assert [(item.nome_produto, item.estoque_anterior, item.estoque_atual) for item in resultados] == [
        ("Coca-Cola 2L", 5, 3)
    ]
    assert buscar_produto(coca)["estoque"] == 3
    assert buscar_produto(bala)["estoque"] == 100


def test_ajuste_em_lote_faz_rollback_se_um_produto_nao_existir(coca, bala):
    with pytest.raises(ErroPDV, match="não encontrado"):
        ajustar_estoque_em_lote({coca: 3, 999: 4})

    assert buscar_produto(coca)["estoque"] == 5
    assert buscar_produto(bala)["estoque"] == 100


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
