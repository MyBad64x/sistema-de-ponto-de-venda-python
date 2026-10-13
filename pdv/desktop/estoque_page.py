"""Gestão desktop do estoque, disponível somente para a dona."""

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pdv.estoque import ajustar_estoque_em_lote, registrar_compra
from pdv.erros import ErroPDV
from pdv.gestao import listar_compras, listar_produtos_gestao
from pdv.precificacao import calcular_rentabilidade
from pdv.produtos import (
    buscar_produto_por_codigo_barras,
    buscar_produtos_por_nome,
    editar_produto,
)
from pdv.terminal.utilitarios import dinheiro


FILTROS_ESTOQUE = {
    "Todos": None,
    "Parados há mais de 30 dias": "parados",
    "Cadastrados nos últimos 30 dias": "recentes",
    "Sem custo conhecido": "sem_custo",
}

ORDENACOES_ESTOQUE = {
    "Nome": "nome",
    "Mais recentes": "recentes",
    "Maior preço": "preco_maior",
    "Menor preço": "preco_menor",
    "Maior custo": "custo_maior",
    "Menor custo": "custo_menor",
    "Maior lucro por unidade": "lucro_maior",
    "Menor lucro por unidade": "lucro_menor",
    "Maior margem": "margem_maior",
    "Menor margem": "margem_menor",
    "Maior estoque": "estoque_maior",
    "Menor estoque": "estoque_menor",
}


class PrecificacaoDialog(QDialog):
    def __init__(self, produto, parent=None):
        super().__init__(parent)
        self.produto = produto
        self.setWindowTitle("Simular preço de venda")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        titulo = QLabel(produto["nome"])
        titulo.setObjectName("tituloPrecificacao")
        layout.addWidget(titulo)

        formulario = QFormLayout()
        self.custo_label = QLabel(
            dinheiro(produto["custo_medio"])
            if produto["custo_medio"] is not None
            else "Desconhecido"
        )
        formulario.addRow("Custo médio", self.custo_label)

        self.preco_input = QDoubleSpinBox()
        self.preco_input.setObjectName("novoPrecoInput")
        self.preco_input.setRange(0, 1_000_000_000)
        self.preco_input.setDecimals(2)
        self.preco_input.setSingleStep(0.5)
        self.preco_input.setValue(produto["preco"])
        formulario.addRow("Preço de venda", self.preco_input)
        layout.addLayout(formulario)

        self.resultado_label = QLabel()
        self.resultado_label.setObjectName("resultadoPrecificacao")
        self.resultado_label.setWordWrap(True)
        layout.addWidget(self.resultado_label)

        self.preco_input.valueChanged.connect(self._atualizar_resultado)
        self._atualizar_resultado(self.preco_input.value())

        botoes = QDialogButtonBox()
        self.salvar_button = botoes.addButton(
            "Salvar preço", QDialogButtonBox.ButtonRole.AcceptRole
        )
        botoes.addButton(QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        self.setStyleSheet("""
            QLabel#tituloPrecificacao { color: #173c35; font-size: 18px; font-weight: 700; }
            QLabel#resultadoPrecificacao { color: #253d36; font-size: 14px; }
            QDoubleSpinBox {
                min-height: 34px;
                padding: 0 8px;
                color: #20352e;
                selection-background-color: #17634f;
                selection-color: #ffffff;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
        """)

    def _atualizar_resultado(self, preco):
        rentabilidade = calcular_rentabilidade(preco, self.produto["custo_medio"])
        if rentabilidade is None:
            self.resultado_label.setText(
                "Custo desconhecido. Registre uma compra para calcular lucro e margem."
            )
            return

        margem = rentabilidade.margem_bruta_percentual
        acrescimo = rentabilidade.acrescimo_sobre_custo_percentual
        linhas = [
            f"Lucro bruto por unidade: {dinheiro(rentabilidade.lucro_bruto_unitario)}",
            "Margem sobre a venda: não calculável" if margem is None
            else f"Margem sobre a venda: {margem:.2f}%",
            "Acréscimo sobre o custo: não calculável" if acrescimo is None
            else f"Acréscimo sobre o custo: {acrescimo:.2f}%",
        ]
        self.resultado_label.setText("\n".join(linhas))


def _resolver_produto(entrada, parent):
    entrada = entrada.strip()
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
        parent,
        "Selecionar produto",
        "Mais de um produto corresponde à busca:",
        nomes,
        0,
        False,
    )
    if not confirmou:
        return None
    return resultados[nomes.index(escolha)]


class ProdutosEstoquePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        titulo = QLabel("Produtos e precificação")
        titulo.setObjectName("tituloEstoque")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.filtro_input = QComboBox()
        self.filtro_input.setObjectName("filtroEstoque")
        self.filtro_input.addItems(FILTROS_ESTOQUE)
        self.ordenacao_input = QComboBox()
        self.ordenacao_input.setObjectName("ordenacaoEstoque")
        self.ordenacao_input.addItems(ORDENACOES_ESTOQUE)
        self.atualizar_button = QPushButton("Atualizar")
        self.atualizar_button.clicked.connect(self.atualizar)
        filtros.addWidget(QLabel("Mostrar"))
        filtros.addWidget(self.filtro_input, 1)
        filtros.addWidget(QLabel("Ordenar por"))
        filtros.addWidget(self.ordenacao_input, 1)
        filtros.addWidget(self.atualizar_button)
        layout.addLayout(filtros)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusEstoque")
        layout.addWidget(self.status_label)

        self.produtos_tabela = QTableWidget(0, 7)
        self.produtos_tabela.setObjectName("produtosEstoque")
        self.produtos_tabela.setHorizontalHeaderLabels(
            ["Produto", "Estoque", "Preço", "Custo médio", "Lucro/un.", "Margem", "Última atividade"]
        )
        self.produtos_tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.produtos_tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.produtos_tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.produtos_tabela.horizontalHeader().setSectionResizeMode(
            0, self.produtos_tabela.horizontalHeader().ResizeMode.Stretch
        )
        for coluna in range(1, 7):
            self.produtos_tabela.horizontalHeader().setSectionResizeMode(
                coluna,
                self.produtos_tabela.horizontalHeader().ResizeMode.ResizeToContents,
            )
        layout.addWidget(self.produtos_tabela, 1)

        acoes = QHBoxLayout()
        acoes.addStretch(1)
        self.precificar_button = QPushButton("Simular/alterar preço")
        self.precificar_button.setObjectName("precificarProduto")
        self.precificar_button.clicked.connect(self.precificar_selecionado)
        acoes.addWidget(self.precificar_button)
        layout.addLayout(acoes)

        self.setStyleSheet("""
            QLabel#tituloEstoque { color: #173c35; font-size: 24px; font-weight: 700; }
            QLabel#statusEstoque { color: #53655f; }
            QComboBox {
                min-height: 36px;
                padding: 0 8px;
                color: #20352e;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
            QTableWidget#produtosEstoque {
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
        self.atualizar()

    def atualizar(self):
        filtro = FILTROS_ESTOQUE[self.filtro_input.currentText()]
        ordenacao = ORDENACOES_ESTOQUE[self.ordenacao_input.currentText()]
        produtos = listar_produtos_gestao(filtro=filtro, ordenar_por=ordenacao)
        self.produtos_tabela.setRowCount(len(produtos))

        for linha, produto in enumerate(produtos):
            nome = QTableWidgetItem(produto["nome"])
            nome.setData(Qt.ItemDataRole.UserRole, produto["id"])
            self.produtos_tabela.setItem(linha, 0, nome)
            self.produtos_tabela.setItem(linha, 1, QTableWidgetItem(str(produto["estoque"])))
            self.produtos_tabela.setItem(linha, 2, QTableWidgetItem(dinheiro(produto["preco"])))
            self.produtos_tabela.setItem(
                linha, 3,
                QTableWidgetItem(
                    dinheiro(produto["custo_medio"])
                    if produto["custo_medio"] is not None else "Desconhecido"
                ),
            )
            self.produtos_tabela.setItem(
                linha, 4,
                QTableWidgetItem(
                    dinheiro(produto["lucro_bruto_unitario"])
                    if produto["lucro_bruto_unitario"] is not None else "-"
                ),
            )
            margem = produto["margem_bruta_percentual"]
            self.produtos_tabela.setItem(
                linha, 5, QTableWidgetItem(f"{margem:.2f}%" if margem is not None else "-")
            )
            self.produtos_tabela.setItem(
                linha, 6, QTableWidgetItem(produto["ultima_atividade"] or "Sem data")
            )

        self.status_label.setText(f"{len(produtos)} produto(s) encontrado(s).")
        self.precificar_button.setEnabled(bool(produtos))

    def precificar_selecionado(self):
        linha = self.produtos_tabela.currentRow()
        if linha < 0:
            self.status_label.setText("Selecione um produto para precificar.")
            return
        id_produto = self.produtos_tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        produto = next(
            (item for item in listar_produtos_gestao() if item["id"] == id_produto),
            None,
        )
        if produto is None:
            self.status_label.setText("O produto não está mais disponível.")
            self.atualizar()
            return

        dialogo = PrecificacaoDialog(produto, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        novo_preco = dialogo.preco_input.value()
        try:
            editar_produto(id_produto, produto["nome"], novo_preco)
        except ErroPDV as erro:
            QMessageBox.warning(self, "Preço não atualizado", str(erro))
            return

        self.atualizar()


class CompraPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.itens = {}
        self.adicoes = []
        self.custos_iniciais = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        titulo = QLabel("Reposição")
        titulo.setObjectName("tituloCompra")
        layout.addWidget(titulo)
        layout.addWidget(QLabel(
            "Leia cada unidade recebida ou digite o nome. Use - para desfazer a última leitura."
        ))

        self.produto_input = QLineEdit()
        self.produto_input.setObjectName("produtoCompraInput")
        self.produto_input.setPlaceholderText("Código de barras ou nome do produto")
        self.produto_input.setMinimumHeight(40)
        self.produto_input.returnPressed.connect(self.adicionar_entrada)
        layout.addWidget(self.produto_input)

        dados_compra = QFormLayout()
        self.fornecedor_input = QLineEdit()
        self.referencia_input = QLineEdit()
        self.observacao_input = QLineEdit()
        dados_compra.addRow("Fornecedor", self.fornecedor_input)
        dados_compra.addRow("Referência do comprovante", self.referencia_input)
        dados_compra.addRow("Observação", self.observacao_input)
        layout.addLayout(dados_compra)

        self.itens_tabela = QTableWidget(0, 4)
        self.itens_tabela.setObjectName("itensCompra")
        self.itens_tabela.setHorizontalHeaderLabels(
            ["Produto", "Unidades recebidas", "Custo unitário", "Total do item"]
        )
        self.itens_tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.itens_tabela.horizontalHeader().setSectionResizeMode(
            0, self.itens_tabela.horizontalHeader().ResizeMode.Stretch
        )
        for coluna in range(1, 4):
            self.itens_tabela.horizontalHeader().setSectionResizeMode(
                coluna,
                self.itens_tabela.horizontalHeader().ResizeMode.ResizeToContents,
            )
        layout.addWidget(self.itens_tabela, 1)

        acoes = QHBoxLayout()
        self.status_label = QLabel("Nenhuma compra em andamento.")
        self.status_label.setObjectName("statusCompra")
        acoes.addWidget(self.status_label, 1)
        self.desfazer_button = QPushButton("Desfazer leitura")
        self.desfazer_button.clicked.connect(self.desfazer_ultima_leitura)
        acoes.addWidget(self.desfazer_button)
        self.salvar_button = QPushButton("Registrar compra")
        self.salvar_button.setObjectName("registrarCompra")
        self.salvar_button.clicked.connect(self.salvar_compra)
        acoes.addWidget(self.salvar_button)
        layout.addLayout(acoes)

        self.setStyleSheet("""
            QLabel#tituloCompra { color: #173c35; font-size: 22px; font-weight: 700; }
            QLabel#statusCompra { color: #53655f; }
            QLineEdit {
                min-height: 34px;
                padding: 0 9px;
                color: #20352e;
                selection-background-color: #17634f;
                selection-color: #ffffff;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
            QTableWidget#itensCompra {
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
            QPushButton {
                min-height: 38px;
                padding: 0 14px;
                color: #173c35;
                background: white;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
            }
            QPushButton#registrarCompra { color: white; background: #17634f; border: 0; }
        """)
        self._atualizar_tabela()

    @staticmethod
    def _pedir_custo(parent, titulo, texto):
        return QInputDialog.getDouble(
            parent, titulo, texto, 0.0, 0.0, 1_000_000_000, 2
        )

    def adicionar_entrada(self):
        entrada = self.produto_input.text().strip()
        self.produto_input.clear()
        if not entrada:
            return
        if entrada == "-":
            self.desfazer_ultima_leitura()
            return

        try:
            produto = _resolver_produto(entrada, self)
            if produto is None:
                return
            id_produto = produto["id"]
            item = self.itens.get(id_produto)
            if item is None:
                custo_inicial = None
                if produto["estoque"] > 0 and produto["custo_medio"] is None:
                    custo_inicial, confirmou = self._pedir_custo(
                        self,
                        "Custo atual do estoque",
                        f"Informe o custo unitário das {produto['estoque']} unidades existentes de {produto['nome']}:",
                    )
                    if not confirmou:
                        return

                custo_unitario, confirmou = self._pedir_custo(
                    self,
                    "Custo de compra",
                    f"Informe o custo unitário de {produto['nome']} nesta compra:",
                )
                if not confirmou:
                    return

                item = {"produto": produto, "quantidade": 0, "custo_unitario": custo_unitario}
                self.itens[id_produto] = item
                if custo_inicial is not None:
                    self.custos_iniciais[id_produto] = custo_inicial

            item["quantidade"] += 1
            self.adicoes.append(id_produto)
            self.status_label.setText(
                f"{produto['nome']}: {item['quantidade']} unidade(s) recebida(s)."
            )
            self._atualizar_tabela()
        except ErroPDV as erro:
            self.status_label.setText(str(erro))
        finally:
            self.produto_input.setFocus()

    def desfazer_ultima_leitura(self):
        if not self.adicoes:
            self.status_label.setText("Não há leitura para desfazer.")
            return
        id_produto = self.adicoes.pop()
        self.itens[id_produto]["quantidade"] -= 1
        if self.itens[id_produto]["quantidade"] == 0:
            del self.itens[id_produto]
            self.custos_iniciais.pop(id_produto, None)
        self.status_label.setText("Última unidade removida da compra.")
        self._atualizar_tabela()
        self.produto_input.setFocus()

    def _atualizar_tabela(self):
        itens = list(self.itens.values())
        self.itens_tabela.setRowCount(len(itens))
        for linha, item in enumerate(itens):
            self.itens_tabela.setItem(linha, 0, QTableWidgetItem(item["produto"]["nome"]))
            self.itens_tabela.setItem(linha, 1, QTableWidgetItem(str(item["quantidade"])))
            self.itens_tabela.setItem(
                linha, 2, QTableWidgetItem(dinheiro(item["custo_unitario"]))
            )
            self.itens_tabela.setItem(
                linha,
                3,
                QTableWidgetItem(dinheiro(item["quantidade"] * item["custo_unitario"])),
            )
        self.salvar_button.setEnabled(bool(itens))
        self.desfazer_button.setEnabled(bool(self.adicoes))

    def salvar_compra(self):
        if not self.itens:
            return
        try:
            id_compra = registrar_compra(
                [
                    (id_produto, item["quantidade"], item["custo_unitario"])
                    for id_produto, item in self.itens.items()
                ],
                fornecedor=self.fornecedor_input.text().strip(),
                referencia=self.referencia_input.text().strip(),
                observacao=self.observacao_input.text().strip(),
                custos_iniciais=self.custos_iniciais,
            )
        except ErroPDV as erro:
            QMessageBox.warning(self, "Compra não registrada", str(erro))
            return

        self.itens.clear()
        self.adicoes.clear()
        self.custos_iniciais.clear()
        self.fornecedor_input.clear()
        self.referencia_input.clear()
        self.observacao_input.clear()
        self.status_label.setText(f"Compra #{id_compra} registrada.")
        self._atualizar_tabela()
        self.produto_input.setFocus()


class ContagemPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contagens = {}
        self.adicoes = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        titulo = QLabel("Contagem física")
        titulo.setObjectName("tituloContagem")
        layout.addWidget(titulo)
        layout.addWidget(QLabel(
            "Leia cada unidade contada. ENTER somente finaliza o campo do leitor; use Aplicar para salvar."
        ))

        self.produto_input = QLineEdit()
        self.produto_input.setObjectName("produtoContagemInput")
        self.produto_input.setPlaceholderText("Código de barras ou nome do produto")
        self.produto_input.setMinimumHeight(40)
        self.produto_input.returnPressed.connect(self.adicionar_entrada)
        layout.addWidget(self.produto_input)

        self.contagens_tabela = QTableWidget(0, 3)
        self.contagens_tabela.setObjectName("contagensEstoque")
        self.contagens_tabela.setHorizontalHeaderLabels(
            ["Produto", "Contado", "No sistema"]
        )
        self.contagens_tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.contagens_tabela.horizontalHeader().setSectionResizeMode(
            0, self.contagens_tabela.horizontalHeader().ResizeMode.Stretch
        )
        for coluna in (1, 2):
            self.contagens_tabela.horizontalHeader().setSectionResizeMode(
                coluna,
                self.contagens_tabela.horizontalHeader().ResizeMode.ResizeToContents,
            )
        layout.addWidget(self.contagens_tabela, 1)

        acoes = QHBoxLayout()
        self.status_label = QLabel("Somente os produtos contados serão ajustados.")
        self.status_label.setObjectName("statusContagem")
        acoes.addWidget(self.status_label, 1)
        self.desfazer_button = QPushButton("Desfazer leitura")
        self.desfazer_button.clicked.connect(self.desfazer_ultima_leitura)
        acoes.addWidget(self.desfazer_button)
        self.aplicar_button = QPushButton("Aplicar contagem")
        self.aplicar_button.setObjectName("aplicarContagem")
        self.aplicar_button.clicked.connect(self.aplicar_contagem)
        acoes.addWidget(self.aplicar_button)
        layout.addLayout(acoes)

        self.setStyleSheet("""
            QLabel#tituloContagem { color: #173c35; font-size: 22px; font-weight: 700; }
            QLabel#statusContagem { color: #53655f; }
            QLineEdit {
                min-height: 40px;
                padding: 0 10px;
                color: #20352e;
                selection-background-color: #17634f;
                selection-color: #ffffff;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
            QTableWidget#contagensEstoque {
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
            QPushButton {
                min-height: 38px;
                padding: 0 14px;
                color: #173c35;
                background: white;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
            }
            QPushButton#aplicarContagem { color: white; background: #17634f; border: 0; }
        """)
        self._atualizar_tabela()

    def adicionar_entrada(self):
        entrada = self.produto_input.text().strip()
        self.produto_input.clear()
        if not entrada:
            return
        if entrada == "-":
            self.desfazer_ultima_leitura()
            return

        try:
            produto = _resolver_produto(entrada, self)
            if produto is None:
                return
            id_produto = produto["id"]
            self.contagens[id_produto] = {
                "produto": produto,
                "quantidade": self.contagens.get(id_produto, {}).get("quantidade", 0) + 1,
            }
            self.adicoes.append(id_produto)
            self.status_label.setText(
                f"{produto['nome']}: {self.contagens[id_produto]['quantidade']} unidade(s) contada(s)."
            )
            self._atualizar_tabela()
        except ErroPDV as erro:
            self.status_label.setText(str(erro))
        finally:
            self.produto_input.setFocus()

    def desfazer_ultima_leitura(self):
        if not self.adicoes:
            self.status_label.setText("Não há leitura para desfazer.")
            return
        id_produto = self.adicoes.pop()
        self.contagens[id_produto]["quantidade"] -= 1
        if self.contagens[id_produto]["quantidade"] == 0:
            del self.contagens[id_produto]
        self.status_label.setText("Última unidade removida da contagem.")
        self._atualizar_tabela()
        self.produto_input.setFocus()

    def _atualizar_tabela(self):
        itens = list(self.contagens.values())
        self.contagens_tabela.setRowCount(len(itens))
        for linha, item in enumerate(itens):
            produto = item["produto"]
            self.contagens_tabela.setItem(linha, 0, QTableWidgetItem(produto["nome"]))
            self.contagens_tabela.setItem(
                linha, 1, QTableWidgetItem(str(item["quantidade"]))
            )
            self.contagens_tabela.setItem(
                linha, 2, QTableWidgetItem(str(produto["estoque"]))
            )
        self.aplicar_button.setEnabled(bool(itens))
        self.desfazer_button.setEnabled(bool(self.adicoes))

    def aplicar_contagem(self):
        if not self.contagens:
            return

        resposta = QMessageBox.question(
            self,
            "Aplicar contagem",
            "Aplicar as diferenças de estoque dos produtos contados? Os demais não serão alterados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        try:
            resultados = ajustar_estoque_em_lote(
                {
                    id_produto: item["quantidade"]
                    for id_produto, item in self.contagens.items()
                },
                "Contagem física desktop",
            )
        except ErroPDV as erro:
            self.status_label.setText(str(erro))
            return

        self.contagens.clear()
        self.adicoes.clear()
        self._atualizar_tabela()
        self.status_label.setText(
            f"{len(resultados)} produto(s) ajustado(s); produtos não contados permaneceram inalterados."
        )


class HistoricoComprasPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        titulo = QLabel("Histórico de compras")
        titulo.setObjectName("tituloHistoricoCompras")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.fornecedor_input = QLineEdit()
        self.fornecedor_input.setPlaceholderText("Fornecedor")
        self.referencia_input = QLineEdit()
        self.referencia_input.setPlaceholderText("Referência")
        self.inicio_input = QLineEdit()
        self.inicio_input.setPlaceholderText("Data inicial (dd/mm/aaaa)")
        self.fim_input = QLineEdit()
        self.fim_input.setPlaceholderText("Data final (dd/mm/aaaa)")
        self.pesquisar_button = QPushButton("Pesquisar")
        self.pesquisar_button.clicked.connect(self.pesquisar)
        for widget in (
            self.fornecedor_input,
            self.referencia_input,
            self.inicio_input,
            self.fim_input,
            self.pesquisar_button,
        ):
            filtros.addWidget(widget)
        layout.addLayout(filtros)

        self.status_label = QLabel("Últimas compras")
        layout.addWidget(self.status_label)
        self.compras_tabela = QTableWidget(0, 7)
        self.compras_tabela.setObjectName("comprasEstoque")
        self.compras_tabela.setHorizontalHeaderLabels(
            ["Data", "Fornecedor", "Referência", "Produto", "Quantidade", "Custo/un.", "Total"]
        )
        self.compras_tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.compras_tabela.horizontalHeader().setSectionResizeMode(
            3, self.compras_tabela.horizontalHeader().ResizeMode.Stretch
        )
        for coluna in (0, 1, 2, 4, 5, 6):
            self.compras_tabela.horizontalHeader().setSectionResizeMode(
                coluna,
                self.compras_tabela.horizontalHeader().ResizeMode.ResizeToContents,
            )
        self.compras_tabela.setStyleSheet("""
            QLineEdit {
                min-height: 36px;
                padding: 0 8px;
                color: #20352e;
                selection-background-color: #17634f;
                selection-color: #ffffff;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
            QTableWidget#comprasEstoque {
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
        """)
        layout.addWidget(self.compras_tabela, 1)
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
        try:
            compras = listar_compras(
                fornecedor=self.fornecedor_input.text().strip() or None,
                referencia=self.referencia_input.text().strip() or None,
                inicio=self._ler_data(self.inicio_input.text(), "Data inicial"),
                fim=self._ler_data(self.fim_input.text(), "Data final"),
            )
        except ErroPDV as erro:
            self.status_label.setText(str(erro))
            return

        self.compras_tabela.setRowCount(len(compras))
        for linha, compra in enumerate(compras):
            valores = (
                compra["data_compra"],
                compra["fornecedor"] or "-",
                compra["referencia"] or "-",
                compra["produto"],
                str(compra["quantidade"]),
                dinheiro(compra["custo_unitario"]),
                dinheiro(compra["total_item"]),
            )
            for coluna, valor in enumerate(valores):
                self.compras_tabela.setItem(linha, coluna, QTableWidgetItem(valor))

        self.status_label.setText(f"{len(compras)} item(ns) de compra encontrado(s).")


class EstoquePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.paginas = QTabWidget()
        self.paginas.setObjectName("paginasEstoque")
        self.paginas.addTab(ProdutosEstoquePage(), "Produtos e preços")
        self.paginas.addTab(CompraPage(), "Reposição")
        self.paginas.addTab(ContagemPage(), "Contagem física")
        self.paginas.addTab(HistoricoComprasPage(), "Compras")
        layout.addWidget(self.paginas)