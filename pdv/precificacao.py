"""Calculos de lucro bruto e indicadores de precificacao."""

from dataclasses import dataclass

from pdv.erros import ErroPDV


@dataclass(frozen=True)
class Rentabilidade:
    preco_venda: float
    custo_unitario: float
    lucro_bruto_unitario: float
    margem_bruta_percentual: float = None
    acrescimo_sobre_custo_percentual: float = None


def calcular_rentabilidade(preco_venda, custo_unitario):
    """Calcula indicadores por unidade; retorna None se o custo for desconhecido."""
    if custo_unitario is None:
        return None

    if preco_venda < 0:
        raise ErroPDV("O preco de venda nao pode ser negativo.")
    if custo_unitario < 0:
        raise ErroPDV("O custo unitario nao pode ser negativo.")

    preco_venda = round(preco_venda, 2)
    custo_unitario = round(custo_unitario, 2)
    lucro_bruto = round(preco_venda - custo_unitario, 2)

    margem_bruta = None
    if preco_venda > 0:
        margem_bruta = round(lucro_bruto / preco_venda * 100, 2)

    acrescimo_sobre_custo = None
    if custo_unitario > 0:
        acrescimo_sobre_custo = round(lucro_bruto / custo_unitario * 100, 2)

    return Rentabilidade(
        preco_venda=preco_venda,
        custo_unitario=custo_unitario,
        lucro_bruto_unitario=lucro_bruto,
        margem_bruta_percentual=margem_bruta,
        acrescimo_sobre_custo_percentual=acrescimo_sobre_custo,
    )