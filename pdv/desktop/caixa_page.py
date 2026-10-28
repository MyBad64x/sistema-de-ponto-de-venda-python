"""Caixa da interface desktop: abertura, sangria, suprimento, fechamento e histórico."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pdv.backup import fazer_backup
from pdv.caixa import (
    abrir_caixa,
    caixa_aberto,
    detalhar_caixa,
    fechar_caixa,
    listar_caixas,
    registrar_sangria,
    registrar_suprimento,
    resumo_caixa_aberto,
)
from pdv.erros import ErroPDV
from pdv.terminal.utilitarios import dinheiro

CAIXAS_NO_HISTORICO = 20
VALOR_MAXIMO = 1_000_000_000


def _dinheiro_ou_traco(valor):
    return "-" if valor is None else dinheiro(valor)


def _situacao(diferenca):
    if diferenca > 0:
        return "SOBRA"
    if diferenca < 0:
        return "FALTA"
    return "OK"


def _criar_tabela(cabecalhos, coluna_esticada=0):
    """Tabela somente de leitura; só uma coluna estica, as outras se ajustam ao conteúdo."""
    tabela = QTableWidget(0, len(cabecalhos))
    tabela.setHorizontalHeaderLabels(cabecalhos)
    tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    tabela.verticalHeader().setVisible(False)

    cabecalho = tabela.horizontalHeader()
    for coluna in range(len(cabecalhos)):
        modo = (
            cabecalho.ResizeMode.Stretch
            if coluna == coluna_esticada
            else cabecalho.ResizeMode.ResizeToContents
        )
        cabecalho.setSectionResizeMode(coluna, modo)
        alinhamento = Qt.AlignmentFlag.AlignVCenter | (
            Qt.AlignmentFlag.AlignLeft if coluna == 0 else Qt.AlignmentFlag.AlignRight
        )
        tabela.horizontalHeaderItem(coluna).setTextAlignment(alinhamento)
    return tabela


def _preencher(tabela, linhas):
    tabela.setRowCount(len(linhas))
    for numero, linha in enumerate(linhas):
        for coluna, texto in enumerate(linha):
            celula = QTableWidgetItem(texto)
            if coluna > 0:
                celula.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
            tabela.setItem(numero, coluna, celula)


def _ajustar_altura(tabela):
    """Faz a tabela ter exatamente a altura das suas linhas, sem barra de rolagem."""
    altura = tabela.horizontalHeader().sizeHint().height() + 4
    altura += sum(tabela.rowHeight(linha) for linha in range(tabela.rowCount()))
    tabela.setFixedHeight(altura)


class ResumoCaixaWidget(QWidget):
    """Vendas por forma de pagamento e conta do dinheiro na gaveta."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.cabecalho_label = QLabel()
        self.cabecalho_label.setObjectName("cabecalhoResumo")
        layout.addWidget(self.cabecalho_label)

        self.vendas_tabela = _criar_tabela(["Vendas", "Total"])
        self.vendas_tabela.setObjectName("vendasDoCaixa")
        self.gaveta_tabela = _criar_tabela(["Dinheiro na gaveta", "Valor"])
        self.gaveta_tabela.setObjectName("gavetaDoCaixa")

        # lado a lado: a janela é larga e baixa, e o "= Esperado" precisa ficar à vista
        tabelas = QHBoxLayout()
        tabelas.setSpacing(14)
        tabelas.addWidget(self.vendas_tabela, 0, Qt.AlignmentFlag.AlignTop)
        tabelas.addWidget(self.gaveta_tabela, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(tabelas)

    def mostrar(self, resumo):
        self.cabecalho_label.setText(
            f"Caixa #{resumo.id_caixa} - aberto em {resumo.data_abertura}"
        )

        vendas = [(forma, dinheiro(total)) for forma, total in resumo.vendas_por_forma.items()]
        if not vendas:
            vendas = [("Nenhuma venda", "")]
        vendas.append((f"Total ({resumo.quantidade_vendas} vendas)", dinheiro(resumo.total_vendas)))
        _preencher(self.vendas_tabela, vendas)

        gaveta = [
            ("Valor inicial", dinheiro(resumo.valor_inicial)),
            ("+ Vendas em dinheiro", dinheiro(resumo.vendas_dinheiro)),
            ("+ Suprimentos", dinheiro(resumo.suprimentos)),
            ("- Sangrias", dinheiro(resumo.sangrias)),
            ("= Esperado", dinheiro(resumo.dinheiro_esperado)),
        ]
        if resumo.valor_contado is not None:
            diferenca = f"{dinheiro(resumo.diferenca)} ({_situacao(resumo.diferenca)})"
            gaveta.append(("Contado", dinheiro(resumo.valor_contado)))
            gaveta.append(("Diferença", diferenca))
        _preencher(self.gaveta_tabela, gaveta)

        _ajustar_altura(self.vendas_tabela)
        _ajustar_altura(self.gaveta_tabela)


class ResumoCaixaDialog(QDialog):
    def __init__(self, resumo, titulo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(780, 380)

        layout = QVBoxLayout(self)
        self.resumo_widget = ResumoCaixaWidget()
        self.resumo_widget.mostrar(resumo)
        layout.addWidget(self.resumo_widget)
        layout.addStretch(1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)


class MovimentoDialog(QDialog):
    """Sangria ou suprimento: pede valor e motivo e chama a regra de negócio."""

    def __init__(self, titulo, registrar, dinheiro_na_gaveta, parent=None):
        super().__init__(parent)
        self.registrar = registrar
        self.resumo = None
        self.setWindowTitle(titulo)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Dinheiro na gaveta agora: {dinheiro(dinheiro_na_gaveta)}"))

        formulario = QFormLayout()
        self.valor_input = QDoubleSpinBox()
        self.valor_input.setObjectName("valorMovimento")
        self.valor_input.setDecimals(2)
        self.valor_input.setRange(0, VALOR_MAXIMO)
        self.valor_input.setPrefix("R$ ")
        self.motivo_input = QLineEdit()
        self.motivo_input.setObjectName("motivoMovimento")
        self.motivo_input.setPlaceholderText("Ex.: levar ao banco, reforço de troco")
        formulario.addRow("Valor:", self.valor_input)
        formulario.addRow("Motivo:", self.motivo_input)
        layout.addLayout(formulario)

        self.erro_label = QLabel()
        self.erro_label.setStyleSheet("color: #a12f2f;")
        layout.addWidget(self.erro_label)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.confirmar_button = botoes.button(QDialogButtonBox.StandardButton.Ok)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def accept(self):
        try:
            self.resumo = self.registrar(self.valor_input.value(), self.motivo_input.text())
        except ErroPDV as erro:
            # o diálogo continua aberto para o operador corrigir
            self.erro_label.setText(str(erro))
            return
        super().accept()


class CaixaPage(QWidget):
    def __init__(self, carrinho_vazio=None, parent=None):
        super().__init__(parent)
        # função que diz se o carrinho da aba Venda está vazio (None = não confere)
        self._carrinho_vazio = carrinho_vazio

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        titulo = QLabel("Caixa")
        titulo.setObjectName("tituloCaixa")
        layout.addWidget(titulo)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusCaixa")
        layout.addWidget(self.status_label)

        acoes = QHBoxLayout()
        self.abrir_button = QPushButton("Abrir caixa")
        self.sangria_button = QPushButton("Sangria")
        self.suprimento_button = QPushButton("Suprimento")
        self.fechar_button = QPushButton("Fechar caixa")
        self.abrir_button.clicked.connect(self.abrir)
        self.sangria_button.clicked.connect(self.sangria)
        self.suprimento_button.clicked.connect(self.suprimento)
        self.fechar_button.clicked.connect(self.fechar)
        for botao in (
            self.abrir_button,
            self.sangria_button,
            self.suprimento_button,
            self.fechar_button,
        ):
            acoes.addWidget(botao)
        acoes.addStretch(1)
        layout.addLayout(acoes)

        self.mensagem_label = QLabel()
        self.mensagem_label.setObjectName("mensagemCaixa")
        layout.addWidget(self.mensagem_label)

        # duas seções, para o resumo e o histórico não disputarem espaço na janela
        self.secoes = QTabWidget()
        self.secoes.setObjectName("secoesCaixa")

        caixa_atual = QWidget()
        caixa_atual_layout = QVBoxLayout(caixa_atual)
        caixa_atual_layout.setContentsMargins(0, 12, 0, 0)
        self.sem_caixa_label = QLabel("Abra o caixa para ver o resumo.")
        self.sem_caixa_label.setObjectName("semCaixa")
        self.resumo_widget = ResumoCaixaWidget()
        caixa_atual_layout.addWidget(self.sem_caixa_label)
        caixa_atual_layout.addWidget(self.resumo_widget)
        caixa_atual_layout.addStretch(1)
        self.secoes.addTab(caixa_atual, "Caixa atual")

        historico = QWidget()
        historico_layout = QVBoxLayout(historico)
        historico_layout.setContentsMargins(0, 12, 0, 0)
        self.historico_tabela = _criar_tabela(
            ["Caixa", "Abertura", "Fechamento", "Vendas", "Total vendas", "Esperado", "Contado", "Diferença"],
            coluna_esticada=1,
        )
        self.historico_tabela.setObjectName("historicoCaixas")
        self.historico_tabela.cellDoubleClicked.connect(lambda *_: self.ver_resumo_selecionado())
        self.ver_resumo_button = QPushButton("Ver resumo do caixa")
        self.ver_resumo_button.clicked.connect(self.ver_resumo_selecionado)
        historico_layout.addWidget(self.historico_tabela, 1)
        rodape = QHBoxLayout()
        rodape.addWidget(self.ver_resumo_button)
        rodape.addStretch(1)
        historico_layout.addLayout(rodape)
        self.secoes.addTab(historico, "Histórico")

        layout.addWidget(self.secoes, 1)

        self.setStyleSheet("""
            QLabel#tituloCaixa { color: #173c35; font-size: 24px; font-weight: 700; }
            QLabel#semCaixa { color: #53655f; }
            QLabel#statusCaixa { color: #173c35; font-size: 16px; font-weight: 600; }
            QLabel#cabecalhoResumo { color: #53655f; }
            QTableWidget {
                color: #20352e;
                background: white;
                alternate-background-color: #f0f4f1;
                border: 1px solid #d5dfda;
                gridline-color: #e1e8e4;
            }
            QTabWidget#secoesCaixa::pane { border: 0; }
            QPushButton {
                min-height: 38px;
                padding: 0 14px;
                color: #173c35;
                background: white;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
            }
            QPushButton:hover { background: #e8efeb; }
            QPushButton:disabled { color: #8a9992; background: #eef2f0; }
        """)
        self.atualizar()

    # ------------------------------------------------------------ tela

    def ao_exibir(self):
        """Chamada pela janela quando a aba Caixa é aberta: outras abas mudam os números."""
        self.atualizar()

    def atualizar(self):
        aberto = caixa_aberto()

        if aberto is None:
            self.status_label.setText("Nenhum caixa aberto.")
            self.resumo_widget.setVisible(False)
            self.sem_caixa_label.setVisible(True)
        else:
            self.status_label.setText(f"Caixa #{aberto['id']} aberto.")
            self.resumo_widget.mostrar(resumo_caixa_aberto())
            self.resumo_widget.setVisible(True)
            self.sem_caixa_label.setVisible(False)

        self.abrir_button.setEnabled(aberto is None)
        self.sangria_button.setEnabled(aberto is not None)
        self.suprimento_button.setEnabled(aberto is not None)
        self.fechar_button.setEnabled(aberto is not None)

        self._carregar_historico()

    def _carregar_historico(self):
        caixas = listar_caixas(limite=CAIXAS_NO_HISTORICO)
        linhas = [
            (
                f"#{caixa['id']}",
                caixa["abertura"],
                caixa["fechamento"] or "ABERTO",
                str(caixa["quantidade_vendas"]),
                dinheiro(caixa["total_vendas"]),
                _dinheiro_ou_traco(caixa["esperado"]),
                _dinheiro_ou_traco(caixa["contado"]),
                _dinheiro_ou_traco(caixa["diferenca"]),
            )
            for caixa in caixas
        ]
        _preencher(self.historico_tabela, linhas)
        for numero, caixa in enumerate(caixas):
            self.historico_tabela.item(numero, 0).setData(Qt.ItemDataRole.UserRole, caixa["id"])
        self.ver_resumo_button.setEnabled(bool(caixas))

    def _mostrar_erro(self, mensagem):
        self.mensagem_label.setStyleSheet("color: #a12f2f;")
        self.mensagem_label.setText(mensagem)

    def _mostrar_aviso(self, mensagem):
        self.mensagem_label.setStyleSheet("color: #17634f;")
        self.mensagem_label.setText(mensagem)

    # ------------------------------------------------------------ ações

    def abrir(self):
        valor, confirmou = QInputDialog.getDouble(
            self, "Abrir caixa", "Valor inicial na gaveta:", 0, 0, VALOR_MAXIMO, 2
        )
        if not confirmou:
            return

        try:
            id_caixa = abrir_caixa(valor)
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            return

        self._mostrar_aviso(f"Caixa #{id_caixa} aberto com {dinheiro(valor)}.")
        self.atualizar()

    def sangria(self):
        self._movimentar("Sangria (retirada de dinheiro)", registrar_sangria)

    def suprimento(self):
        self._movimentar("Suprimento (entrada de dinheiro)", registrar_suprimento)

    def _movimentar(self, titulo, registrar):
        try:
            gaveta = resumo_caixa_aberto().dinheiro_esperado
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            self.atualizar()
            return

        dialogo = MovimentoDialog(titulo, registrar, gaveta, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        self._mostrar_aviso(
            f"Registrado. Dinheiro na gaveta: {dinheiro(dialogo.resumo.dinheiro_esperado)}."
        )
        self.atualizar()

    def fechar(self):
        if self._carrinho_vazio is not None and not self._carrinho_vazio():
            self._mostrar_erro(
                "Há itens no carrinho. Finalize a venda ou limpe o carrinho antes."
            )
            return

        try:
            resumo_caixa_aberto()  # dá erro aqui mesmo se não houver caixa aberto
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            self.atualizar()
            return

        resposta = QMessageBox.question(
            self,
            "Fechar caixa",
            "Fechar o caixa?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        # conferência "às cegas": o operador conta antes de ver quanto era esperado
        valor_contado, confirmou = QInputDialog.getDouble(
            self,
            "Conferência do caixa",
            "Conte todo o dinheiro da gaveta (cédulas e moedas).\nValor contado:",
            0,
            0,
            VALOR_MAXIMO,
            2,
        )
        if not confirmou:
            return

        try:
            resumo = fechar_caixa(valor_contado)
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            return

        self._mostrar_aviso(f"Caixa #{resumo.id_caixa} fechado.")
        self.atualizar()
        ResumoCaixaDialog(resumo, "Fechamento de caixa", self).exec()

        # o caixa já está fechado; se o backup falhar, só avisa
        try:
            caminho = fazer_backup()
        except ErroPDV as erro:
            QMessageBox.warning(
                self,
                "Backup",
                f"{erro}\n\nFaça um backup manual pelo menu de terminal (Backup > Fazer backup agora).",
            )
        else:
            self._mostrar_aviso(
                f"Caixa #{resumo.id_caixa} fechado. Backup automático criado: {caminho.name}"
            )

    def ver_resumo_selecionado(self):
        linha = self.historico_tabela.currentRow()
        if linha < 0:
            self._mostrar_erro("Selecione um caixa do histórico.")
            return

        id_caixa = self.historico_tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        try:
            resumo = detalhar_caixa(id_caixa)
        except ErroPDV as erro:
            self._mostrar_erro(str(erro))
            return

        ResumoCaixaDialog(resumo, f"Resumo do caixa #{id_caixa}", self).exec()