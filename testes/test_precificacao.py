import pytest

from pdv.erros import ErroPDV
from pdv.precificacao import calcular_rentabilidade


def test_calcula_lucro_margem_e_acrescimo():
    rentabilidade = calcular_rentabilidade(13, 8)

    assert rentabilidade.preco_venda == 13
    assert rentabilidade.custo_unitario == 8
    assert rentabilidade.lucro_bruto_unitario == 5
    assert rentabilidade.margem_bruta_percentual == 38.46
    assert rentabilidade.acrescimo_sobre_custo_percentual == 62.5


def test_calcula_acrescimo_de_trinta_porcento_sem_confundir_com_margem():
    rentabilidade = calcular_rentabilidade(13, 10)

    assert rentabilidade.acrescimo_sobre_custo_percentual == 30
    assert rentabilidade.margem_bruta_percentual == 23.08


def test_custo_desconhecido_nao_vira_lucro_artificial():
    assert calcular_rentabilidade(13, None) is None


def test_preco_zero_deixa_margem_indefinida():
    rentabilidade = calcular_rentabilidade(0, 8)

    assert rentabilidade.lucro_bruto_unitario == -8
    assert rentabilidade.margem_bruta_percentual is None
    assert rentabilidade.acrescimo_sobre_custo_percentual == -100


def test_custo_zero_deixa_acrescimo_indefinido():
    rentabilidade = calcular_rentabilidade(13, 0)

    assert rentabilidade.lucro_bruto_unitario == 13
    assert rentabilidade.margem_bruta_percentual == 100
    assert rentabilidade.acrescimo_sobre_custo_percentual is None


@pytest.mark.parametrize("preco, custo", [(-1, 1), (1, -1)])
def test_recusa_preco_ou_custo_negativo(preco, custo):
    with pytest.raises(ErroPDV):
        calcular_rentabilidade(preco, custo)