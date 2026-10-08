import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit

from pdv.desktop.janela_principal import MainWindow
from pdv.desktop.login import LoginDialog
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