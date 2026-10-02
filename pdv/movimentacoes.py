"""Histórico de movimentações de estoque (entradas, ajustes e vendas)."""

from pdv.banco import conexao

ENTRADA = "ENTRADA"
AJUSTE = "AJUSTE"
VENDA = "VENDA"
CUSTO_INICIAL = "CUSTO_INICIAL"


def registrar_movimentacao(
    conn,
    produto_id,
    tipo,
    quantidade,
    observacao="",
    compra_id=None,
    custo_unitario=None,
    data_movimentacao=None,
):
    """Grava uma movimentação usando a conexão de quem chamou.

    Recebe a conexão em vez de abrir outra para que a alteração do estoque e o
    registro da movimentação façam parte da mesma transação: ou as duas coisas
    são gravadas, ou nenhuma.
    """
    conn.execute("""
        INSERT INTO movimentacoes_estoque(
            produto_id, tipo, quantidade, observacao, compra_id,
            custo_unitario, data_movimentacao
        )
        VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
    """, (
        produto_id,
        tipo,
        quantidade,
        observacao or "",
        compra_id,
        custo_unitario,
        data_movimentacao,
    ))


def listar_movimentacoes(limite=None):
    """Movimentações da mais recente para a mais antiga, com data no horário local."""
    sql = """
        SELECT
            m.id,
            p.nome AS produto,
            m.tipo,
            m.quantidade,
            COALESCE(m.observacao, '') AS observacao,
            datetime(m.data_movimentacao, 'localtime') AS data
        FROM movimentacoes_estoque m
        JOIN produtos p ON p.id = m.produto_id
        ORDER BY m.id DESC
    """
    parametros = ()
    if limite is not None:
        sql += " LIMIT ?"
        parametros = (limite,)

    with conexao() as conn:
        return conn.execute(sql, parametros).fetchall()
