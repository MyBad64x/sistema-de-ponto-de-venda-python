"""Janela-base da interface desktop."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pdv.desktop.comprovantes_page import ComprovantesPage
from pdv.desktop.estoque_page import EstoquePage
from pdv.desktop.vendas_page import VendaPage


class MainWindow(QMainWindow):
    encerrar_sessao = Signal()

    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario

        self.setWindowTitle("PDV Python")
        self.resize(1000, 680)
        self.setMinimumSize(760, 520)

        pagina = QWidget()
        pagina.setObjectName("paginaPrincipal")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        barra_superior = QWidget()
        cabecalho_layout = QHBoxLayout(barra_superior)
        cabecalho_layout.setContentsMargins(10, 0, 10, 0)
        cabecalho = QLabel("PDV Python")
        cabecalho.setObjectName("cabecalhoApp")
        nome = QLabel(usuario["nome"])
        nome.setObjectName("nomeUsuario")
        perfil = "Dona" if usuario["perfil"] == "dono" else "Operador"
        perfil_label = QLabel(perfil)
        perfil_label.setObjectName("perfilUsuario")
        cabecalho_layout.addWidget(cabecalho)
        cabecalho_layout.addStretch(1)
        cabecalho_layout.addWidget(nome)
        cabecalho_layout.addWidget(perfil_label)

        sair = QPushButton("Encerrar sessão")
        sair.setObjectName("encerrarSessao")
        sair.clicked.connect(self.encerrar_sessao.emit)
        cabecalho_layout.addWidget(sair)

        self.paginas = QTabWidget()
        self.paginas.setObjectName("paginasPDV")
        self.paginas.addTab(VendaPage(), "Venda")
        self.paginas.addTab(ComprovantesPage(), "Comprovantes")
        if usuario["perfil"] == "dono":
            self.paginas.addTab(EstoquePage(), "Estoque")
        layout.addWidget(barra_superior)
        layout.addWidget(self.paginas, 1)

        self.setCentralWidget(pagina)
        self.setStyleSheet("""
            QMainWindow { background: #f4f6f5; }
            QWidget#paginaPrincipal { background: #f4f6f5; }
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
            QTabWidget::pane { border: 1px solid #d5dfda; background: #f4f6f5; }
            QTabBar::tab {
                min-width: 100px;
                min-height: 38px;
                padding: 0 16px;
                color: #53655f;
                background: #e8efeb;
                border: 1px solid #d5dfda;
            }
            QTabBar::tab:selected { color: #173c35; background: #ffffff; font-weight: 600; }
        """)