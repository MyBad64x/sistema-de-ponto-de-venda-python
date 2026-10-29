"""Fluxo de venda da interface desktop."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdv.caixa import DINHEIRO, caixa_aberto
from pdv.carrinho import Carrinho
from pdv.comprovante import gerar_comprovante, salvar_comprovante
from pdv.erros import ErroPDV, EstoqueInsuficiente
from pdv.produtos import buscar_produto_por_codigo_barras, buscar_produtos_por_nome
from pdv.terminal.utilitarios import dinheiro
from pdv.vendas import FORMAS_PAGAMENTO, finalizar_venda


class ComprovanteDialog(QDialog):
    def __init__(self, texto, parent=None):
        super().__init__(parent)
        self.texto = texto
        self.setWindowTitle("Comprovante não fiscal")
        self.resize(460, 560)

        layout = QVBoxLayout(self)
        conteudo = QPlainTextEdit()
        conteudo.setReadOnly(True)
        conteudo.setPlainText(texto)
        layout.addWidget(conteudo)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes)


class VendaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.carrinho = Carrinho()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        titulo = QLabel("Venda")
        titulo.setObjectName("tituloVenda")
        layout.addWidget(titulo)

        instrucoes = QLabel(
            "Leia o código de barras ou pesquise pelo nome. Cada leitura adiciona uma unidade."
        )
        instrucoes.setObjectName("instrucoesVenda")
        layout.addWidget(instrucoes)

        self.aviso_caixa_label = QLabel(
            "Caixa fechado. Abra o caixa na aba Caixa para registrar vendas."
        )
        self.aviso_caixa_label.setObjectName("avisoCaixa")
        layout.addWidget(self.aviso_caixa_label)
        self.produto_input = QLineEdit()
        self.produto_input.setObjectName("produtoInput")
        self.produto_input.setPlaceholderText("Código de barras ou nome do produto")
        self.produto_input.setMinimumHeight(42)
        self.produto_input.returnPressed.connect(self.adicionar_entrada)
        layout.addWidget(self.produto_input)

        self.itens_tabela = QTableWidget(0, 4)
        self.itens_tabela.setObjectName("itensVenda")
        self.itens_tabela.setHorizontalHeaderLabels(
            ["Produto", "Quantidade", "Preço unitário", "Subtotal"]
        )
        self.itens_tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.itens_tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.itens_tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.itens_tabela.horizontalHeader().setSectionResizeMode(0, self.itens_tabela.horizontalHeader().ResizeMode.Stretch)
        for coluna in range(1, 4):
            self.itens_tabela.horizontalHeader().setSectionResizeMode(
                coluna,
                self.itens_tabela.horizontalHeader().ResizeMode.ResizeToContents,
            )
        for coluna in range(1, 4):
            self.itens_tabela.horizontalHeaderItem(coluna).setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        layout.addWidget(self.itens_tabela, 1)

        acoes = QHBoxLayout()
        self.desfazer_button = QPushButton("Desfazer última leitura")
        self.desfazer_button.clicked.connect(self.desfazer_ultima_leitura)
        self.remover_button = QPushButton("Remover produto")
        self.remover_button.clicked.connect(self.remover_produto_selecionado)
        self.limpar_button = QPushButton("Limpar carrinho")
        self.limpar_button.clicked.connect(self.limpar_carrinho)
        acoes.addWidget(self.desfazer_button)
        acoes.addWidget(self.remover_button)
        acoes.addWidget(self.limpar_button)
        acoes.addStretch(1)
        layout.addLayout(acoes)

        rodape = QHBoxLayout()
        self.status_label = QLabel("Pronto para registrar produtos.")
        self.status_label.setObjectName("statusVenda")
        self.total_label = QLabel("Total: R$ 0,00")
        self.total_label.setObjectName("totalVenda")
        self.finalizar_button = QPushButton("Finalizar venda")
        self.finalizar_button.setObjectName("finalizarVenda")
        self.finalizar_button.setMinimumSize(170, 46)
        self.finalizar_button.clicked.connect(self.finalizar)
        rodape.addWidget(self.status_label, 1)
        rodape.addWidget(self.total_label)
        rodape.addWidget(self.finalizar_button)
        layout.addLayout(rodape)

        self.setStyleSheet("""
            QLabel#tituloVenda { color: #173c35; font-size: 24px; font-weight: 700; }
            QLabel#instrucoesVenda, QLabel#statusVenda { color: #53655f; }
            QLabel#avisoCaixa {
                padding: 8px 12px;
                color: #7a4b00;
                background: #fff3d6;
                border: 1px solid #e6c987;
                border-radius: 4px;
            }
            QLineEdit#produtoInput {
                padding: 0 12px;
                color: #20352e;
                selection-background-color: #17634f;
                selection-color: #ffffff;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
                font-size: 16px;
            }
            QLineEdit#produtoInput:focus { border: 2px solid #24735d; }
            QTableWidget#itensVenda {
                color: #20352e;
                background: white;
                alternate-background-color: #f0f4f1;
                border: 1px solid #d5dfda;
                gridline-color: #e1e8e4;
            }
            QHeaderView::section {
                min-height: 30px;
                padding: 0 8px;
                color: #20352e;
                background: #e8efeb;
                border: 0;
                border-bottom: 1px solid #bdcbc5;
            }
            QLabel#totalVenda { color: #173c35; font-size: 22px; font-weight: 700; }
            QPushButton {
                min-height: 38px;
                padding: 0 14px;
                color: #173c35;
                background: white;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
            }
            QPushButton:hover { background: #e8efeb; }
            QPushButton#finalizarVenda {
                color: white;
                background: #17634f;
                border: 0;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton#finalizarVenda:hover { background: #104c3d; }
            QPushButton:disabled { color: #8a9992; background: #eef2f0; border: 1px solid #d5dfda; }
            QPushButton#finalizarVenda:disabled { color: #eef2f0; background: #9db5ac; border: 0; }
        """)
        self.atualizar_caixa()

    def ao_exibir(self):
        """Chamada pela janela quando a aba Venda é aberta: o caixa pode ter mudado."""
        self.atualizar_caixa()
        if self._caixa_esta_aberto:
            self.produto_input.setFocus()  # pronto para a próxima leitura

    def atualizar_caixa(self):
        """Mostra o aviso e libera ou trava o botão conforme o caixa esteja aberto."""
        self._caixa_esta_aberto = caixa_aberto() is not None
        self.aviso_caixa_label.setVisible(not self._caixa_esta_aberto)

        # o carrinho exige caixa aberto (regra em pdv/carrinho.py), então a leitura também trava
        self.produto_input.setEnabled(self._caixa_esta_aberto)
        self.produto_input.setPlaceholderText(
            "Código de barras ou nome do produto"
            if self._caixa_esta_aberto
            else "Abra o caixa para registrar vendas"
        )
        self._atualizar_carrinho()

    def _mostrar_erro(self, mensagem):
        self.status_label.setText(mensagem)
        self.status_label.setStyleSheet("color: #a12f2f;")

    def _resolver_produto(self, entrada):
        produto = buscar_produto_por_codigo_barras(entrada, incluir_inativos=True)
        if produto is not None:
            if not produto["ativo"]:
                raise ErroPDV(f"O produto '{produto['nome']}' está desativado.")
            return produto

        resultados = buscar_produtos_por_nome(entrada)
        if not resultados:
            raise ErroPDV(f"Nenhum produto encontrado para '{entrada}'.")
        if len(resultados) == 1:
            return resultados[0]

        nomes = [f"{produto['nome']} (ID {produto['id']})" for produto in resultados]
        escolha, confirmou = QInputDialog.getItem(
            self,
            "Selecionar produto",
            "Mais de um produto corresponde à busca:",
            nomes,
            0,
            False,
        )
        if not confirmou:
            return None
        indice = nomes.index(escolha)
        return resultados[indice]

    def adicionar_entrada(self):
        entrada = self.produto_input.text().strip()
        self.produto_input.clear()

        if not entrada:
            self.produto_input.setFocus()
            return

        if entrada == "-":
            self.desfazer_ultima_leitura()
            return

        try:
            produto = self._resolver_produto(entrada)
            if produto is None:
                return
            item = self.carrinho.adicionar(produto["id"], 1)
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            self.produto_input.setFocus()
            return

        self.status_label.setStyleSheet("")
        self.status_label.setText(f"{item.nome} adicionado ao carrinho.")
        self._atualizar_carrinho()
        self.produto_input.setFocus()

    def _atualizar_carrinho(self):
        itens = self.carrinho.detalhar()
        self.itens_tabela.setRowCount(len(itens))

        for linha, item in enumerate(itens):
            celula_nome = QTableWidgetItem(item.nome)
            celula_nome.setData(Qt.ItemDataRole.UserRole, item.id_produto)
            self.itens_tabela.setItem(linha, 0, celula_nome)
            self.itens_tabela.setItem(linha, 1, QTableWidgetItem(str(item.quantidade)))
            self.itens_tabela.setItem(linha, 2, QTableWidgetItem(dinheiro(item.preco_unitario)))
            self.itens_tabela.setItem(linha, 3, QTableWidgetItem(dinheiro(item.subtotal)))
            for coluna in range(1, 4):
                self.itens_tabela.item(linha, coluna).setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )

        self.total_label.setText(f"Total: {dinheiro(self.carrinho.total())}")
        self.finalizar_button.setEnabled(self._caixa_esta_aberto and not self.carrinho.esta_vazio())
        self.desfazer_button.setEnabled(bool(itens))
        self.remover_button.setEnabled(bool(itens))
        self.limpar_button.setEnabled(bool(itens))

    def desfazer_ultima_leitura(self):
        try:
            id_produto = self.carrinho.desfazer_ultima_adicao()
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
        else:
            self.status_label.setStyleSheet("")
            self.status_label.setText(f"Leitura desfeita: produto #{id_produto}.")
        self._atualizar_carrinho()
        self.produto_input.setFocus()

    def remover_produto_selecionado(self):
        linha = self.itens_tabela.currentRow()
        if linha < 0:
            self._mostrar_erro("Selecione um produto para remover.")
            return
        id_produto = self.itens_tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        self.carrinho.remover(id_produto)
        self._atualizar_carrinho()
        self.produto_input.setFocus()

    def limpar_carrinho(self):
        resposta = QMessageBox.question(
            self,
            "Limpar carrinho",
            "Remover todos os produtos do carrinho?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return
        self.carrinho.limpar()
        self._atualizar_carrinho()
        self.status_label.setText("Carrinho limpo.")
        self.produto_input.setFocus()

    def finalizar(self):
        if self.carrinho.esta_vazio():
            return

        forma_pagamento, confirmou = QInputDialog.getItem(
            self,
            "Pagamento",
            "Forma de pagamento:",
            list(FORMAS_PAGAMENTO),
            0,
            False,
        )
        if not confirmou:
            return

        valor_recebido = None
        if forma_pagamento == DINHEIRO:
            valor_recebido, confirmou = QInputDialog.getDouble(
                self,
                "Pagamento em dinheiro",
                "Valor recebido:",
                self.carrinho.total(),
                self.carrinho.total(),
                1_000_000_000,
                2,
            )
            if not confirmou:
                return

        try:
            resultado = finalizar_venda(
                self.carrinho,
                forma_pagamento,
                valor_recebido=valor_recebido,
            )
        except EstoqueInsuficiente as erro:
            resposta = QMessageBox.question(
                self,
                "Estoque insuficiente",
                f"{erro}\nDeseja concluir mesmo assim, permitindo estoque negativo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resposta != QMessageBox.StandardButton.Yes:
                return
            try:
                resultado = finalizar_venda(
                    self.carrinho,
                    forma_pagamento,
                    permitir_estoque_negativo=True,
                    valor_recebido=valor_recebido,
                )
            except ErroPDV as erro_final:
                self._mostrar_erro(str(erro_final))
                return
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            self.atualizar_caixa()  # o caixa pode ter sido fechado em outro lugar
            return

        texto = gerar_comprovante(resultado.id_venda)
        try:
            salvar_comprovante(resultado.id_venda)
        except OSError:
            QMessageBox.warning(
                self,
                "Comprovante",
                "A venda foi registrada, mas não foi possível salvar o arquivo do comprovante.",
            )

        self._atualizar_carrinho()
        self.status_label.setStyleSheet("")
        self.status_label.setText(f"Venda #{resultado.id_venda} finalizada.")
        ComprovanteDialog(texto, self).exec()
        self.produto_input.setFocus()