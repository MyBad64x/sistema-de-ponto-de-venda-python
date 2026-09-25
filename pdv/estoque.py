"""Entrada e ajuste de estoque."""

from dataclasses import dataclass

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.movimentacoes import AJUSTE, ENTRADA, registrar_movimentacao
from pdv.produtos import obter_produto


@dataclass
class ResultadoEstoque:
    nome_produto: str
    estoque_anterior: int
    estoque_atual: int


def entrada_estoque(id_produto, quantidade, observacao=""):
    """Soma unidades ao estoque (ex.: chegada de mercadoria)."""
    if quantidade <= 0:
        raise ErroPDV("A quantidade de entrada deve ser maior que zero.")

    with conexao() as conn:
        produto = obter_produto(conn, id_produto)

        conn.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            (quantidade, id_produto),
        )
        registrar_movimentacao(conn, id_produto, ENTRADA, quantidade, observacao)

    return ResultadoEstoque(
        produto["nome"], produto["estoque"], produto["estoque"] + quantidade
    )


def ajustar_estoque(id_produto, novo_estoque, observacao=""):
    """Corrige o estoque para o valor contado (ex.: inventário, perda, quebra).

    O histórico guarda a diferença (positiva ou negativa), não o valor final.
    """
    if novo_estoque < 0:
        raise ErroPDV("O estoque não pode ser negativo.")

    with conexao() as conn:
        produto = obter_produto(conn, id_produto)
        diferenca = novo_estoque - produto["estoque"]

        if diferenca == 0:
            raise ErroPDV("O estoque já está com esse valor; nenhum ajuste feito.")

        conn.execute(
            "UPDATE produtos SET estoque = ? WHERE id = ?",
            (novo_estoque, id_produto),
        )
        registrar_movimentacao(conn, id_produto, AJUSTE, diferenca, observacao)

    return ResultadoEstoque(produto["nome"], produto["estoque"], novo_estoque)
