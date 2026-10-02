"""Entrada e ajuste de estoque."""

from dataclasses import dataclass

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.movimentacoes import AJUSTE, CUSTO_INICIAL, ENTRADA, registrar_movimentacao
from pdv.produtos import obter_produto


@dataclass
class ResultadoEstoque:
    nome_produto: str
    estoque_anterior: int
    estoque_atual: int


def _validar_custo_unitario(custo_unitario):
    if custo_unitario < 0:
        raise ErroPDV("O custo unitário não pode ser negativo.")
    return round(custo_unitario, 2)


def definir_custo_inicial(id_produto, custo_unitario):
    """Informa o custo conhecido para um produto ainda sem custo médio."""
    custo_unitario = _validar_custo_unitario(custo_unitario)

    with conexao() as conn:
        produto = obter_produto(conn, id_produto)
        if produto["custo_medio"] is not None:
            raise ErroPDV(f"O produto '{produto['nome']}' já possui custo médio.")

        conn.execute(
            "UPDATE produtos SET custo_medio = ? WHERE id = ?",
            (custo_unitario, id_produto),
        )
        registrar_movimentacao(
            conn,
            id_produto,
            CUSTO_INICIAL,
            0,
            "Custo inicial informado",
            custo_unitario=custo_unitario,
        )

    return custo_unitario


def registrar_compra(
    itens,
    fornecedor="",
    referencia="",
    observacao="",
    data_compra=None,
    custos_iniciais=None,
):
    """Registra uma compra e atualiza estoque e custo médio atomicamente.

    Cada item é uma tupla (id_produto, quantidade, custo_unitario). Produtos
    com saldo positivo e custo desconhecido exigem que custos_iniciais informe
    o custo do saldo atual. Esse custo só é salvo se a compra for confirmada.
    """
    try:
        itens = list(itens)
    except TypeError:
        raise ErroPDV("Informe pelo menos um item para a compra.")

    if not itens:
        raise ErroPDV("Informe pelo menos um item para a compra.")

    custos_iniciais = custos_iniciais or {}
    custos_iniciais = {
        id_produto: _validar_custo_unitario(custo)
        for id_produto, custo in custos_iniciais.items()
    }

    itens_validos = []
    produtos_incluidos = set()

    for item in itens:
        try:
            id_produto, quantidade, custo_unitario = item
        except (TypeError, ValueError):
            raise ErroPDV("Cada item deve ter produto, quantidade e custo unitário.")

        if id_produto in produtos_incluidos:
            raise ErroPDV("Cada produto pode aparecer apenas uma vez na compra.")
        produtos_incluidos.add(id_produto)

        if quantidade <= 0:
            raise ErroPDV("A quantidade comprada deve ser maior que zero.")

        itens_validos.append((
            id_produto,
            quantidade,
            _validar_custo_unitario(custo_unitario),
        ))

    with conexao() as conn:
        itens_calculados = []

        for id_produto, quantidade, custo_unitario in itens_validos:
            produto = obter_produto(conn, id_produto)
            estoque_atual = produto["estoque"]
            custo_medio = produto["custo_medio"]
            custo_inicial = None

            if estoque_atual > 0 and custo_medio is None:
                custo_inicial = custos_iniciais.get(id_produto)
                if custo_inicial is None:
                    raise ErroPDV(
                        f"Informe o custo inicial do produto '{produto['nome']}' "
                        "antes de registrar a compra."
                    )
                custo_medio = custo_inicial

            if estoque_atual <= 0:
                novo_custo_medio = custo_unitario
            else:
                novo_custo_medio = round(
                    (estoque_atual * custo_medio + quantidade * custo_unitario)
                    / (estoque_atual + quantidade),
                    2,
                )

            itens_calculados.append(
                (produto, quantidade, custo_unitario, novo_custo_medio, custo_inicial)
            )

        if data_compra is None:
            cursor = conn.execute(
                "INSERT INTO compras(fornecedor, referencia, observacao) VALUES (?, ?, ?)",
                (fornecedor or "", referencia or "", observacao or ""),
            )
        else:
            cursor = conn.execute(
                """
                INSERT INTO compras(fornecedor, referencia, data_compra, observacao)
                VALUES (?, ?, ?, ?)
                """,
                (fornecedor or "", referencia or "", data_compra, observacao or ""),
            )

        id_compra = cursor.lastrowid
        data_registro = conn.execute(
            "SELECT data_compra FROM compras WHERE id = ?", (id_compra,)
        ).fetchone()["data_compra"]

        for produto, quantidade, custo_unitario, novo_custo_medio, custo_inicial in itens_calculados:
            if custo_inicial is not None:
                conn.execute(
                    "UPDATE produtos SET custo_medio = ? WHERE id = ?",
                    (custo_inicial, produto["id"]),
                )
                registrar_movimentacao(
                    conn,
                    produto["id"],
                    CUSTO_INICIAL,
                    0,
                    f"Custo inicial informado na compra #{id_compra}",
                    compra_id=id_compra,
                    custo_unitario=custo_inicial,
                    data_movimentacao=data_registro,
                )

            conn.execute(
                "UPDATE produtos SET estoque = estoque + ?, custo_medio = ? WHERE id = ?",
                (quantidade, novo_custo_medio, produto["id"]),
            )
            registrar_movimentacao(
                conn,
                produto["id"],
                ENTRADA,
                quantidade,
                f"Compra #{id_compra}",
                compra_id=id_compra,
                custo_unitario=custo_unitario,
                data_movimentacao=data_registro,
            )

    return id_compra


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
    return ajustar_estoque_em_lote({id_produto: novo_estoque}, observacao)[0]


def ajustar_estoque_em_lote(contagens, observacao="Contagem de estoque"):
    """Aplica várias contagens numa transação e registra somente as diferenças."""
    if not contagens:
        raise ErroPDV("Informe ao menos um produto para a contagem.")

    for novo_estoque in contagens.values():
        if novo_estoque < 0:
            raise ErroPDV("O estoque não pode ser negativo.")

    with conexao() as conn:
        resultados = []

        for id_produto, novo_estoque in contagens.items():
            produto = obter_produto(conn, id_produto)
            diferenca = novo_estoque - produto["estoque"]

            if diferenca == 0:
                continue

            conn.execute(
                "UPDATE produtos SET estoque = ? WHERE id = ?",
                (novo_estoque, id_produto),
            )
            registrar_movimentacao(conn, id_produto, AJUSTE, diferenca, observacao)
            resultados.append(ResultadoEstoque(produto["nome"], produto["estoque"], novo_estoque))

        if not resultados:
            raise ErroPDV("O estoque já está com esse valor; nenhum ajuste feito.")

    return resultados
