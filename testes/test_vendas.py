import pytest

from pdv.banco import conexao
from pdv.erros import ErroPDV, EstoqueInsuficiente
from pdv.estoque import definir_custo_inicial, registrar_compra
from pdv.movimentacoes import listar_movimentacoes
from pdv.produtos import buscar_produto, cadastrar_produto, desativar_produto
from pdv.vendas import finalizar_venda


def _contar(tabela):
    with conexao() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


# ---------------------------------------------------------------- carrinho

def test_adicionar_sem_caixa_aberto(carrinho, coca):
    with pytest.raises(ErroPDV, match="Abra o caixa"):
        carrinho.adicionar(coca, 1)


def test_mesmo_produto_soma_na_mesma_linha(caixa, carrinho, coca):
    carrinho.adicionar(coca, 3)
    item = carrinho.adicionar(coca, 2)

    assert item.quantidade == 5
    assert carrinho.itens == {coca: 5}


@pytest.mark.parametrize("quantidade", [0, -4])
def test_quantidade_zero_ou_negativa(caixa, carrinho, coca, quantidade):
    """Antes: vender -4 gerava venda de R$ -40,00 e aumentava o estoque."""
    with pytest.raises(ErroPDV, match="maior que zero"):
        carrinho.adicionar(coca, quantidade)


def test_produto_desativado_nao_entra_no_carrinho(caixa, carrinho, coca):
    desativar_produto(coca)
    with pytest.raises(ErroPDV, match="desativado"):
        carrinho.adicionar(coca, 1)


def test_produto_inexistente(caixa, carrinho):
    with pytest.raises(ErroPDV, match="não encontrado"):
        carrinho.adicionar(999, 1)


def test_total_e_remocao(caixa, carrinho, coca, bala):
    carrinho.adicionar(coca, 2)
    carrinho.adicionar(bala, 3)
    assert carrinho.total() == 25.30

    carrinho.remover(coca)
    assert carrinho.total() == 0.30

    with pytest.raises(ErroPDV):
        carrinho.remover(coca)


def test_desfazer_ultima_adicao_remove_uma_unidade(caixa, carrinho, coca, bala):
    carrinho.adicionar(coca, 2)
    carrinho.adicionar(bala, 1)

    assert carrinho.desfazer_ultima_adicao() == bala
    assert carrinho.itens == {coca: 2}
    assert carrinho.desfazer_ultima_adicao() == coca
    assert carrinho.itens == {coca: 1}


def test_desfazer_sem_adicoes_disponiveis(carrinho):
    with pytest.raises(ErroPDV, match="Não há uma adição recente"):
        carrinho.desfazer_ultima_adicao()


def test_remover_produto_remove_adicoes_correspondentes_do_historico(caixa, carrinho, coca, bala):
    carrinho.adicionar(coca, 1)
    carrinho.adicionar(bala, 1)
    carrinho.remover(coca)

    assert carrinho.desfazer_ultima_adicao() == bala
    assert carrinho.esta_vazio()


# ---------------------------------------------------------------- venda

def test_venda_completa(caixa, carrinho, coca, bala):
    """Antes: 'table vendas has no column named caixa_id' em toda venda."""
    carrinho.adicionar(coca, 2)
    carrinho.adicionar(bala, 3)

    resultado = finalizar_venda(carrinho, "PIX")

    assert resultado.total == 25.30
    assert resultado.estoques_negativos == []
    assert carrinho.esta_vazio()
    assert buscar_produto(coca)["estoque"] == 3
    assert buscar_produto(bala)["estoque"] == 97

    with conexao() as conn:
        venda = conn.execute("SELECT * FROM vendas").fetchone()
        itens = conn.execute("SELECT * FROM itens_vendas ORDER BY produto_id").fetchall()

    assert venda["caixa_id"] == caixa
    assert venda["forma_pagamento"] == "PIX"
    assert [(i["produto_id"], i["quantidade"], i["valor_unitario"]) for i in itens] == [
        (coca, 2, 12.50),
        (bala, 3, 0.10),
    ]

    vendas_no_historico = [m for m in listar_movimentacoes() if m["tipo"] == "VENDA"]
    assert {m["quantidade"] for m in vendas_no_historico} == {-2, -3}


def test_venda_guarda_o_custo_medio_vigente(caixa, carrinho, coca):
    definir_custo_inicial(coca, 8)
    carrinho.adicionar(coca, 2)
    finalizar_venda(carrinho, "PIX")

    registrar_compra([(coca, 2, 14)])

    with conexao() as conn:
        item_vendido = conn.execute(
            "SELECT valor_unitario, custo_unitario FROM itens_vendas"
        ).fetchone()

    assert tuple(item_vendido) == (12.5, 8)
    assert buscar_produto(coca)["custo_medio"] == 10.4


def test_venda_sem_custo_conhecido_nao_inventa_custo(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)
    finalizar_venda(carrinho, "PIX")

    with conexao() as conn:
        custo_venda = conn.execute(
            "SELECT custo_unitario FROM itens_vendas"
        ).fetchone()[0]

    assert custo_venda is None


def test_centavos_sao_gravados_arredondados(caixa, carrinho, bala):
    """Antes: 0.1 x 3 era gravado como 0.30000000000000004."""
    carrinho.adicionar(bala, 3)
    finalizar_venda(carrinho, "Dinheiro")

    with conexao() as conn:
        assert conn.execute("SELECT valor_total FROM vendas").fetchone()[0] == 0.3


def test_mesmo_produto_duas_vezes_nao_vende_alem_do_estoque(caixa, carrinho, coca):
    """Antes: estoque 5, carrinho 3 + 3 -> vendia 6 e o estoque ficava 2."""
    carrinho.adicionar(coca, 3)
    carrinho.adicionar(coca, 3)

    with pytest.raises(EstoqueInsuficiente) as erro:
        finalizar_venda(carrinho, "PIX")

    assert (erro.value.disponivel, erro.value.pedido) == (5, 6)
    # nada foi gravado e o carrinho continua lá para o operador decidir
    assert _contar("vendas") == 0
    assert buscar_produto(coca)["estoque"] == 5
    assert carrinho.itens == {coca: 6}


def test_venda_com_estoque_negativo_autorizada(caixa, carrinho, coca):
    carrinho.adicionar(coca, 6)

    resultado = finalizar_venda(carrinho, "PIX", permitir_estoque_negativo=True)

    assert resultado.estoques_negativos == [("Coca-Cola 2L", -1)]
    assert buscar_produto(coca)["estoque"] == -1


def test_produto_desativado_depois_de_ir_para_o_carrinho(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)
    desativar_produto(coca)

    with pytest.raises(ErroPDV, match="desativado"):
        finalizar_venda(carrinho, "PIX")
    assert _contar("vendas") == 0


def test_forma_de_pagamento_invalida(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)
    with pytest.raises(ErroPDV, match="Forma de pagamento"):
        finalizar_venda(carrinho, "pix")


def test_carrinho_vazio(caixa, carrinho):
    with pytest.raises(ErroPDV, match="vazio"):
        finalizar_venda(carrinho, "PIX")


def test_caixa_fechado_no_meio_da_venda(caixa, carrinho, coca):
    from pdv.caixa import fechar_caixa

    carrinho.adicionar(coca, 1)
    fechar_caixa(100)

    with pytest.raises(ErroPDV, match="Abra o caixa"):
        finalizar_venda(carrinho, "PIX")


# ---------------------------------------------------------------- troco

def _venda_gravada():
    with conexao() as conn:
        return conn.execute("SELECT * FROM vendas ORDER BY id DESC").fetchone()


def test_troco_no_pagamento_em_dinheiro(caixa, carrinho, coca):
    carrinho.adicionar(coca, 2)  # 25,00

    resultado = finalizar_venda(carrinho, "Dinheiro", valor_recebido=50)

    assert resultado.valor_recebido == 50
    assert resultado.troco == 25

    venda = _venda_gravada()
    assert (venda["valor_total"], venda["valor_recebido"], venda["troco"]) == (25, 50, 25)


def test_troco_com_centavos(caixa, carrinho):
    salgado = cadastrar_produto("Salgado", 12.70, 10)
    carrinho.adicionar(salgado, 1)

    resultado = finalizar_venda(carrinho, "Dinheiro", valor_recebido=20)

    # sem o round, 20 - 12.7 daria 7.300000000000001
    assert resultado.troco == 7.3


def test_dinheiro_sem_valor_recebido_considera_valor_exato(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)

    resultado = finalizar_venda(carrinho, "Dinheiro")

    assert resultado.valor_recebido == 12.5
    assert resultado.troco == 0


def test_valor_recebido_menor_que_o_total(caixa, carrinho, coca):
    carrinho.adicionar(coca, 2)  # 25,00

    with pytest.raises(ErroPDV, match="menor que o total"):
        finalizar_venda(carrinho, "Dinheiro", valor_recebido=20)

    # nada foi gravado e o carrinho continua lá
    assert _contar("vendas") == 0
    assert buscar_produto(coca)["estoque"] == 5
    assert carrinho.itens == {coca: 2}


def test_pix_nao_tem_troco(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)

    resultado = finalizar_venda(carrinho, "PIX")

    assert (resultado.valor_recebido, resultado.troco) == (None, None)
    venda = _venda_gravada()
    assert (venda["valor_recebido"], venda["troco"]) == (None, None)


def test_valor_recebido_so_vale_para_dinheiro(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)

    with pytest.raises(ErroPDV, match="só vale para pagamento em dinheiro"):
        finalizar_venda(carrinho, "Cartão de crédito", valor_recebido=50)
    assert _contar("vendas") == 0
