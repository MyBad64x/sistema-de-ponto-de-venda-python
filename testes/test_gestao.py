from datetime import date

import pytest

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.estoque import definir_custo_inicial, registrar_compra
from pdv.gestao import (
    listar_compras,
    listar_produtos_gestao,
    resumo_potencial_estoque,
    resumo_rentabilidade,
)
from pdv.produtos import cadastrar_produto
from pdv.relatorios import Periodo
from pdv.vendas import finalizar_venda


HOJE = date(2026, 10, 6)
PERIODO = Periodo(date(2026, 10, 1), HOJE)


def _vender(carrinho, itens):
    for id_produto, quantidade in itens:
        carrinho.adicionar(id_produto, quantidade)
    resultado = finalizar_venda(carrinho, "PIX")
    with conexao() as conn:
        conn.execute(
            "UPDATE vendas SET data = ? WHERE id = ?",
            ("2026-10-06 15:00:00", resultado.id_venda),
        )


def test_lista_gerencial_calcula_lucro_e_ordena_por_margem(coca, bala):
    definir_custo_inicial(coca, 8)
    definir_custo_inicial(bala, 0.05)

    produtos = listar_produtos_gestao(ordenar_por="margem_maior")

    assert produtos[0]["id"] == bala
    coca_gerencial = next(produto for produto in produtos if produto["id"] == coca)
    assert coca_gerencial["lucro_bruto_unitario"] == 4.5
    assert coca_gerencial["margem_bruta_percentual"] == 36
    assert coca_gerencial["lucro_bruto_potencial"] == 22.5


def test_filtros_de_produto_recente_parado_e_sem_custo(coca, bala):
    with conexao() as conn:
        conn.execute(
            "UPDATE produtos SET data_cadastro = ? WHERE id = ?",
            ("2026-07-01 10:00:00", coca),
        )
        conn.execute(
            "UPDATE movimentacoes_estoque SET data_movimentacao = ? WHERE produto_id = ?",
            ("2026-08-01 10:00:00", coca),
        )
        conn.execute(
            "UPDATE produtos SET data_cadastro = ? WHERE id = ?",
            ("2026-10-01 10:00:00", bala),
        )

    assert [p["id"] for p in listar_produtos_gestao(
        filtro="parados", dias_sem_movimentacao=30, hoje=HOJE
    )] == [coca]
    assert [p["id"] for p in listar_produtos_gestao(filtro="recentes", hoje=HOJE)] == [bala]
    assert {p["id"] for p in listar_produtos_gestao(filtro="sem_custo")} == {coca, bala}


def test_lista_gerencial_recusa_filtro_e_ordenacao_invalidos():
    with pytest.raises(ErroPDV, match="Filtro"):
        listar_produtos_gestao(filtro="desconhecido")
    with pytest.raises(ErroPDV, match="Ordenação"):
        listar_produtos_gestao(ordenar_por="preco; DROP TABLE produtos")


def test_lista_gerencial_expoe_custo_desconhecido_sem_calcular_lucro(coca):
    (produto,) = listar_produtos_gestao()

    assert produto["custo_medio"] is None
    assert produto["lucro_bruto_unitario"] is None
    assert produto["margem_bruta_percentual"] is None


def test_historico_de_compras_pesquisa_fornecedor_referencia_e_data(coca):
    definir_custo_inicial(coca, 8)
    id_compra = registrar_compra(
        [(coca, 2, 9)],
        fornecedor="Distribuidora Central",
        referencia="REC-2026-10",
        data_compra="2026-10-05 12:00:00",
    )

    por_fornecedor = listar_compras(fornecedor="central")
    por_referencia = listar_compras(referencia="2026-10")
    por_data = listar_compras(inicio=date(2026, 10, 5), fim=date(2026, 10, 5))

    assert por_fornecedor[0]["compra_id"] == id_compra
    assert por_referencia[0]["referencia"] == "REC-2026-10"
    assert por_data[0]["produto"] == "Coca-Cola 2L"
    assert por_data[0]["total_item"] == 18


def test_historico_de_compras_recusa_periodo_invertido():
    with pytest.raises(ErroPDV, match="data inicial"):
        listar_compras(inicio=date(2026, 10, 6), fim=date(2026, 10, 1))


def test_resumo_de_lucro_realizado_separa_vendas_sem_custo(
    caixa, carrinho, coca, bala
):
    definir_custo_inicial(coca, 8)
    _vender(carrinho, [(coca, 2), (bala, 5)])

    resumo = resumo_rentabilidade(PERIODO)

    assert resumo.faturamento_total == 25.5
    assert resumo.faturamento_com_custo == 25
    assert resumo.custo_das_mercadorias == 16
    assert resumo.lucro_bruto == 9
    assert resumo.margem_bruta_percentual == 36
    assert resumo.unidades_sem_custo == 5


def test_potencial_do_estoque_exclui_produtos_sem_custo(coca, bala):
    definir_custo_inicial(coca, 8)

    resumo = resumo_potencial_estoque()

    assert resumo.faturamento_potencial == 62.5
    assert resumo.custo_estimado == 40
    assert resumo.lucro_bruto_potencial == 22.5
    assert resumo.margem_bruta_percentual == 36
    assert resumo.produtos_sem_custo == 1