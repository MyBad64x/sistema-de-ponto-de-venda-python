import pytest

from pdv.banco import criar_tabelas
from pdv.caixa import abrir_caixa
from pdv.carrinho import Carrinho
from pdv.produtos import cadastrar_produto


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    """Cada teste roda num banco novo e vazio, sem tocar no database/loja.db real."""
    caminho = tmp_path / "teste.db"
    monkeypatch.setenv("PDV_BANCO", str(caminho))
    criar_tabelas()
    return caminho


@pytest.fixture
def caixa():
    return abrir_caixa(100)


@pytest.fixture
def carrinho():
    return Carrinho()


@pytest.fixture
def coca():
    return cadastrar_produto("Coca-Cola 2L", 12.50, 5)


@pytest.fixture
def bala():
    return cadastrar_produto("Bala", 0.10, 100)
