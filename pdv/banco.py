"""Conexão com o SQLite e criação/atualização das tabelas."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# O banco fica em <pasta do projeto>/database/loja.db, não importa de qual pasta
# o programa é executado. A variável de ambiente PDV_BANCO permite apontar para
# outro arquivo (os testes usam isso para trabalhar num banco temporário).
PASTA_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO = PASTA_PROJETO / "database" / "loja.db"


def caminho_banco():
    return Path(os.environ.get("PDV_BANCO", CAMINHO_PADRAO))


@contextmanager
def conexao():
    """Abre uma conexão e garante commit, rollback e fechamento.

    Uso:
        with conexao() as conn:
            conn.execute(...)

    Se tudo der certo dentro do bloco, faz commit. Se qualquer erro acontecer,
    desfaz tudo (rollback) e deixa o erro seguir. Em qualquer caso, fecha a conexão.
    Assim uma venda nunca fica "pela metade" no banco.
    """
    caminho = caminho_banco()
    caminho.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(caminho)
    # permite acessar colunas pelo nome: produto["nome"] em vez de produto[1]
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def criar_tabelas():
    with conexao() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                estoque INTEGER NOT NULL,
                ativo INTEGER DEFAULT 1
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes_estoque(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                observacao TEXT,
                data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS caixa(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                valor_inicial REAL NOT NULL,
                data_fechamento TIMESTAMP,
                valor_final REAL,
                status TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caixa_id INTEGER,
                valor_total REAL,
                forma_pagamento TEXT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS itens_vendas(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                produto_id INTEGER,
                quantidade INTEGER,
                valor_unitario REAL
            )
        """)

        _atualizar_banco_antigo(conn)


def _atualizar_banco_antigo(conn):
    """Migrações: ajustes em bancos criados por versões anteriores.

    CREATE TABLE IF NOT EXISTS não altera uma tabela que já existe, então
    colunas novas precisam ser adicionadas aqui com ALTER TABLE.
    """
    colunas_vendas = {coluna["name"] for coluna in conn.execute("PRAGMA table_info(vendas)")}

    # v1.2.2: vendas passou a guardar em qual caixa aconteceu
    if "caixa_id" not in colunas_vendas:
        conn.execute("ALTER TABLE vendas ADD COLUMN caixa_id INTEGER")


if __name__ == "__main__":
    criar_tabelas()
    print(f"Banco pronto em {caminho_banco()}")
