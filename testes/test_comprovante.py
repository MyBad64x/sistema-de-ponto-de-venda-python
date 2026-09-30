import pytest

from pdv.comprovante import (
    LARGURA,
    gerar_comprovante,
    montar_texto,
    pasta_comprovantes,
    salvar_comprovante,
)
from pdv.erros import ErroPDV
from pdv.vendas import finalizar_venda


def _vender(caixa, carrinho, coca, bala, forma="Dinheiro", recebido=None):
    carrinho.adicionar(coca, 2)     # 2 x 12,50 = 25,00
    carrinho.adicionar(bala, 10)    # 10 x 0,10 = 1,00
    return finalizar_venda(carrinho, forma, valor_recebido=recebido)


def test_texto_tem_itens_total_e_troco(caixa, carrinho, coca, bala):
    resultado = _vender(caixa, carrinho, coca, bala, recebido=30)
    texto = gerar_comprovante(resultado.id_venda)

    assert f"Venda #{resultado.id_venda}" in texto
    assert "Coca-Cola 2L" in texto
    assert "2 x R$ 12,50" in texto
    assert "R$ 25,00" in texto
    assert "10 x R$ 0,10" in texto
    assert "TOTAL" in texto and "R$ 26,00" in texto
    assert "Recebido" in texto and "R$ 30,00" in texto
    assert "Troco" in texto and "R$ 4,00" in texto


def test_pix_nao_mostra_troco(caixa, carrinho, coca, bala):
    resultado = _vender(caixa, carrinho, coca, bala, forma="PIX")
    texto = gerar_comprovante(resultado.id_venda)

    assert "PIX" in texto
    assert "Troco" not in texto
    assert "Recebido" not in texto


def test_nenhuma_linha_passa_da_largura(caixa, carrinho, coca, bala):
    resultado = _vender(caixa, carrinho, coca, bala, recebido=30)
    texto = gerar_comprovante(resultado.id_venda)

    assert all(len(linha) <= LARGURA for linha in texto.splitlines())


def test_nome_muito_longo_e_cortado():
    venda = {"id": 1, "valor_total": 5.0, "forma_pagamento": "PIX",
            "valor_recebido": None, "troco": None, "data": "01/01/2026 10:00"}
    itens = [{"nome": "X" * 80, "quantidade": 1, "valor_unitario": 5.0}]

    texto = montar_texto(venda, itens)

    assert all(len(linha) <= LARGURA for linha in texto.splitlines())


def test_valor_no_padrao_brasileiro():
    venda = {"id": 1, "valor_total": 1234.5, "forma_pagamento": "PIX",
             "valor_recebido": None, "troco": None, "data": "01/01/2026 10:00"}
    itens = [{"nome": "Item", "quantidade": 1, "valor_unitario": 1234.5}]

    assert "R$ 1.234,50" in montar_texto(venda, itens)


def test_salvar_cria_arquivo_com_o_texto(caixa, carrinho, coca, bala):
    resultado = _vender(caixa, carrinho, coca, bala, forma="PIX")

    caminho = salvar_comprovante(resultado.id_venda)

    assert caminho.parent == pasta_comprovantes()
    assert caminho.name == f"venda_{resultado.id_venda:06d}.txt"
    assert caminho.read_text(encoding="utf-8") == gerar_comprovante(resultado.id_venda)


def test_venda_inexistente():
    with pytest.raises(ErroPDV, match="não encontrada"):
        gerar_comprovante(999)