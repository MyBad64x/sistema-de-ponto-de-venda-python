import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit

from pdv.banco import conexao
from pdv.comprovante import gerar_comprovante
from pdv.desktop.comprovantes_page import ComprovantesPage
from pdv.desktop.janela_principal import MainWindow
from pdv.desktop.login import LoginDialog
from pdv.desktop.vendas_page import ComprovanteDialog, VendaPage
from pdv.produtos import editar_produto
from pdv.usuarios import criar_usuario


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def test_primeiro_acesso_cria_usuario_dono_com_senha_confirmada(qapp, qtbot):
    tela = LoginDialog()
    qtbot.addWidget(tela)
    tela.nome_input.setText("Alberto")
    tela.login_input.setText("alberto")
    tela.senha_input.setText("senha-segura")
    tela.confirmacao_input.setText("senha-segura")

    qtbot.mouseClick(tela.confirmar_button, Qt.MouseButton.LeftButton)

    assert tela.usuario["perfil"] == "dono"
    assert tela.result() == LoginDialog.DialogCode.Accepted


def test_primeiro_acesso_rejeita_senhas_diferentes(qapp, qtbot):
    tela = LoginDialog()
    qtbot.addWidget(tela)
    tela.nome_input.setText("Alberto")
    tela.login_input.setText("alberto")
    tela.senha_input.setText("senha-segura")
    tela.confirmacao_input.setText("senha-diferente")

    qtbot.mouseClick(tela.confirmar_button, Qt.MouseButton.LeftButton)

    assert tela.result() != LoginDialog.DialogCode.Accepted
    assert tela.erro_label.text() == "As senhas não conferem."


def test_login_usa_autenticacao_existente_e_mascara_senha(qapp, qtbot):
    criar_usuario("Alberto", "alberto", "senha-segura", "operador")
    tela = LoginDialog()
    qtbot.addWidget(tela)
    tela.login_input.setText("alberto")
    tela.senha_input.setText("senha-segura")

    qtbot.mouseClick(tela.confirmar_button, Qt.MouseButton.LeftButton)

    assert tela.usuario["perfil"] == "operador"
    assert tela.senha_input.echoMode() == QLineEdit.EchoMode.Password


def test_janela_exibe_identidade_e_perfil_do_usuario(qapp, qtbot):
    janela = MainWindow({"id": 1, "nome": "Alberto", "perfil": "dono"})
    qtbot.addWidget(janela)

    assert janela.windowTitle() == "PDV Python"
    assert janela.usuario["perfil"] == "dono"
    assert janela.paginas.tabText(0) == "Venda"
    assert janela.paginas.tabText(1) == "Comprovantes"
    assert janela.paginas.tabText(2) == "Estoque"


def test_janela_do_operador_nao_exibe_aba_de_estoque(qapp, qtbot):
    janela = MainWindow({"id": 2, "nome": "Funcionário", "perfil": "operador"})
    qtbot.addWidget(janela)

    assert janela.paginas.count() == 2
    assert [janela.paginas.tabText(indice) for indice in range(2)] == [
        "Venda", "Comprovantes"
    ]


def test_leitura_de_codigo_adiciona_unidade_e_desfazer_remove(
    qapp, qtbot, caixa, coca
):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "00123")
    pagina = VendaPage()
    qtbot.addWidget(pagina)
    pagina.produto_input.setText("00123")

    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)

    assert pagina.carrinho.itens == {coca: 1}
    assert pagina.total_label.text() == "Total: R$ 12,50"
    assert pagina.itens_tabela.item(0, 0).text() == "Coca-Cola 2L"
    assert "custo" not in " ".join(
        pagina.itens_tabela.horizontalHeaderItem(coluna).text().lower()
        for coluna in range(pagina.itens_tabela.columnCount())
    )

    pagina.desfazer_ultima_leitura()

    assert pagina.carrinho.esta_vazio()
    assert not pagina.finalizar_button.isEnabled()


def test_busca_manual_por_nome_adiciona_unidade(qapp, qtbot, caixa, bala):
    pagina = VendaPage()
    qtbot.addWidget(pagina)
    pagina.produto_input.setText("Bala")

    qtbot.keyClick(pagina.produto_input, Qt.Key.Key_Return)

    assert pagina.carrinho.itens == {bala: 1}


def test_finaliza_venda_pix_e_guarda_comprovante(qapp, qtbot, caixa, coca, monkeypatch):
    pagina = VendaPage()
    qtbot.addWidget(pagina)
    pagina.carrinho.adicionar(coca, 1)
    pagina._atualizar_carrinho()
    monkeypatch.setattr(
        "pdv.desktop.vendas_page.QInputDialog.getItem",
        lambda *args, **kwargs: ("PIX", True),
    )
    monkeypatch.setattr(
        ComprovanteDialog,
        "exec",
        lambda self: QDialog.DialogCode.Accepted,
    )

    pagina.finalizar()

    assert pagina.carrinho.esta_vazio()
    with conexao() as conn:
        venda = conn.execute("SELECT * FROM vendas").fetchone()
    assert venda["forma_pagamento"] == "PIX"
    assert f"Venda #{venda['id']}" in gerar_comprovante(venda["id"])


def test_finaliza_pagamento_em_dinheiro_com_troco(
    qapp, qtbot, caixa, coca, monkeypatch
):
    pagina = VendaPage()
    qtbot.addWidget(pagina)
    pagina.carrinho.adicionar(coca, 1)
    pagina._atualizar_carrinho()
    monkeypatch.setattr(
        "pdv.desktop.vendas_page.QInputDialog.getItem",
        lambda *args, **kwargs: ("Dinheiro", True),
    )
    monkeypatch.setattr(
        "pdv.desktop.vendas_page.QInputDialog.getDouble",
        lambda *args, **kwargs: (20, True),
    )
    monkeypatch.setattr(
        ComprovanteDialog,
        "exec",
        lambda self: QDialog.DialogCode.Accepted,
    )

    pagina.finalizar()

    with conexao() as conn:
        venda = conn.execute("SELECT * FROM vendas").fetchone()
    assert (venda["valor_recebido"], venda["troco"]) == (20, 7.5)


def test_consulta_desktop_filtra_e_abre_comprovante(qapp, qtbot, caixa, coca, monkeypatch):
    pagina_venda = VendaPage()
    qtbot.addWidget(pagina_venda)
    pagina_venda.carrinho.adicionar(coca, 1)
    from pdv.vendas import finalizar_venda

    resultado = finalizar_venda(pagina_venda.carrinho, "PIX")
    pagina = ComprovantesPage()
    qtbot.addWidget(pagina)
    pagina.id_input.setText(str(resultado.id_venda))
    pagina.pesquisar()

    assert pagina.resultados_tabela.rowCount() == 1
    assert pagina.resultados_tabela.item(0, 0).text() == str(resultado.id_venda)

    textos = []
    monkeypatch.setattr(
        ComprovanteDialog,
        "exec",
        lambda self: textos.append(self.texto) or QDialog.DialogCode.Accepted,
    )
    pagina.resultados_tabela.selectRow(0)
    pagina._abrir_selecionado()

    assert len(textos) == 1
    assert f"Venda #{resultado.id_venda}" in textos[0]