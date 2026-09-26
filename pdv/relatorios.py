"""Relatórios de vendas por período.

As vendas são gravadas em UTC. Por isso os filtros usam date(v.data, 'localtime'):
converte para o horário do computador antes de pegar só a data. Sem isso, uma
venda das 22h em Brasília (01h do dia seguinte em UTC) cairia no dia errado.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from pdv.banco import conexao
from pdv.erros import ErroPDV


@dataclass(frozen=True)
class Periodo:
    inicio: date
    fim: date

    def __post_init__(self):
        if self.inicio > self.fim:
            raise ErroPDV("A data inicial não pode ser depois da data final.")

    @property
    def parametros(self):
        """As duas datas no formato do SQLite: ('2026-09-01', '2026-09-26')."""
        return (self.inicio.isoformat(), self.fim.isoformat())


# O parâmetro "hoje" existe para os testes poderem fixar a data
# No uso normal ele fica vazio e vale a data de hoje do computador.


def periodo_hoje(hoje=None):
    hoje = hoje or date.today()
    return Periodo(hoje, hoje)


def periodo_ultimos_dias(dias, hoje=None):
    hoje = hoje or date.today()
    return Periodo(hoje - timedelta(days=dias - 1), hoje)


def periodo_mes_atual(hoje=None):
    hoje = hoje or date.today()
    return Periodo(hoje.replace(day=1), hoje)


@dataclass
class ResumoVendas:
    periodo: Periodo
    por_forma: list  # linhas como forma_pagamento, quantidade e total

    @property
    def quantidade_vendas(self):
        return sum(linha["quantidade"] for linha in self.por_forma)

    @property
    def total(self):
        return round(sum(linha["total"] for linha in self.por_forma), 2)

    @property
    def ticket_medio(self):
        """Valor Médio por venda."""
        if self.quantidade_vendas == 0:
            return 0
        return round(self.total / self.quantidade_vendas, 2)


def resumo_vendas(periodo):
    with conexao() as conn:
        linhas = conn.execute("""
            SELECT
                v.forma_pagamento,
                COUNT(*) AS quantidade,
                ROUND(SUM(v.valor_total), 2) AS total
            FROM vendas v
            WHERE date(v.data, 'localtime') BETWEEN ? AND ?
            GROUP BY v.forma_pagamento
            ORDER BY total DESC
        """, periodo.parametros).fetchall()

    return ResumoVendas(periodo, linhas)


def produtos_mais_vendidos(periodo, limite=10):
    """Ranking por quantidade vendida.

    O faturamento usa o valor_unitario gravado em itens_vendas, ou seja, o preço
    do momento da venda. Se o preço do produto mudar depois, o relatório não muda.
    """
    with conexao() as conn:
        return conn.execute("""
            SELECT
                p.id,
                p.nome,
                SUM(i.quantidade) AS quantidade,
                ROUND(SUM(i.quantidade * i.valor_unitario), 2) AS faturamento
            FROM itens_vendas i
            JOIN vendas v ON v.id = i.venda_id
            JOIN produtos p ON p.id = i.produto_id
            WHERE date(v.data, 'localtime') BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY quantidade DESC, faturamento DESC
            LIMIT ?
        """, (*periodo.parametros, limite)).fetchall()


def vendas_por_dia(periodo):
    """Uma linha por dia que teve venda, do mais antigo para o mais recente."""
    with conexao() as conn:
        return conn.execute("""
            SELECT
                date(v.data, 'localtime') AS dia,
                COUNT(*) AS quantidade,
                ROUND(SUM(v.valor_total), 2) AS total
            FROM vendas v
            WHERE date(v.data, 'localtime') BETWEEN ? AND ?
            GROUP BY dia
            ORDER BY dia
        """, periodo.parametros).fetchall()
