"""Janela-base da interface desktop."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    encerrar_sessao = Signal()

    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario

        self.setWindowTitle("PDV Python")
        self.resize(1000, 680)
        self.setMinimumSize(760, 520)

        pagina = QWidget()
        pagina.setObjectName("paginaInicial")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(14)

        cabecalho = QLabel("PDV Python")
        cabecalho.setObjectName("cabecalhoApp")
        nome = QLabel(usuario["nome"])
        nome.setObjectName("nomeUsuario")
        perfil = "Dona" if usuario["perfil"] == "dono" else "Operador"
        perfil_label = QLabel(perfil)
        perfil_label.setObjectName("perfilUsuario")

        layout.addWidget(cabecalho)
        layout.addWidget(nome)
        layout.addWidget(perfil_label)
        layout.addStretch(1)

        sair = QPushButton("Encerrar sessão")
        sair.setObjectName("encerrarSessao")
        sair.clicked.connect(self.encerrar_sessao.emit)
        layout.addWidget(sair)

        self.setCentralWidget(pagina)
        self.setStyleSheet("""
            QMainWindow { background: #f4f6f5; }
            QWidget#paginaInicial { background: #f4f6f5; }
            QLabel#cabecalhoApp { color: #173c35; font-size: 22px; font-weight: 700; }
            QLabel#nomeUsuario { color: #253d36; font-size: 18px; }
            QLabel#perfilUsuario { color: #53655f; font-size: 13px; }
            QPushButton {
                min-height: 38px;
                max-width: 190px;
                color: #173c35;
                background: white;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
            }
            QPushButton:hover { background: #e8efeb; }
        """)