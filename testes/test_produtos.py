import pytest

from pdv.erros import ErroPDV
from pdv.movimentacoes import listar_movimentacoes
from pdv.produtos import (
    ativar_produto,
    buscar_produto,
    buscar_produto_por_codigo_barras,
    buscar_produtos_por_nome,
    cadastrar_produto,
    desativar_produto,
    editar_produto,
    listar_produtos,
)


def test_cadastrar_produto(coca):
    produto = buscar_produto(coca)

    assert produto["nome"] == "Coca-Cola 2L"
    assert produto["preco"] == 12.50
    assert produto["estoque"] == 5
    assert produto["ativo"] == 1


def test_cadastrar_e_buscar_codigo_preserva_zeros_a_esquerda():
    id_produto = cadastrar_produto("Refrigerante", 13, 0, " 0012345678905 ")

    produto = buscar_produto_por_codigo_barras("0012345678905")

    assert produto["id"] == id_produto
    assert produto["codigo_barras"] == "0012345678905"


def test_codigo_de_barras_duplicado_e_recusado(coca):
    from pdv.produtos import editar_produto

    editar_produto(coca, "Coca-Cola 2L", 12.5, "789123")

    with pytest.raises(ErroPDV, match="código de barras já está cadastrado"):
        cadastrar_produto("Outro produto", 5, 0, "789123")


def test_busca_por_codigo_ignora_maiusculas_e_espacos():
    id_produto = cadastrar_produto("Produto", 10, 0, "abC123")

    produto = buscar_produto_por_codigo_barras("  ABC123  ")

    assert produto["id"] == id_produto


def test_busca_por_codigo_nao_encontra_codigo_vazio_ou_inexistente():
    assert buscar_produto_por_codigo_barras("   ") is None
    assert buscar_produto_por_codigo_barras("inexistente") is None


def test_busca_por_nome_parcial_e_sem_diferenciar_maiusculas(coca, bala):
    produtos = buscar_produtos_por_nome("COCA")

    assert [produto["id"] for produto in produtos] == [coca]
    assert buscar_produtos_por_nome("   ") == []


def test_busca_por_codigo_nao_retorna_produto_inativo(coca):
    from pdv.produtos import editar_produto

    editar_produto(coca, "Coca-Cola 2L", 12.5, "789123")
    desativar_produto(coca)

    assert buscar_produto_por_codigo_barras("789123") is None


def test_editar_sem_codigo_preserva_codigo_existente(coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789123")
    editar_produto(coca, "Coca-Cola 2L 2L", 13)

    assert buscar_produto(coca)["codigo_barras"] == "789123"


def test_editar_codigo_vazio_remove_codigo_existente(coca):
    editar_produto(coca, "Coca-Cola 2L", 12.5, "789123")
    editar_produto(coca, "Coca-Cola 2L", 12.5, "")

    assert buscar_produto(coca)["codigo_barras"] is None


def test_estoque_inicial_entra_no_historico(coca):
    (movimentacao,) = listar_movimentacoes()

    assert movimentacao["tipo"] == "ENTRADA"
    assert movimentacao["quantidade"] == 5
    assert movimentacao["observacao"] == "Estoque inicial"


def test_produto_sem_estoque_inicial_nao_gera_movimentacao():
    cadastrar_produto("Sem estoque", 1, 0)
    assert listar_movimentacoes() == []


def test_nome_e_apenas_espacos_sao_recusados():
    with pytest.raises(ErroPDV):
        cadastrar_produto("", 1, 0)
    with pytest.raises(ErroPDV):
        cadastrar_produto("   ", 1, 0)


def test_preco_e_estoque_negativos_sao_recusados():
    with pytest.raises(ErroPDV):
        cadastrar_produto("X", -1, 0)
    with pytest.raises(ErroPDV):
        cadastrar_produto("X", 1, -1)


def test_editar_altera_nome_e_preco_mas_nao_o_estoque(coca):
    editar_produto(coca, "Coca-Cola 2 litros", 13)
    produto = buscar_produto(coca)

    assert produto["nome"] == "Coca-Cola 2 litros"
    assert produto["preco"] == 13
    assert produto["estoque"] == 5


def test_editar_produto_inexistente():
    with pytest.raises(ErroPDV, match="não encontrado"):
        editar_produto(999, "X", 1)


def test_desativar_produto_inexistente_nao_quebra():
    """Antes: TypeError 'NoneType' object is not subscriptable."""
    with pytest.raises(ErroPDV, match="não encontrado"):
        desativar_produto(999)


def test_desativar_e_reativar(coca):
    produto = desativar_produto(coca)
    assert produto["nome"] == "Coca-Cola 2L"
    assert listar_produtos() == []
    assert len(listar_produtos(incluir_inativos=True)) == 1

    with pytest.raises(ErroPDV, match="já está desativado"):
        desativar_produto(coca)

    ativar_produto(coca)
    assert len(listar_produtos()) == 1

    with pytest.raises(ErroPDV, match="já está ativo"):
        ativar_produto(coca)


def test_listagem_em_ordem_alfabetica(coca, bala):
    assert [p["nome"] for p in listar_produtos()] == ["Bala", "Coca-Cola 2L"]
