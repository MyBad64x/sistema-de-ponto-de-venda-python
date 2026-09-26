import pytest

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
from pdv.vendas import finalizar_venda


def test_abrir_caixa():
    assert caixa_aberto() is None
    id_caixa = abrir_caixa(100)
    assert caixa_aberto()["id"] == id_caixa


def test_nao_abre_dois_caixas(caixa):
    with pytest.raises(ErroPDV, match="Já existe"):
        abrir_caixa(50)


def test_valor_inicial_negativo():
    with pytest.raises(ErroPDV):
        abrir_caixa(-1)


def test_fechar_sem_caixa_aberto():
    with pytest.raises(ErroPDV, match="Nenhum caixa"):
        fechar_caixa(0)


def test_status_sem_caixa_aberto():
    with pytest.raises(ErroPDV, match="Nenhum caixa"):
        resumo_caixa_aberto()


def test_fechar_caixa_sem_vendas(caixa):
    resumo = fechar_caixa(100)

    assert resumo.total_vendas == 0
    assert resumo.dinheiro_esperado == 100
    assert resumo.diferenca == 0
    assert caixa_aberto() is None


def test_fechamento_conta_so_as_vendas_do_proprio_caixa(carrinho, coca):
    abrir_caixa(100)
    carrinho.adicionar(coca, 1)
    finalizar_venda(carrinho, "Dinheiro")
    fechar_caixa(112.50)

    abrir_caixa(50)
    carrinho.adicionar(coca, 2)
    finalizar_venda(carrinho, "PIX")

    resumo = resumo_caixa_aberto()
    assert resumo.quantidade_vendas == 1
    assert resumo.total_vendas == 25.0


# ---------------------------------------------------------------- gaveta

def test_so_vendas_em_dinheiro_entram_na_gaveta(caixa, carrinho, coca, bala):
    carrinho.adicionar(coca, 2)  # 25,00 no PIX
    finalizar_venda(carrinho, "PIX")
    carrinho.adicionar(bala, 10)  # 1,00 em dinheiro
    finalizar_venda(carrinho, "Dinheiro")

    resumo = resumo_caixa_aberto()

    assert resumo.vendas_por_forma == {"PIX": 25.0, "Dinheiro": 1.0}
    assert resumo.total_vendas == 26.0
    assert resumo.dinheiro_esperado == 101.0  # 100 inicial + 1 em dinheiro


def test_sangria_e_suprimento_mexem_no_dinheiro_esperado(caixa):
    registrar_suprimento(50, "Reforço de troco")
    resumo = registrar_sangria(30, "Depósito no banco")

    assert resumo.suprimentos == 50
    assert resumo.sangrias == 30
    assert resumo.dinheiro_esperado == 120  # 100 + 50 - 30


def test_varias_sangrias_somam(caixa):
    registrar_sangria(10, "A")
    resumo = registrar_sangria(15.5, "B")
    assert resumo.sangrias == 25.5


def test_sangria_maior_que_a_gaveta(caixa):
    with pytest.raises(ErroPDV, match="maior que o dinheiro"):
        registrar_sangria(100.01, "Depósito")

    # pode tirar exatamente o que tem
    assert registrar_sangria(100, "Depósito").dinheiro_esperado == 0


@pytest.mark.parametrize("valor", [0, -5])
def test_valor_zero_ou_negativo(caixa, valor):
    with pytest.raises(ErroPDV, match="maior que zero"):
        registrar_suprimento(valor, "X")
    with pytest.raises(ErroPDV, match="maior que zero"):
        registrar_sangria(valor, "X")


def test_motivo_obrigatorio(caixa):
    with pytest.raises(ErroPDV, match="motivo"):
        registrar_sangria(10, "   ")


def test_sangria_sem_caixa_aberto():
    with pytest.raises(ErroPDV, match="Nenhum caixa"):
        registrar_sangria(10, "X")


def test_movimentos_de_um_caixa_nao_passam_para_o_proximo(caixa):
    registrar_suprimento(50, "Troco")
    fechar_caixa(150)

    abrir_caixa(80)
    resumo = resumo_caixa_aberto()
    assert (resumo.suprimentos, resumo.sangrias) == (0, 0)
    assert resumo.dinheiro_esperado == 80


# ---------------------------------------------------------------- conferência

@pytest.mark.parametrize("contado, diferenca", [
    (120, 0),     # bateu
    (118, -2),    # faltou
    (125.5, 5.5), # sobrou
])
def test_conferencia_no_fechamento(caixa, contado, diferenca):
    registrar_suprimento(50, "Troco")
    registrar_sangria(30, "Banco")

    resumo = fechar_caixa(contado)

    assert resumo.dinheiro_esperado == 120
    assert resumo.valor_contado == contado
    assert resumo.diferenca == diferenca


def test_valor_contado_negativo(caixa):
    with pytest.raises(ErroPDV):
        fechar_caixa(-1)
    assert caixa_aberto() is not None


# ---------------------------------------------------------------- histórico

def test_historico_vazio():
    assert listar_caixas() == []


def test_historico_do_mais_recente_para_o_mais_antigo(carrinho, coca):
    abrir_caixa(100)
    carrinho.adicionar(coca, 2)
    finalizar_venda(carrinho, "Dinheiro")  # 25,00
    fechar_caixa(123)  # esperado 125 -> falta 2

    abrir_caixa(50)  # sem vendas, continua aberto

    recente, antigo = listar_caixas()

    assert recente["status"] == "ABERTO"
    assert recente["quantidade_vendas"] == 0  # LEFT JOIN: caixa sem vendas aparece
    assert recente["total_vendas"] == 0
    assert recente["fechamento"] is None
    assert recente["contado"] is None
    assert recente["diferenca"] is None

    assert antigo["status"] == "FECHADO"
    assert antigo["quantidade_vendas"] == 1
    assert antigo["total_vendas"] == 25
    assert antigo["esperado"] == 125
    assert antigo["contado"] == 123
    assert antigo["diferenca"] == -2


def test_historico_formata_datas_no_padrao_brasileiro(caixa):
    fechar_caixa(100)
    (linha,) = listar_caixas()

    # ex.: 26/09/2026 09:57
    assert len(linha["abertura"]) == 16
    assert linha["abertura"][2] == "/" and linha["abertura"][5] == "/"


def test_historico_com_limite():
    for valor in (10, 20, 30):
        abrir_caixa(valor)
        fechar_caixa(valor)

    assert [linha["esperado"] for linha in listar_caixas(limite=2)] == [30, 20]


def test_detalhar_caixa_fechado_bate_com_o_fechamento(caixa, carrinho, coca):
    carrinho.adicionar(coca, 1)
    finalizar_venda(carrinho, "PIX")
    registrar_sangria(40, "Banco")
    fechamento = fechar_caixa(58)

    detalhe = detalhar_caixa(caixa)

    assert detalhe == fechamento
    assert detalhe.dinheiro_esperado == 60
    assert detalhe.diferenca == -2


def test_detalhar_caixa_aberto(caixa):
    detalhe = detalhar_caixa(caixa)
    assert detalhe.valor_contado is None
    assert detalhe.diferenca is None


def test_detalhar_caixa_inexistente():
    with pytest.raises(ErroPDV, match="não encontrado"):
        detalhar_caixa(999)
