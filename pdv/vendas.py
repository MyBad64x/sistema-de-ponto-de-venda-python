"""Finalização de vendas."""

from dataclasses import dataclass, field

from pdv.banco import conexao
from pdv.caixa import ABERTO, DINHEIRO
from pdv.erros import ErroPDV, EstoqueInsuficiente
from pdv.movimentacoes import VENDA, registrar_movimentacao
from pdv.produtos import obter_produto

FORMAS_PAGAMENTO = (
    DINHEIRO,
    "PIX",
    "Cartão de débito",
    "Cartão de crédito",
)


@dataclass
class ResultadoVenda:
    id_venda: int
    total: float
    forma_pagamento: str
    # [(nome do produto, estoque que ficou)] para produtos que ficaram negativos
    estoques_negativos: list = field(default_factory=list)


def finalizar_venda(carrinho, forma_pagamento, permitir_estoque_negativo=False):
    """Grava a venda, os itens, baixa o estoque e registra as movimentações.

    Tudo acontece numa única transação: se qualquer passo falhar, nada é gravado.
    Se faltar estoque, levanta EstoqueInsuficiente; quem chamou pode perguntar ao
    operador e tentar de novo com permitir_estoque_negativo=True.
    """
    if forma_pagamento not in FORMAS_PAGAMENTO:
        raise ErroPDV(f"Forma de pagamento inválida: {forma_pagamento}.")

    if carrinho.esta_vazio():
        raise ErroPDV("O carrinho está vazio.")

    with conexao() as conn:

        caixa = conn.execute(
            "SELECT id FROM caixa WHERE status = ?", (ABERTO,)
        ).fetchone()
        if caixa is None:
            raise ErroPDV("Abra o caixa antes de finalizar a venda.")

        # 1) confere tudo antes de gravar qualquer coisa
        itens = []
        total = 0

        for id_produto, quantidade in carrinho.itens.items():
            produto = obter_produto(conn, id_produto)

            if not produto["ativo"]:
                raise ErroPDV(f"O produto '{produto['nome']}' foi desativado.")

            if quantidade > produto["estoque"] and not permitir_estoque_negativo:
                raise EstoqueInsuficiente(produto["nome"], produto["estoque"], quantidade)

            itens.append((produto, quantidade))
            total += produto["preco"] * quantidade

        total = round(total, 2)

        # 2) grava a venda
        cursor = conn.execute(
            "INSERT INTO vendas(caixa_id, valor_total, forma_pagamento) VALUES (?, ?, ?)",
            (caixa["id"], total, forma_pagamento),
        )
        id_venda = cursor.lastrowid

        estoques_negativos = []

        for produto, quantidade in itens:
            conn.execute("""
                INSERT INTO itens_vendas(venda_id, produto_id, quantidade, valor_unitario)
                VALUES (?, ?, ?, ?)
            """, (id_venda, produto["id"], quantidade, produto["preco"]))

            # "estoque - ?" faz a conta no próprio banco, com o valor mais atual
            conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto["id"]),
            )

            registrar_movimentacao(
                conn, produto["id"], VENDA, -quantidade, f"Venda #{id_venda}"
            )

            estoque_final = produto["estoque"] - quantidade
            if estoque_final < 0:
                estoques_negativos.append((produto["nome"], estoque_final))

    # só limpa o carrinho depois que o banco confirmou a venda
    carrinho.limpar()

    return ResultadoVenda(id_venda, total, forma_pagamento, estoques_negativos)
