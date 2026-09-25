"""Abertura, consulta e fechamento de caixa."""

from dataclasses import dataclass

from pdv.banco import conexao
from pdv.erros import ErroPDV

ABERTO = "ABERTO"
FECHADO = "FECHADO"


@dataclass
class ResumoCaixa:
    id_caixa: int
    data_abertura: str
    valor_inicial: float
    quantidade_vendas: int
    total_vendas: float

    @property
    def saldo(self):
        return round(self.valor_inicial + self.total_vendas, 2)


def _caixa_aberto(conn):
    return conn.execute("""
        SELECT id, valor_inicial, datetime(data_abertura, 'localtime') AS data_abertura
        FROM caixa
        WHERE status = ?
    """, (ABERTO,)).fetchone()


def _resumir(conn, caixa):
    vendas = conn.execute("""
        SELECT COUNT(*) AS quantidade, COALESCE(SUM(valor_total), 0) AS total
        FROM vendas
        WHERE caixa_id = ?
    """, (caixa["id"],)).fetchone()

    return ResumoCaixa(
        id_caixa=caixa["id"],
        data_abertura=caixa["data_abertura"],
        valor_inicial=caixa["valor_inicial"],
        quantidade_vendas=vendas["quantidade"],
        total_vendas=round(vendas["total"], 2),
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


def resumo_caixa_aberto():
    """Situação do caixa aberto até agora (para a opção 'Status do caixa')."""
    with conexao() as conn:
        caixa = _caixa_aberto(conn)
        if caixa is None:
            raise ErroPDV("Nenhum caixa está aberto.")
        return _resumir(conn, caixa)


def fechar_caixa():
    with conexao() as conn:
        caixa = _caixa_aberto(conn)
        if caixa is None:
            raise ErroPDV("Nenhum caixa está aberto.")

        resumo = _resumir(conn, caixa)

        conn.execute("""
            UPDATE caixa
            SET valor_final = ?, data_fechamento = CURRENT_TIMESTAMP, status = ?
            WHERE id = ?
        """, (resumo.saldo, FECHADO, caixa["id"]))

    return resumo
