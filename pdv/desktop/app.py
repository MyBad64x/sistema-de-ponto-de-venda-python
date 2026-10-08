"""Ponto de entrada da interface desktop experimental."""

import sys

from PySide6.QtWidgets import QApplication

from pdv.banco import criar_tabelas
from pdv.desktop.janela_principal import MainWindow
from pdv.desktop.login import LoginDialog


def main():
    criar_tabelas()
    aplicacao = QApplication(sys.argv)
    aplicacao.setApplicationName("PDV Python")
    aplicacao.setStyle("Fusion")

    login = LoginDialog()
    if login.exec() != LoginDialog.DialogCode.Accepted:
        return 0

    janela = MainWindow(login.usuario)
    janela.encerrar_sessao.connect(aplicacao.quit)
    janela.show()
    return aplicacao.exec()