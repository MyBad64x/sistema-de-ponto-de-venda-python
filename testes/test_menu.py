import pytest

import pdv.terminal.menu as menu
from pdv.carrinho import Carrinho
from pdv.erros import ErroPDV
from pdv.produtos import buscar_produto, cadastrar_produto, editar_produto


def _digitar(monkeypatch, *respostas):
    respostas = iter(respostas)
    monkeypatch.setattr("builtins.input", lambda _mensagem="": next(respostas))


def test_leitor_de_vendas_adiciona_uma_unidade_e_desfaz_ultima_leitura(
    monkeypatch, caixa
):
    id_produto = cadastrar_produto("Refrigerante", 13, 5, "00123")
    monkeypatch.setattr(menu, "carrinho", Carrinho())
    _digitar(monkeypatch, "00123", "-", "refrigerante", "")

    menu.adicionar_ao_carrinho()

    assert menu.carrinho.itens == {id_produto: 1}


def test_codigo_numerico_inexistente_nao_e_confundido_com_id(coca):
    with pytest.raises(ErroPDV, match="Nenhum produto encontrado"):
        menu._produto_por_entrada(str(coca))


def test_compra_por_leitor_registra_quantidade_custo_e_referencia(monkeypatch):
    id_produto = cadastrar_produto("Refrigerante", 13, 0, "00123")
    _digitar(monkeypatch, "00123", "8,50", "", "Distribuidora", "NF-44", "compra semanal")

    menu.entrada()

    produto = buscar_produto(id_produto)
    assert (produto["estoque"], produto["custo_medio"]) == (1, 8.5)
    from pdv.banco import conexao

    with conexao() as conn:
        compra = conn.execute("SELECT * FROM compras").fetchone()
        movimentacao = conn.execute(
            "SELECT compra_id, quantidade, custo_unitario FROM movimentacoes_estoque "
            "WHERE compra_id = ?",
            (compra["id"],),
        ).fetchone()

    assert (compra["fornecedor"], compra["referencia"], compra["observacao"]) == (
        "Distribuidora", "NF-44", "compra semanal"
    )
    assert tuple(movimentacao) == (compra["id"], 1, 8.5)


def test_contagem_por_leitura_acumula_unidades_e_aplica_ajuste(monkeypatch, coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    _digitar(monkeypatch, "789COCA", "789COCA", "-", "", "s")

    menu.ajustar_por_contagem()

    assert buscar_produto(coca)["estoque"] == 1


def test_contagem_cancelada_nao_altera_estoque(monkeypatch, coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    _digitar(monkeypatch, "789COCA", "", "n")

    menu.ajustar_por_contagem()

    assert buscar_produto(coca)["estoque"] == 5


def test_compra_cancelada_nao_persiste_custo_inicial(monkeypatch, coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    _digitar(monkeypatch, "789COCA", "8", "10", "-", "")

    menu.entrada()

    produto = buscar_produto(coca)
    assert (produto["estoque"], produto["custo_medio"]) == (5, None)


def test_ajuste_manual_aceita_busca_por_codigo(monkeypatch, coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    _digitar(monkeypatch, "789COCA", "3", "Inventário")

    menu.ajuste()

    assert buscar_produto(coca)["estoque"] == 3