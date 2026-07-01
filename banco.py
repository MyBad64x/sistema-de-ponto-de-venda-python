import sqlite3
import os

def conectar():
    os.makedirs("database", exist_ok=True)
    caminho = os.path.abspath("database/loja.db")
    return sqlite3.connect(caminho)

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

# tabela produtos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL,
        ativo INTEGER DEFAULT 1
    )
    """)

# tabela de movimentações do estoque
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes_estoque(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        observacao TEXT,
        data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

# tabela vendas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        valor_total REAL,
        forma_pagamento TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

#tabela de itens vendidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_vendas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        valor_unitario REAL
    )
    """)

#tabela do caixa
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caixa(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_abertura TIMESTAMP DEFAULT
    CURRENT_TIMESTAMP,
        valor_inicial REAL NOT NULL,
        data_fechamento TIMESTAMP,
        valor_final REAL,
        status TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

#checagem se as tabelas foram criadas mesmo
if __name__ == "__main__":
    criar_tabelas()
    print("Banco criado com sucesso!")
    print("Tabela produtos criada")
    print("Tabela vendas criada")
    print("Tabela itens_vendas criada")
    print("Tabela caixa criada")