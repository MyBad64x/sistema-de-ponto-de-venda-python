"""Consulta desktop de comprovantes não fiscais."""

from datetime import datetime

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdv.comprovante import gerar_comprovante, listar_comprovantes
from pdv.desktop.vendas_page import ComprovanteDialog
from pdv.erros import ErroPDV
from pdv.terminal.utilitarios import dinheiro
from pdv.vendas import FORMAS_PAGAMENTO


class ComprovantesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        titulo = QLabel("Comprovantes não fiscais")
        titulo.setObjectName("tituloComprovantes")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.id_input = QLineEdit()
        self.id_input.setObjectName("numeroVendaFiltro")
        self.id_input.setPlaceholderText("Número da venda")
        self.inicio_input = QLineEdit()
        self.inicio_input.setPlaceholderText("Data inicial (dd/mm/aaaa)")
        self.fim_input = QLineEdit()
        self.fim_input.setPlaceholderText("Data final (dd/mm/aaaa)")
        self.pagamento_input = QComboBox()
        self.pagamento_input.addItem("Todas as formas", None)
        for forma in FORMAS_PAGAMENTO:
            self.pagamento_input.addItem(forma, forma)
        filtros.addWidget(self.id_input)
        filtros.addWidget(self.inicio_input)
        filtros.addWidget(self.fim_input)
        filtros.addWidget(self.pagamento_input)
        self.pesquisar_button = QPushButton("Pesquisar")
        self.pesquisar_button.clicked.connect(self.pesquisar)
        filtros.addWidget(self.pesquisar_button)
        layout.addLayout(filtros)

        self.status_label = QLabel("Últimas vendas")
        self.status_label.setObjectName("statusComprovantes")
        layout.addWidget(self.status_label)

        self.resultados_tabela = QTableWidget(0, 4)
        self.resultados_tabela.setObjectName("resultadosComprovantes")
        self.resultados_tabela.setHorizontalHeaderLabels(
            ["Venda", "Data", "Total", "Pagamento"]
        )
        self.resultados_tabela.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.resultados_tabela.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.resultados_tabela.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.resultados_tabela.horizontalHeader().setStretchLastSection(True)
        self.resultados_tabela.cellDoubleClicked.connect(self._abrir_linha)
        layout.addWidget(self.resultados_tabela, 1)

        self.abrir_button = QPushButton("Abrir comprovante")
        self.abrir_button.clicked.connect(self._abrir_selecionado)
        layout.addWidget(self.abrir_button)

        self.setStyleSheet("""
            QLabel#tituloComprovantes { color: #173c35; font-size: 24px; font-weight: 700; }
            QLabel#statusComprovantes { color: #53655f; }
            QLineEdit, QComboBox {
                min-height: 36px;
                padding: 0 8px;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
            QTableWidget#resultadosComprovantes {
                background: white;
                alternate-background-color: #f0f4f1;
                border: 1px solid #d5dfda;
                gridline-color: #e1e8e4;
            }
            QPushButton {
                min-height: 38px;
                padding: 0 14px;
                color: #173c35;
                background: white;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
            }
            QPushButton:hover { background: #e8efeb; }
        """)
        self.pesquisar()

    @staticmethod
    def _ler_data(texto, rotulo):
        texto = texto.strip()
        if not texto:
            return None
        try:
            return datetime.strptime(texto, "%d/%m/%Y").date()
        except ValueError as erro:
            raise ErroPDV(f"{rotulo} inválida. Use dd/mm/aaaa.") from erro

    def pesquisar(self):
        texto_id = self.id_input.text().strip()
        try:
            id_venda = int(texto_id) if texto_id else None
            if texto_id and id_venda <= 0:
                raise ErroPDV("O número da venda deve ser maior que zero.")
            inicio = self._ler_data(self.inicio_input.text(), "Data inicial")
            fim = self._ler_data(self.fim_input.text(), "Data final")
            comprovantes = listar_comprovantes(
                id_venda=id_venda,
                inicio=inicio,
                fim=fim,
                forma_pagamento=self.pagamento_input.currentData(),
            )
        except ValueError as erro:
            self.status_label.setText("O número da venda deve ser um inteiro.")
            return
        except ErroPDV as erro:
            self.status_label.setText(str(erro))
            return

        self.resultados_tabela.setRowCount(len(comprovantes))
        for linha, comprovante in enumerate(comprovantes):
            id_item = QTableWidgetItem(str(comprovante["id"]))
            id_item.setData(256, comprovante["id"])
            self.resultados_tabela.setItem(linha, 0, id_item)
            self.resultados_tabela.setItem(linha, 1, QTableWidgetItem(comprovante["data"]))
            self.resultados_tabela.setItem(
                linha, 2, QTableWidgetItem(dinheiro(comprovante["valor_total"]))
            )
            self.resultados_tabela.setItem(
                linha, 3, QTableWidgetItem(comprovante["forma_pagamento"])
            )

        quantidade = len(comprovantes)
        self.status_label.setText(
            f"{quantidade} venda(s) encontrada(s). Selecione uma para abrir o comprovante."
        )

    def _abrir_linha(self, linha, _coluna):
        self.resultados_tabela.selectRow(linha)
        self._abrir_selecionado()

    def _abrir_selecionado(self):
        linha = self.resultados_tabela.currentRow()
        if linha < 0:
            self.status_label.setText("Selecione uma venda para abrir o comprovante.")
            return

        id_venda = self.resultados_tabela.item(linha, 0).data(256)
        try:
            texto = gerar_comprovante(id_venda)
        except ErroPDV as erro:
            self.status_label.setText(str(erro))
            return

        ComprovanteDialog(texto, self).exec()