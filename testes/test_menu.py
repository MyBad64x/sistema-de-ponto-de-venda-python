import pytest

import pdv.terminal.menu as menu
from pdv.carrinho import Carrinho
from pdv.estoque import definir_custo_inicial, registrar_compra
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


def test_operador_nao_recebe_opcoes_de_gestao_ou_relatorio_financeiro():
    descricoes = [descricao for _, descricao, _ in menu._opcoes_menu({"perfil": "operador"})]

    assert "Gestão e precificação" not in descricoes
    assert "Relatórios" not in descricoes


def test_dono_tem_acesso_a_gestao_e_relatorios():
    descricoes = [descricao for _, descricao, _ in menu._opcoes_menu({"perfil": "dono"})]

    assert "Estoque" in descricoes
    assert "Relatórios" in descricoes


def test_precificar_produto_persiste_novo_preco_apos_confirmacao(
    monkeypatch, coca, capsys
):
    definir_custo_inicial(coca, 8)
    _digitar(monkeypatch, "Coca-Cola", "15", "s")

    menu.precificar_produto()

    assert buscar_produto(coca)["preco"] == 15
    assert "Margem bruta sobre a venda" in capsys.readouterr().out


def test_precificar_produto_nao_persiste_novo_preco_se_cancelado(
    monkeypatch, coca
):
    _digitar(monkeypatch, "Coca-Cola", "15", "n")

    menu.precificar_produto()

    assert buscar_produto(coca)["preco"] == 12.5


def test_consulta_compras_filtra_por_fornecedor_e_exibe_registro(
    monkeypatch, coca, capsys
):
    definir_custo_inicial(coca, 8)
    registrar_compra(
        [(coca, 2, 9)], fornecedor="Distribuidora Central", referencia="REC-44"
    )
    _digitar(monkeypatch, "Central", "", "", "")

    menu.consultar_compras()

    saida = capsys.readouterr().out
    assert "Distribuidora Central" in saida
    assert "REC-44" in saida


def test_consulta_gerencial_exibe_custo_e_margem(monkeypatch, coca, capsys):
    definir_custo_inicial(coca, 8)
    _digitar(monkeypatch, "1", "1")

    menu.consultar_produtos_gestao()

    saida = capsys.readouterr().out
    assert "CUSTO" in saida
    assert "MARGEM" in saida
    assert "R$ 8,00" in saida