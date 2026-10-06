"""Cadastro de produtos."""

import sqlite3

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.movimentacoes import ENTRADA, registrar_movimentacao


def _validar_nome(nome):
    nome = (nome or "").strip()
    if not nome:
        raise ErroPDV("O nome do produto não pode ficar vazio.")
    return nome


def _validar_preco(preco):
    if preco < 0:
        raise ErroPDV("O preço não pode ser negativo.")
    return round(preco, 2)


def _normalizar_codigo_barras(codigo_barras):
    if codigo_barras is None:
        return None
    codigo_barras = str(codigo_barras).strip()
    return codigo_barras or None


def obter_produto(conn, id_produto):
    """Busca o produto dentro de uma conexão já aberta; erro se não existir."""
    produto = conn.execute(
        "SELECT * FROM produtos WHERE id = ?", (id_produto,)
    ).fetchone()

    if produto is None:
        raise ErroPDV(f"Produto {id_produto} não encontrado.")

    return produto


def buscar_produto(id_produto):
    """Devolve o produto (ativo ou não) ou None se o ID não existir."""
    with conexao() as conn:
        return conn.execute(
            "SELECT * FROM produtos WHERE id = ?", (id_produto,)
        ).fetchone()


def buscar_produto_por_codigo_barras(codigo_barras, incluir_inativos=False):
    """Busca um produto ativo pelo código, preservando zeros à esquerda."""
    codigo_barras = _normalizar_codigo_barras(codigo_barras)
    if codigo_barras is None:
        return None

    sql = "SELECT * FROM produtos WHERE codigo_barras = ? COLLATE NOCASE"
    if not incluir_inativos:
        sql += " AND ativo = 1"

    with conexao() as conn:
        return conn.execute(sql, (codigo_barras,)).fetchone()


def buscar_produtos_por_nome(nome):
    """Busca produtos ativos cujo nome contenha o texto informado."""
    nome = (nome or "").strip()
    if not nome:
        return []

    with conexao() as conn:
        return conn.execute(
            """
            SELECT * FROM produtos
            WHERE nome LIKE ? COLLATE NOCASE AND ativo = 1
            ORDER BY nome
            """,
            (f"%{nome}%",),
        ).fetchall()


def listar_produtos(incluir_inativos=False):
    sql = "SELECT * FROM produtos"
    if not incluir_inativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome"

    with conexao() as conn:
        return conn.execute(sql).fetchall()


def cadastrar_produto(nome, preco, estoque_inicial=0, codigo_barras=None):
    """Cadastra o produto e devolve o ID criado.

    O estoque inicial também entra no histórico de movimentações, assim a soma
    das movimentações de um produto sempre bate com o estoque dele.
    """
    nome = _validar_nome(nome)
    preco = _validar_preco(preco)
    codigo_barras = _normalizar_codigo_barras(codigo_barras)
    if estoque_inicial < 0:
        raise ErroPDV("O estoque inicial não pode ser negativo.")

    try:
        with conexao() as conn:
            cursor = conn.execute(
                """
                INSERT INTO produtos(nome, preco, estoque, codigo_barras, data_cadastro)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (nome, preco, estoque_inicial, codigo_barras),
            )
            id_produto = cursor.lastrowid

            if estoque_inicial > 0:
                registrar_movimentacao(
                    conn, id_produto, ENTRADA, estoque_inicial, "Estoque inicial"
                )
    except sqlite3.IntegrityError as erro:
        if "codigo_barras" not in str(erro):
            raise
        raise ErroPDV("Este código de barras já está cadastrado.") from erro

    return id_produto


def editar_produto(id_produto, nome, preco, codigo_barras=None):
    """Altera nome e preço.

    O estoque não é editado aqui de propósito: mudanças de estoque passam pelo
    módulo de estoque (entrada ou ajuste) para ficarem registradas no histórico.
    """
    nome = _validar_nome(nome)
    preco = _validar_preco(preco)

    try:
        with conexao() as conn:
            produto = obter_produto(conn, id_produto)
            if codigo_barras is None:
                codigo_barras = produto["codigo_barras"]
            else:
                codigo_barras = _normalizar_codigo_barras(codigo_barras)

            conn.execute(
                """
                UPDATE produtos
                SET nome = ?, preco = ?, codigo_barras = ?
                WHERE id = ?
                """,
                (nome, preco, codigo_barras, id_produto),
            )
    except sqlite3.IntegrityError as erro:
        if "codigo_barras" not in str(erro):
            raise
        raise ErroPDV("Este código de barras já está cadastrado.") from erro


def desativar_produto(id_produto):
    """Desativa em vez de excluir, para não perder o histórico de vendas."""
    with conexao() as conn:
        produto = obter_produto(conn, id_produto)

        if not produto["ativo"]:
            raise ErroPDV(f"O produto '{produto['nome']}' já está desativado.")

        conn.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (id_produto,))

    return produto


def ativar_produto(id_produto):
    with conexao() as conn:
        produto = obter_produto(conn, id_produto)

        if produto["ativo"]:
            raise ErroPDV(f"O produto '{produto['nome']}' já está ativo.")

        conn.execute("UPDATE produtos SET ativo = 1 WHERE id = ?", (id_produto,))

    return produto
