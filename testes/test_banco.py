import sqlite3

import pytest

from pdv.banco import CAMINHO_PADRAO, PASTA_PROJETO, caminho_banco, conexao, criar_tabelas


def _colunas(tabela):
    with conexao() as conn:
        return {coluna["name"] for coluna in conn.execute(f"PRAGMA table_info({tabela})")}


def test_cria_todas_as_tabelas():
    with conexao() as conn:
        tabelas = {linha["name"] for linha in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}

    assert {
        "produtos", "movimentacoes_estoque", "vendas", "itens_vendas",
        "caixa", "movimentacoes_caixa", "usuarios",
    } <= tabelas


def test_usuarios_tem_colunas_esperadas():
    assert {
        "id", "nome", "login", "senha_hash",
        "perfil", "ativo", "data_criacao",
    } <= _colunas("usuarios")


def test_usuarios_rejeita_perfil_invalido():
    with pytest.raises(sqlite3.IntegrityError):
        with conexao() as conn:
            conn.execute("""
                INSERT INTO usuarios(nome, login, senha_hash, perfil)
                VALUES ('Teste', 'teste', 'hash-de-teste', 'gerente')
            """)


def test_login_nao_aceita_diferenca_apenas_de_maiusculas():
    with conexao() as conn:
        conn.execute("""
            INSERT INTO usuarios(nome, login, senha_hash, perfil)
            VALUES ('Teste', 'Alberto', 'hash-de-teste', 'dono')
        """)

    with pytest.raises(sqlite3.IntegrityError):
        with conexao() as conn:
            conn.execute("""
                INSERT INTO usuarios(nome, login, senha_hash, perfil)
                VALUES ('Outro', 'alberto', 'outro-hash', 'operador')
            """)

def test_vendas_tem_coluna_caixa_id():
    assert "caixa_id" in _colunas("vendas")


def test_migra_vendas_sem_troco(tmp_path, monkeypatch):
    """Bancos criados até a v1.6.0 não tinham vendas.valor_recebido nem vendas.troco."""
    caminho = tmp_path / "antigo.db"
    conn = sqlite3.connect(caminho)
    conn.execute("""
        CREATE TABLE vendas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER,
            valor_total REAL,
            forma_pagamento TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO vendas(caixa_id, valor_total, forma_pagamento) VALUES (1, 10, 'PIX')")
    conn.commit()
    conn.close()

    monkeypatch.setenv("PDV_BANCO", str(caminho))
    criar_tabelas()

    assert {"valor_recebido", "troco"} <= _colunas("vendas")
    with conexao() as conn:
        # vendas antigas continuam lá, com as colunas novas vazias
        venda = conn.execute("SELECT valor_total, valor_recebido, troco FROM vendas").fetchone()
    assert tuple(venda) == (10, None, None)


def test_migra_caixa_antigo_sem_valor_contado(tmp_path, monkeypatch):
    """Bancos criados até a v1.3.0 não tinham caixa.valor_contado."""
    caminho = tmp_path / "antigo.db"
    conn = sqlite3.connect(caminho)
    conn.execute("""
        CREATE TABLE caixa(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valor_inicial REAL NOT NULL,
            data_fechamento TIMESTAMP,
            valor_final REAL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    monkeypatch.setenv("PDV_BANCO", str(caminho))
    criar_tabelas()

    assert "valor_contado" in _colunas("caixa")


def test_criar_tabelas_pode_rodar_varias_vezes():
    criar_tabelas()
    criar_tabelas()


def test_migra_banco_antigo_sem_caixa_id(tmp_path, monkeypatch):
    """Bancos criados até a v1.2.1 não tinham vendas.caixa_id."""
    caminho = tmp_path / "antigo.db"
    conn = sqlite3.connect(caminho)
    conn.execute("""
        CREATE TABLE vendas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            valor_total REAL,
            forma_pagamento TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO vendas(valor_total, forma_pagamento) VALUES (10, 'PIX')")
    conn.commit()
    conn.close()

    monkeypatch.setenv("PDV_BANCO", str(caminho))
    criar_tabelas()

    assert "caixa_id" in _colunas("vendas")
    with conexao() as conn:
        assert conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0] == 1


def test_caminho_padrao_fica_na_pasta_do_projeto(monkeypatch):
    monkeypatch.delenv("PDV_BANCO")
    assert caminho_banco() == CAMINHO_PADRAO
    assert CAMINHO_PADRAO.parent.parent == PASTA_PROJETO
    assert (PASTA_PROJETO / "main.py").exists()
