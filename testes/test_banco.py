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
        "caixa", "movimentacoes_caixa", "usuarios", "compras",
    } <= tabelas


def test_tabelas_de_produto_compra_e_venda_tem_colunas_de_custo():
    assert {"codigo_barras", "custo_medio", "data_cadastro"} <= _colunas("produtos")
    assert {"fornecedor", "referencia", "data_compra", "observacao"} <= _colunas("compras")
    assert {"compra_id", "custo_unitario"} <= _colunas("movimentacoes_estoque")
    assert "custo_unitario" in _colunas("itens_vendas")


def test_codigo_de_barras_nao_pode_ser_duplicado_ignorando_maiusculas():
    with conexao() as conn:
        conn.execute(
            "INSERT INTO produtos(nome, preco, estoque, codigo_barras) VALUES (?, ?, ?, ?)",
            ("Produto A", 10, 1, "abc123"),
        )

    with pytest.raises(sqlite3.IntegrityError):
        with conexao() as conn:
            conn.execute(
                "INSERT INTO produtos(nome, preco, estoque, codigo_barras) VALUES (?, ?, ?, ?)",
                ("Produto B", 10, 1, "ABC123"),
            )


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


def test_migra_produtos_movimentacoes_e_vendas_sem_dados_de_custo(tmp_path, monkeypatch):
    caminho = tmp_path / "antigo.db"
    conn = sqlite3.connect(caminho)
    conn.execute("""
        CREATE TABLE produtos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    """)
    conn.execute("INSERT INTO produtos(nome, preco, estoque) VALUES ('Produto antigo', 15, 4)")
    conn.execute("""
        CREATE TABLE movimentacoes_estoque(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            observacao TEXT,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO movimentacoes_estoque(produto_id, tipo, quantidade, observacao)
        VALUES (1, 'ENTRADA', 4, 'Estoque inicial')
    """)
    conn.execute("""
        CREATE TABLE itens_vendas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            valor_unitario REAL
        )
    """)
    conn.execute(
        "INSERT INTO itens_vendas(venda_id, produto_id, quantidade, valor_unitario) "
        "VALUES (1, 1, 1, 15)"
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("PDV_BANCO", str(caminho))
    criar_tabelas()

    with conexao() as conn:
        produto = conn.execute(
            "SELECT nome, codigo_barras, custo_medio, data_cadastro "
            "FROM produtos WHERE id = 1"
        ).fetchone()
        movimentacao = conn.execute(
            "SELECT quantidade, compra_id, custo_unitario FROM movimentacoes_estoque"
        ).fetchone()
        item_venda = conn.execute(
            "SELECT valor_unitario, custo_unitario FROM itens_vendas"
        ).fetchone()

    assert tuple(produto) == ("Produto antigo", None, None, None)
    assert tuple(movimentacao) == (4, None, None)
    assert tuple(item_venda) == (15, None)


def test_caminho_padrao_fica_na_pasta_do_projeto(monkeypatch):
    monkeypatch.delenv("PDV_BANCO")
    assert caminho_banco() == CAMINHO_PADRAO
    assert CAMINHO_PADRAO.parent.parent == PASTA_PROJETO
    assert (PASTA_PROJETO / "main.py").exists()
