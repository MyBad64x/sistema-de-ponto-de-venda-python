from datetime import date

import pytest

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.produtos import editar_produto
from pdv.relatorios import (
    Periodo,
    periodo_hoje,
    periodo_mes_atual,
    periodo_ultimos_dias,
    produtos_mais_vendidos,
    resumo_vendas,
    vendas_por_dia,
)
from pdv.vendas import finalizar_venda

SETEMBRO = Periodo(date(2026, 9, 1), date(2026, 9, 30))


def _vender(carrinho, itens, forma_pagamento, dia):
    """Faz uma venda e muda a data dela para o dia pedido.

    O horário 15:00 UTC (12:00 em Brasília) cai no mesmo dia em qualquer fuso
    do Brasil, então o teste não depende do fuso do computador.
    """
    for id_produto, quantidade in itens:
        carrinho.adicionar(id_produto, quantidade)

    resultado = finalizar_venda(carrinho, forma_pagamento, permitir_estoque_negativo=True)

    with conexao() as conn:
        conn.execute(
            "UPDATE vendas SET data = ? WHERE id = ?",
            (f"{dia} 15:00:00", resultado.id_venda),
        )

    return resultado


# ---------------------------------------------------------------- períodos

def test_periodo_invertido():
    with pytest.raises(ErroPDV, match="data inicial"):
        Periodo(date(2026, 9, 10), date(2026, 9, 1))


def test_periodos_prontos():
    hoje = date(2026, 9, 26)

    assert periodo_hoje(hoje) == Periodo(hoje, hoje)
    assert periodo_ultimos_dias(7, hoje) == Periodo(date(2026, 9, 20), hoje)
    assert periodo_mes_atual(hoje) == Periodo(date(2026, 9, 1), hoje)


def test_parametros_no_formato_do_sqlite():
    assert SETEMBRO.parametros == ("2026-09-01", "2026-09-30")


# ---------------------------------------------------------------- resumo

def test_resumo_sem_vendas():
    resumo = resumo_vendas(SETEMBRO)

    assert resumo.quantidade_vendas == 0
    assert resumo.total == 0
    assert resumo.ticket_medio == 0  # sem divisão por zero


def test_resumo_por_forma_de_pagamento(caixa, carrinho, coca, bala):
    _vender(carrinho, [(coca, 2)], "PIX", "2026-09-10")          # 25,00
    _vender(carrinho, [(coca, 1)], "Dinheiro", "2026-09-11")     # 12,50
    _vender(carrinho, [(bala, 5)], "Dinheiro", "2026-09-12")     # 0,50
    _vender(carrinho, [(coca, 4)], "PIX", "2026-10-01")          # fora do período

    resumo = resumo_vendas(SETEMBRO)

    assert resumo.quantidade_vendas == 3
    assert resumo.total == 38.0
    assert resumo.ticket_medio == 12.67
    # maior total primeiro
    assert [(l["forma_pagamento"], l["quantidade"], l["total"]) for l in resumo.por_forma] == [
        ("PIX", 1, 25.0),
        ("Dinheiro", 2, 13.0),
    ]


def test_periodo_inclui_o_primeiro_e_o_ultimo_dia(caixa, carrinho, coca):
    _vender(carrinho, [(coca, 1)], "PIX", "2026-09-01")
    _vender(carrinho, [(coca, 1)], "PIX", "2026-09-30")
    _vender(carrinho, [(coca, 1)], "PIX", "2026-08-31")

    assert resumo_vendas(SETEMBRO).quantidade_vendas == 2


# ---------------------------------------------------------------- produtos

def test_produtos_mais_vendidos(caixa, carrinho, coca, bala):
    _vender(carrinho, [(coca, 2), (bala, 10)], "PIX", "2026-09-10")
    _vender(carrinho, [(bala, 5)], "Dinheiro", "2026-09-11")

    ranking = produtos_mais_vendidos(SETEMBRO)

    assert [(l["nome"], l["quantidade"], l["faturamento"]) for l in ranking] == [
        ("Bala", 15, 1.5),
        ("Coca-Cola 2L", 2, 25.0),
    ]


def test_faturamento_usa_o_preco_do_momento_da_venda(caixa, carrinho, coca):
    _vender(carrinho, [(coca, 2)], "PIX", "2026-09-10")  # 2 x 12,50
    editar_produto(coca, "Coca-Cola 2L", 15)             # aumento depois da venda

    (linha,) = produtos_mais_vendidos(SETEMBRO)
    assert linha["faturamento"] == 25.0


def test_ranking_com_limite(caixa, carrinho, coca, bala):
    _vender(carrinho, [(coca, 1), (bala, 3)], "PIX", "2026-09-10")

    (primeiro,) = produtos_mais_vendidos(SETEMBRO, limite=1)
    assert primeiro["nome"] == "Bala"


# ---------------------------------------------------------------- por dia

def test_vendas_por_dia(caixa, carrinho, coca):
    _vender(carrinho, [(coca, 1)], "PIX", "2026-09-12")
    _vender(carrinho, [(coca, 2)], "PIX", "2026-09-10")
    _vender(carrinho, [(coca, 1)], "Dinheiro", "2026-09-10")

    dias = vendas_por_dia(SETEMBRO)

    # agrupado por dia e em ordem de data; dias sem venda não aparecem
    assert [(l["dia"], l["quantidade"], l["total"]) for l in dias] == [
        ("2026-09-10", 2, 37.5),
        ("2026-09-12", 1, 12.5),
    ]
