"""Telas de login e primeiro acesso da interface desktop."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from pdv.erros import ErroPDV
from pdv.usuarios import autenticar, criar_usuario, existe_usuario_ativo


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.usuario = None
        self.primeiro_acesso = not existe_usuario_ativo()

        self.setWindowTitle("PDV Python | Acesso")
        self.setModal(True)
        self.setFixedWidth(420)
        self.setObjectName("loginDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(18)

        titulo = QLabel("PDV Python")
        titulo.setObjectName("tituloLogin")
        subtitulo = QLabel(
            "Criar o usuário responsável" if self.primeiro_acesso else "Entrar no sistema"
        )
        subtitulo.setObjectName("subtituloLogin")
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        formulario = QFormLayout()
        formulario.setVerticalSpacing(12)
        formulario.setHorizontalSpacing(12)

        self.nome_input = None
        if self.primeiro_acesso:
            self.nome_input = QLineEdit()
            self.nome_input.setObjectName("nomeInput")
            formulario.addRow("Nome", self.nome_input)

        self.login_input = QLineEdit()
        self.login_input.setObjectName("loginInput")
        formulario.addRow("Login", self.login_input)

        self.senha_input = QLineEdit()
        self.senha_input.setObjectName("senhaInput")
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha_input.returnPressed.connect(self._confirmar)
        formulario.addRow("Senha", self.senha_input)

        self.confirmacao_input = None
        if self.primeiro_acesso:
            self.confirmacao_input = QLineEdit()
            self.confirmacao_input.setObjectName("confirmacaoSenhaInput")
            self.confirmacao_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirmacao_input.returnPressed.connect(self._confirmar)
            formulario.addRow("Confirmar senha", self.confirmacao_input)

        layout.addLayout(formulario)

        self.erro_label = QLabel()
        self.erro_label.setObjectName("erroLogin")
        self.erro_label.setWordWrap(True)
        self.erro_label.setVisible(False)
        layout.addWidget(self.erro_label)

        self.confirmar_button = QPushButton(
            "Criar usuário dono" if self.primeiro_acesso else "Entrar"
        )
        self.confirmar_button.setObjectName("confirmarLogin")
        self.confirmar_button.setDefault(True)
        self.confirmar_button.clicked.connect(self._confirmar)
        layout.addWidget(self.confirmar_button)

        self.setStyleSheet("""
            QDialog#loginDialog { background: #f4f6f5; }
            QLabel#tituloLogin { color: #173c35; font-size: 24px; font-weight: 700; }
            QLabel#subtituloLogin { color: #53655f; font-size: 14px; }
            QLineEdit {
                min-height: 34px;
                padding: 0 9px;
                border: 1px solid #bdcbc5;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus { border: 2px solid #24735d; }
            QPushButton {
                min-height: 38px;
                color: white;
                background: #17634f;
                border: 0;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover { background: #104c3d; }
            QLabel#erroLogin { color: #a12f2f; }
        """)

        primeiro_campo = self.nome_input or self.login_input
        primeiro_campo.setFocus(Qt.FocusReason.OtherFocusReason)

    def _mostrar_erro(self, mensagem):
        self.erro_label.setText(mensagem)
        self.erro_label.setVisible(True)

    def _confirmar(self):
        login = self.login_input.text()
        senha = self.senha_input.text()

        if self.primeiro_acesso:
            if senha != self.confirmacao_input.text():
                self._mostrar_erro("As senhas não conferem.")
                return

            try:
                criar_usuario(self.nome_input.text(), login, senha, "dono")
            except ErroPDV as erro:
                self._mostrar_erro(str(erro))
                return

        self.usuario = autenticar(login, senha)
        if self.usuario is None:
            self._mostrar_erro("Login ou senha inválidos.")
            return

        self.accept()