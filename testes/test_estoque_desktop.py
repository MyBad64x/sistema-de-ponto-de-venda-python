from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

from pdv.banco import conexao
from pdv.desktop.estoque_page import (
    CompraPage,
    ContagemPage,
    HistoricoComprasPage,
    PrecificacaoDialog,
    ProdutosEstoquePage,
)
from pdv.estoque import definir_custo_inicial
from pdv.gestao import listar_produtos_gestao
from pdv.produtos import buscar_produto, cadastrar_produto, editar_produto


def test_reposicao_por_leitura_registra_compra_e_custo_medio(
    monkeypatch, qtbot
):
    produto_id = cadastrar_produto("Refrigerante", 13, 0, "00123")
    monkeypatch.setattr(
        "pdv.desktop.estoque_page.QInputDialog.getDouble",
        lambda *args, **kwargs: (8.5, True),
    )
    pagina = CompraPage()
    qtbot.addWidget(pagina)
    pagina.fornecedor_input.setText("Distribuidora Central")
    pagina.referencia_input.setText("REC-12")
    pagina.produto_input.setText("00123")
    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)

    assert pagina.itens[produto_id]["quantidade"] == 1
    pagina.salvar_compra()

    produto = buscar_produto(produto_id)
    assert (produto["estoque"], produto["custo_medio"]) == (1, 8.5)
    with conexao() as conn:
        compra = conn.execute("SELECT * FROM compras").fetchone()
    assert (compra["fornecedor"], compra["referencia"]) == (
        "Distribuidora Central", "REC-12"
    )


def test_reposicao_estoque_legado_pede_custo_inicial_e_calcula_media(
    monkeypatch, qtbot, coca
):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    custos = iter(((8, True), (10, True)))
    monkeypatch.setattr(
        "pdv.desktop.estoque_page.QInputDialog.getDouble",
        lambda *args, **kwargs: next(custos),
    )
    pagina = CompraPage()
    qtbot.addWidget(pagina)
    pagina.produto_input.setText("789COCA")
    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)
    pagina.salvar_compra()

    produto = buscar_produto(coca)
    assert (produto["estoque"], produto["custo_medio"]) == (6, 8.33)


def test_desfazer_reposicao_nao_grava_compra(monkeypatch, qtbot):
    produto_id = cadastrar_produto("Produto novo", 12, 0, "00123")
    monkeypatch.setattr(
        "pdv.desktop.estoque_page.QInputDialog.getDouble",
        lambda *args, **kwargs: (8.5, True),
    )
    pagina = CompraPage()
    qtbot.addWidget(pagina)
    pagina.produto_input.setText("00123")
    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)
    pagina.desfazer_ultima_leitura()

    assert not pagina.itens
    assert not pagina.salvar_button.isEnabled()
    assert buscar_produto(produto_id)["estoque"] == 0
    with conexao() as conn:
        assert conn.execute("SELECT COUNT(*) FROM compras").fetchone()[0] == 0


def test_contagem_aplica_ajuste_somente_apos_confirmacao(
    monkeypatch, qtbot, coca
):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    monkeypatch.setattr(
        "pdv.desktop.estoque_page.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    pagina = ContagemPage()
    qtbot.addWidget(pagina)
    pagina.produto_input.setText("789COCA")
    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)
    pagina.produto_input.setText("789COCA")
    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)
    pagina.aplicar_contagem()

    assert buscar_produto(coca)["estoque"] == 2
    assert not pagina.contagens


def test_contagem_cancelada_nao_altera_estoque(monkeypatch, qtbot, coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789COCA")
    monkeypatch.setattr(
        "pdv.desktop.estoque_page.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    pagina = ContagemPage()
    qtbot.addWidget(pagina)
    pagina.produto_input.setText("789COCA")
    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)
    pagina.aplicar_contagem()

    assert buscar_produto(coca)["estoque"] == 5
    assert pagina.contagens


def test_historico_compras_filtra_por_fornecedor(qtbot, coca):
    definir_custo_inicial(coca, 8)
    from pdv.estoque import registrar_compra

    registrar_compra(
        [(coca, 2, 9)], fornecedor="Distribuidora Central", referencia="REC-44"
    )
    pagina = HistoricoComprasPage()
    qtbot.addWidget(pagina)
    pagina.fornecedor_input.setText("central")
    pagina.pesquisar()

    assert pagina.compras_tabela.rowCount() == 1
    assert pagina.compras_tabela.item(0, 1).text() == "Distribuidora Central"
    assert pagina.compras_tabela.item(0, 6).text() == "R$ 18,00"


def test_precificacao_atualiza_resultado_ao_alterar_preco(coca):
    definir_custo_inicial(coca, 8)
    produto = next(
        item for item in listar_produtos_gestao() if item["id"] == coca
    )
    dialogo = PrecificacaoDialog(produto)
    dialogo.preco_input.setValue(15)

    assert "R$ 7,00" in dialogo.resultado_label.text()
    assert "46.67%" in dialogo.resultado_label.text()
    assert "87.50%" in dialogo.resultado_label.text()