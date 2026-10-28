import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

from pdv.backup import pasta_backups
from pdv.caixa import abrir_caixa, caixa_aberto, fechar_caixa, registrar_sangria
from pdv.carrinho import Carrinho
from pdv.desktop.caixa_page import (
    CaixaPage,
    MovimentoDialog,
    ResumoCaixaDialog,
)
from pdv.desktop.janela_principal import MainWindow
from pdv.erros import ErroPDV
from pdv.vendas import finalizar_venda


def _texto(tabela, linha, coluna):
    return tabela.item(linha, coluna).text()


def _linhas(tabela):
    return [(_texto(tabela, i, 0), _texto(tabela, i, 1)) for i in range(tabela.rowCount())]


@pytest.fixture
def respostas(monkeypatch):
    """Responde os diálogos de pergunta sem abrir janela de verdade."""
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    monkeypatch.setattr(
        "pdv.desktop.caixa_page.QInputDialog.getDouble",
        lambda *args, **kwargs: (0.0, False),
    )
    capturados = []
    monkeypatch.setattr(ResumoCaixaDialog, "exec", lambda self: capturados.append(self))
    return capturados


def _informar_valor(monkeypatch, valor, confirmou=True):
    monkeypatch.setattr(
        "pdv.desktop.caixa_page.QInputDialog.getDouble",
        lambda *args, **kwargs: (valor, confirmou),
    )


# ---------------------------------------------------------------- estado da tela

def test_sem_caixa_aberto_so_permite_abrir(qtbot):
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    assert pagina.status_label.text() == "Nenhum caixa aberto."
    assert pagina.abrir_button.isEnabled()
    assert not pagina.sangria_button.isEnabled()
    assert not pagina.suprimento_button.isEnabled()
    assert not pagina.fechar_button.isEnabled()
    assert pagina.resumo_widget.isHidden()


def test_com_caixa_aberto_libera_as_outras_acoes(qtbot, caixa):
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    assert pagina.status_label.text() == f"Caixa #{caixa} aberto."
    assert not pagina.abrir_button.isEnabled()
    assert pagina.sangria_button.isEnabled()
    assert pagina.suprimento_button.isEnabled()
    assert pagina.fechar_button.isEnabled()
    assert not pagina.resumo_widget.isHidden()


def test_resumo_mostra_vendas_por_forma_e_conta_da_gaveta(qtbot, caixa, coca):
    carrinho = Carrinho()
    carrinho.adicionar(coca, 2)
    finalizar_venda(carrinho, "Dinheiro")
    carrinho.adicionar(coca, 1)
    finalizar_venda(carrinho, "PIX")
    registrar_sangria(10, "banco")

    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    resumo = pagina.resumo_widget
    assert _linhas(resumo.vendas_tabela) == [
        ("Dinheiro", "R$ 25,00"),
        ("PIX", "R$ 12,50"),
        ("Total (2 vendas)", "R$ 37,50"),
    ]
    assert _linhas(resumo.gaveta_tabela) == [
        ("Valor inicial", "R$ 100,00"),
        ("+ Vendas em dinheiro", "R$ 25,00"),
        ("+ Suprimentos", "R$ 0,00"),
        ("- Sangrias", "R$ 10,00"),
        ("= Esperado", "R$ 115,00"),
    ]


def test_resumo_sem_vendas(qtbot, caixa):
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    assert _linhas(pagina.resumo_widget.vendas_tabela) == [
        ("Nenhuma venda", ""),
        ("Total (0 vendas)", "R$ 0,00"),
    ]


# ---------------------------------------------------------------- abrir

def test_abrir_caixa_pelo_botao(qtbot, monkeypatch):
    _informar_valor(monkeypatch, 50.0)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.abrir()

    aberto = caixa_aberto()
    assert aberto["valor_inicial"] == 50
    assert pagina.status_label.text() == f"Caixa #{aberto['id']} aberto."
    assert "aberto com R$ 50,00" in pagina.mensagem_label.text()
    assert not pagina.abrir_button.isEnabled()
    assert pagina.fechar_button.isEnabled()


def test_cancelar_a_abertura_nao_abre_caixa(qtbot, monkeypatch):
    _informar_valor(monkeypatch, 50.0, confirmou=False)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.abrir()

    assert caixa_aberto() is None
    assert pagina.status_label.text() == "Nenhum caixa aberto."


# ---------------------------------------------------------------- sangria e suprimento

def test_dialogo_de_sangria_registra_valor_e_motivo(qtbot, caixa):
    dialogo = MovimentoDialog("Sangria", registrar_sangria, 100)
    qtbot.addWidget(dialogo)
    dialogo.valor_input.setValue(30)
    dialogo.motivo_input.setText("levar ao banco")

    qtbot.mouseClick(dialogo.confirmar_button, Qt.MouseButton.LeftButton)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    assert dialogo.resumo.sangrias == 30
    assert dialogo.resumo.dinheiro_esperado == 70


@pytest.mark.parametrize(
    "valor, motivo, mensagem",
    [
        (0, "banco", "maior que zero"),
        (10, "   ", "Informe o motivo"),
        (500, "banco", "maior que o dinheiro na gaveta"),
    ],
)
def test_dialogo_mostra_o_erro_e_continua_aberto(qtbot, caixa, valor, motivo, mensagem):
    dialogo = MovimentoDialog("Sangria", registrar_sangria, 100)
    qtbot.addWidget(dialogo)
    dialogo.valor_input.setValue(valor)
    dialogo.motivo_input.setText(motivo)

    qtbot.mouseClick(dialogo.confirmar_button, Qt.MouseButton.LeftButton)

    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert mensagem in dialogo.erro_label.text()
    assert dialogo.resumo is None


def test_sangria_pela_pagina_atualiza_a_gaveta(qtbot, caixa, monkeypatch):
    def preencher_e_confirmar(self):
        self.valor_input.setValue(30)
        self.motivo_input.setText("banco")
        self.accept()
        return self.result()

    monkeypatch.setattr(MovimentoDialog, "exec", preencher_e_confirmar)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.sangria()

    assert "Dinheiro na gaveta: R$ 70,00" in pagina.mensagem_label.text()
    assert ("= Esperado", "R$ 70,00") in _linhas(pagina.resumo_widget.gaveta_tabela)


def test_suprimento_pela_pagina_soma_na_gaveta(qtbot, caixa, monkeypatch):
    def preencher_e_confirmar(self):
        self.valor_input.setValue(50)
        self.motivo_input.setText("reforço de troco")
        self.accept()
        return self.result()

    monkeypatch.setattr(MovimentoDialog, "exec", preencher_e_confirmar)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.suprimento()

    assert ("= Esperado", "R$ 150,00") in _linhas(pagina.resumo_widget.gaveta_tabela)


def test_cancelar_o_dialogo_nao_registra_nada(qtbot, caixa, monkeypatch):
    monkeypatch.setattr(MovimentoDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.sangria()

    assert pagina.mensagem_label.text() == ""
    assert ("= Esperado", "R$ 100,00") in _linhas(pagina.resumo_widget.gaveta_tabela)


# ---------------------------------------------------------------- fechar

def test_fechar_caixa_com_conferencia_e_backup(qtbot, caixa, monkeypatch, respostas):
    _informar_valor(monkeypatch, 100.0)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.fechar()

    assert caixa_aberto() is None
    assert pagina.status_label.text() == "Nenhum caixa aberto."
    assert "Backup automático criado" in pagina.mensagem_label.text()
    assert len(list(pasta_backups().glob("loja_*.db"))) == 1

    # o histórico passa a mostrar o caixa fechado, com esperado, contado e diferença
    assert [_texto(pagina.historico_tabela, 0, coluna) for coluna in (0, 5, 6, 7)] == [
        "#1", "R$ 100,00", "R$ 100,00", "R$ 0,00",
    ]


@pytest.mark.parametrize(
    "contado, situacao",
    [(90.0, "R$ -10,00 (FALTA)"), (105.5, "R$ 5,50 (SOBRA)"), (100.0, "R$ 0,00 (OK)")],
)
def test_resumo_do_fechamento_mostra_sobra_ou_falta(
    qtbot, caixa, monkeypatch, respostas, contado, situacao
):
    _informar_valor(monkeypatch, contado)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.fechar()

    (dialogo,) = respostas
    linhas = _linhas(dialogo.resumo_widget.gaveta_tabela)
    assert ("Diferença", situacao) in linhas


def test_nao_fecha_se_o_operador_desistir_da_pergunta(qtbot, caixa, monkeypatch, respostas):
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.No
    )
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.fechar()

    assert caixa_aberto() is not None


def test_nao_fecha_se_o_operador_cancelar_a_contagem(qtbot, caixa, monkeypatch, respostas):
    _informar_valor(monkeypatch, 100.0, confirmou=False)
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.fechar()

    assert caixa_aberto() is not None


def test_nao_fecha_com_itens_no_carrinho(qtbot, caixa, monkeypatch, respostas):
    _informar_valor(monkeypatch, 100.0)
    pagina = CaixaPage(carrinho_vazio=lambda: False)
    qtbot.addWidget(pagina)

    pagina.fechar()

    assert caixa_aberto() is not None
    assert "itens no carrinho" in pagina.mensagem_label.text()


def test_falha_no_backup_nao_desfaz_o_fechamento(qtbot, caixa, monkeypatch, respostas):
    _informar_valor(monkeypatch, 100.0)
    avisos = []

    def disco_cheio():
        raise ErroPDV("Não foi possível fazer o backup: disco cheio")

    monkeypatch.setattr("pdv.desktop.caixa_page.fazer_backup", disco_cheio)
    monkeypatch.setattr(
        QMessageBox, "warning", lambda parent, titulo, texto: avisos.append(texto)
    )
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.fechar()

    assert caixa_aberto() is None
    assert len(avisos) == 1
    assert "disco cheio" in avisos[0]


# ---------------------------------------------------------------- histórico

def test_historico_lista_do_mais_recente_e_abre_o_resumo(qtbot, monkeypatch, respostas):
    primeiro = abrir_caixa(10)
    fechar_caixa(10)
    segundo = abrir_caixa(20)

    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    assert [_texto(pagina.historico_tabela, i, 0) for i in range(2)] == [
        f"#{segundo}", f"#{primeiro}",
    ]
    assert _texto(pagina.historico_tabela, 0, 2) == "ABERTO"
    assert _texto(pagina.historico_tabela, 0, 5) == "-"

    pagina.historico_tabela.selectRow(1)
    pagina.ver_resumo_selecionado()

    (dialogo,) = respostas
    assert dialogo.windowTitle() == f"Resumo do caixa #{primeiro}"
    assert ("Valor inicial", "R$ 10,00") in _linhas(dialogo.resumo_widget.gaveta_tabela)


def test_ver_resumo_sem_selecionar_avisa(qtbot, caixa, respostas):
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    pagina.ver_resumo_selecionado()

    assert respostas == []
    assert "Selecione um caixa" in pagina.mensagem_label.text()


def test_historico_vazio(qtbot):
    pagina = CaixaPage()
    qtbot.addWidget(pagina)

    assert pagina.historico_tabela.rowCount() == 0
    assert not pagina.ver_resumo_button.isEnabled()


# ---------------------------------------------------------------- janela principal

def test_janela_tem_aba_caixa_para_dona_e_operador(qtbot):
    dona = MainWindow({"id": 1, "nome": "Dona", "perfil": "dono"})
    operador = MainWindow({"id": 2, "nome": "Func", "perfil": "operador"})
    qtbot.addWidget(dona)
    qtbot.addWidget(operador)

    assert [dona.paginas.tabText(i) for i in range(dona.paginas.count())] == [
        "Venda", "Caixa", "Comprovantes", "Estoque",
    ]
    assert [operador.paginas.tabText(i) for i in range(operador.paginas.count())] == [
        "Venda", "Caixa", "Comprovantes",
    ]


def test_aba_caixa_recarrega_ao_ser_aberta(qtbot):
    janela = MainWindow({"id": 1, "nome": "Dona", "perfil": "dono"})
    qtbot.addWidget(janela)
    assert janela.caixa_page.status_label.text() == "Nenhum caixa aberto."

    id_caixa = abrir_caixa(10)  # mudança feita fora da aba (ex.: pelo terminal)
    janela.paginas.setCurrentIndex(1)

    assert janela.caixa_page.status_label.text() == f"Caixa #{id_caixa} aberto."


def test_janela_nao_deixa_fechar_caixa_com_carrinho_cheio(qtbot, caixa, coca):
    janela = MainWindow({"id": 1, "nome": "Dona", "perfil": "dono"})
    qtbot.addWidget(janela)
    janela.venda_page.carrinho.adicionar(coca, 1)

    janela.caixa_page.fechar()

    assert caixa_aberto() is not None
    assert "itens no carrinho" in janela.caixa_page.mensagem_label.text()