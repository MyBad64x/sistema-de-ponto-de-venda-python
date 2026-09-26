"""Abertura, sangria, suprimento, consulta e fechamento de caixa."""

from dataclasses import dataclass

from pdv.banco import conexao
from pdv.erros import ErroPDV

ABERTO = "ABERTO"
FECHADO = "FECHADO"

SANGRIA = "SANGRIA"
SUPRIMENTO = "SUPRIMENTO"

# só as vendas em dinheiro entram fisicamente na gaveta
DINHEIRO = "Dinheiro"


@dataclass
class ResumoCaixa:
    id_caixa: int
    data_abertura: str
    valor_inicial: float
    quantidade_vendas: int
    vendas_por_forma: dict  # {"Dinheiro": 20.0, "PIX": 25.0}
    suprimentos: float
    sangrias: float
    valor_contado: float = None  # só existe depois do fechamento

    @property
    def total_vendas(self):
        return round(sum(self.vendas_por_forma.values()), 2)

    @property
    def vendas_dinheiro(self):
        return self.vendas_por_forma.get(DINHEIRO, 0)

    @property
    def dinheiro_esperado(self):
        """Quanto deveria haver na gaveta agora."""
        return round(
            self.valor_inicial + self.vendas_dinheiro + self.suprimentos - self.sangrias, 2
        )

    @property
    def diferenca(self):
        """Contado - esperado. Positivo = sobra, negativo = falta."""
        if self.valor_contado is None:
            return None
        return round(self.valor_contado - self.dinheiro_esperado, 2)


def _caixa_aberto(conn):
    return conn.execute("""
        SELECT id, valor_inicial, datetime(data_abertura, 'localtime') AS data_abertura
        FROM caixa
        WHERE status = ?
    """, (ABERTO,)).fetchone()


def _exigir_caixa_aberto(conn):
    caixa = _caixa_aberto(conn)
    if caixa is None:
        raise ErroPDV("Nenhum caixa está aberto.")
    return caixa


def _resumir(conn, caixa):
    vendas = conn.execute("""
        SELECT forma_pagamento, COUNT(*) AS quantidade, SUM(valor_total) AS total
        FROM vendas
        WHERE caixa_id = ?
        GROUP BY forma_pagamento
    """, (caixa["id"],)).fetchall()

    movimentos = conn.execute("""
        SELECT tipo, SUM(valor) AS total
        FROM movimentacoes_caixa
        WHERE caixa_id = ?
        GROUP BY tipo
    """, (caixa["id"],)).fetchall()
    totais_movimentos = {linha["tipo"]: linha["total"] for linha in movimentos}

    return ResumoCaixa(
        id_caixa=caixa["id"],
        data_abertura=caixa["data_abertura"],
        valor_inicial=caixa["valor_inicial"],
        quantidade_vendas=sum(linha["quantidade"] for linha in vendas),
        vendas_por_forma={
            linha["forma_pagamento"]: round(linha["total"], 2) for linha in vendas
        },
        suprimentos=round(totais_movimentos.get(SUPRIMENTO, 0), 2),
        sangrias=round(totais_movimentos.get(SANGRIA, 0), 2),
    )


def caixa_aberto():
    """Devolve o caixa aberto ou None."""
    with conexao() as conn:
        return _caixa_aberto(conn)


def abrir_caixa(valor_inicial):
    if valor_inicial < 0:
        raise ErroPDV("O valor inicial do caixa não pode ser negativo.")

    with conexao() as conn:
        if _caixa_aberto(conn) is not None:
            raise ErroPDV("Já existe um caixa aberto.")

        cursor = conn.execute(
            "INSERT INTO caixa(valor_inicial, status) VALUES (?, ?)",
            (round(valor_inicial, 2), ABERTO),
        )

    return cursor.lastrowid


def _movimentar_caixa(tipo, valor, motivo):
    if valor <= 0:
        raise ErroPDV("O valor deve ser maior que zero.")

    motivo = (motivo or "").strip()
    if not motivo:
        raise ErroPDV("Informe o motivo.")

    valor = round(valor, 2)

    with conexao() as conn:
        caixa = _exigir_caixa_aberto(conn)

        if tipo == SANGRIA:
            disponivel = _resumir(conn, caixa).dinheiro_esperado
            if valor > disponivel:
                raise ErroPDV("O valor da sangria é maior que o dinheiro na gaveta.")

        conn.execute(
            "INSERT INTO movimentacoes_caixa(caixa_id, tipo, valor, motivo) VALUES (?, ?, ?, ?)",
            (caixa["id"], tipo, valor, motivo),
        )

        return _resumir(conn, caixa)


def registrar_sangria(valor, motivo):
    """Retirada de dinheiro da gaveta (ex.: levar ao banco, pagar fornecedor)."""
    return _movimentar_caixa(SANGRIA, valor, motivo)


def registrar_suprimento(valor, motivo):
    """Entrada de dinheiro na gaveta que não é venda (ex.: reforço de troco)."""
    return _movimentar_caixa(SUPRIMENTO, valor, motivo)


def resumo_caixa_aberto():
    """Situação do caixa aberto até agora (para a opção 'Status do caixa')."""
    with conexao() as conn:
        return _resumir(conn, _exigir_caixa_aberto(conn))


def fechar_caixa(valor_contado):
    """Fecha o caixa guardando o valor esperado e o valor contado na gaveta."""
    if valor_contado < 0:
        raise ErroPDV("O valor contado não pode ser negativo.")

    with conexao() as conn:
        caixa = _exigir_caixa_aberto(conn)

        resumo = _resumir(conn, caixa)
        resumo.valor_contado = round(valor_contado, 2)

        conn.execute("""
            UPDATE caixa
            SET valor_final = ?,
                valor_contado = ?,
                data_fechamento = CURRENT_TIMESTAMP,
                status = ?
            WHERE id = ?
        """, (resumo.dinheiro_esperado, resumo.valor_contado, FECHADO, caixa["id"]))

    return resumo


def listar_caixas(limite=None):
    """Histórico de caixas, do mais recente para o mais antigo.

    Uma consulta só traz cada caixa com a quantidade e o total das vendas dele.
    O LEFT JOIN mantém na lista os caixas que não tiveram nenhuma venda.
    """
    sql = """
        SELECT
            c.id,
            c.status,
            strftime('%d/%m/%Y %H:%M', c.data_abertura, 'localtime') AS abertura,
            strftime('%d/%m/%Y %H:%M', c.data_fechamento, 'localtime') AS fechamento,
            COUNT(v.id) AS quantidade_vendas,
            ROUND(COALESCE(SUM(v.valor_total), 0), 2) AS total_vendas,
            c.valor_final AS esperado,
            c.valor_contado AS contado,
            ROUND(c.valor_contado - c.valor_final, 2) AS diferenca
        FROM caixa c
        LEFT JOIN vendas v ON v.caixa_id = c.id
        GROUP BY c.id
        ORDER BY c.id DESC
    """
    parametros = ()
    if limite is not None:
        sql += " LIMIT ?"
        parametros = (limite,)

    with conexao() as conn:
        return conn.execute(sql, parametros).fetchall()


def detalhar_caixa(id_caixa):
    """Resumo completo de qualquer caixa, aberto ou fechado."""
    with conexao() as conn:
        caixa = conn.execute("""
            SELECT
                id,
                valor_inicial,
                valor_contado,
                datetime(data_abertura, 'localtime') AS data_abertura
            FROM caixa
            WHERE id = ?
        """, (id_caixa,)).fetchone()

        if caixa is None:
            raise ErroPDV(f"Caixa {id_caixa} não encontrado.")

        resumo = _resumir(conn, caixa)
        resumo.valor_contado = caixa["valor_contado"]

    return resumo
