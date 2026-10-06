"""Consultas gerenciais de estoque, compras e rentabilidade bruta."""

from dataclasses import dataclass
from datetime import date, timedelta

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.precificacao import calcular_rentabilidade


ORDENACOES_PRODUTOS = {
    "nome": "nome COLLATE NOCASE ASC",
    "recentes": "data_cadastro DESC",
    "preco_maior": "preco DESC",
    "preco_menor": "preco ASC",
    "custo_maior": "custo_medio DESC",
    "custo_menor": "custo_medio ASC",
    "lucro_maior": "lucro_bruto_unitario DESC",
    "lucro_menor": "lucro_bruto_unitario ASC",
    "margem_maior": "margem_bruta_percentual DESC",
    "margem_menor": "margem_bruta_percentual ASC",
    "estoque_maior": "estoque DESC",
    "estoque_menor": "estoque ASC",
}

FILTROS_PRODUTOS = (None, "parados", "recentes", "sem_custo")


@dataclass(frozen=True)
class ResumoRentabilidade:
    faturamento_total: float
    faturamento_com_custo: float
    custo_das_mercadorias: float
    lucro_bruto: float
    margem_bruta_percentual: float
    unidades_sem_custo: int


@dataclass(frozen=True)
class ResumoPotencialEstoque:
    faturamento_potencial: float
    custo_estimado: float
    lucro_bruto_potencial: float
    margem_bruta_percentual: float
    produtos_sem_custo: int


def listar_produtos_gestao(
    filtro=None,
    ordenar_por="nome",
    dias_sem_movimentacao=30,
    hoje=None,
):
    """Lista produtos ativos com custo, rentabilidade e atividade recente."""
    if filtro not in FILTROS_PRODUTOS:
        raise ErroPDV("Filtro de produtos inválido.")
    if ordenar_por not in ORDENACOES_PRODUTOS:
        raise ErroPDV("Ordenação de produtos inválida.")
    if dias_sem_movimentacao <= 0:
        raise ErroPDV("O período sem movimentação deve ser maior que zero.")

    hoje = hoje or date.today()
    data_limite = (hoje - timedelta(days=dias_sem_movimentacao)).isoformat()
    consulta = """
        WITH atividade AS (
            SELECT
                p.*,
                (
                    SELECT MAX(date(m.data_movimentacao, 'localtime'))
                    FROM movimentacoes_estoque m
                    WHERE m.produto_id = p.id AND m.quantidade != 0
                ) AS ultima_movimentacao
            FROM produtos p
            WHERE p.ativo = 1
        ), produtos_gerenciais AS (
            SELECT *,
                COALESCE(ultima_movimentacao, date(data_cadastro, 'localtime'))
                    AS ultima_atividade,
                CASE
                    WHEN custo_medio IS NULL THEN NULL
                    ELSE ROUND(preco - custo_medio, 2)
                END AS lucro_bruto_unitario,
                CASE
                    WHEN custo_medio IS NULL OR preco = 0 THEN NULL
                    ELSE ROUND((preco - custo_medio) / preco * 100, 2)
                END AS margem_bruta_percentual
            FROM atividade
        )
        SELECT * FROM produtos_gerenciais
    """
    condicoes = []
    parametros = []

    if filtro == "parados":
        condicoes.extend(("estoque > 0", "ultima_atividade <= ?"))
        parametros.append(data_limite)
    elif filtro == "recentes":
        condicoes.append("date(data_cadastro, 'localtime') >= ?")
        parametros.append(data_limite)
    elif filtro == "sem_custo":
        condicoes.append("custo_medio IS NULL")

    if condicoes:
        consulta += " WHERE " + " AND ".join(condicoes)

    consulta += f" ORDER BY {ORDENACOES_PRODUTOS[ordenar_por]}, nome COLLATE NOCASE, id"

    with conexao() as conn:
        produtos = conn.execute(consulta, parametros).fetchall()

    resultado = []
    for produto in produtos:
        item = dict(produto)
        rentabilidade = calcular_rentabilidade(item["preco"], item["custo_medio"])
        item["lucro_bruto_unitario"] = (
            None if rentabilidade is None else rentabilidade.lucro_bruto_unitario
        )
        item["margem_bruta_percentual"] = (
            None if rentabilidade is None else rentabilidade.margem_bruta_percentual
        )
        item["acrescimo_sobre_custo_percentual"] = (
            None if rentabilidade is None
            else rentabilidade.acrescimo_sobre_custo_percentual
        )
        item["lucro_bruto_potencial"] = (
            None if rentabilidade is None
            else round(rentabilidade.lucro_bruto_unitario * item["estoque"], 2)
        )
        resultado.append(item)

    return resultado


def listar_compras(fornecedor=None, referencia=None, inicio=None, fim=None):
    """Lista itens de compras pesquisáveis por fornecedor, referência e data."""
    if inicio and fim and inicio > fim:
        raise ErroPDV("A data inicial não pode ser depois da data final.")

    consulta = """
        SELECT
            c.id AS compra_id,
            c.fornecedor,
            c.referencia,
            datetime(c.data_compra, 'localtime') AS data_compra,
            c.observacao AS observacao_compra,
            p.id AS produto_id,
            p.nome AS produto,
            m.quantidade,
            m.custo_unitario,
            ROUND(m.quantidade * m.custo_unitario, 2) AS total_item
        FROM compras c
        JOIN movimentacoes_estoque m ON m.compra_id = c.id AND m.tipo = 'ENTRADA'
        JOIN produtos p ON p.id = m.produto_id
        WHERE 1 = 1
    """
    parametros = []

    if fornecedor:
        consulta += " AND c.fornecedor LIKE ? COLLATE NOCASE"
        parametros.append(f"%{fornecedor.strip()}%")
    if referencia:
        consulta += " AND c.referencia LIKE ? COLLATE NOCASE"
        parametros.append(f"%{referencia.strip()}%")
    if inicio:
        consulta += " AND date(c.data_compra, 'localtime') >= ?"
        parametros.append(inicio.isoformat())
    if fim:
        consulta += " AND date(c.data_compra, 'localtime') <= ?"
        parametros.append(fim.isoformat())

    consulta += " ORDER BY c.data_compra DESC, c.id DESC, p.nome COLLATE NOCASE"

    with conexao() as conn:
        return conn.execute(consulta, parametros).fetchall()


def resumo_rentabilidade(periodo):
    """Calcula lucro bruto de vendas no período; custos desconhecidos não viram zero."""
    with conexao() as conn:
        linha = conn.execute("""
            SELECT
                ROUND(COALESCE(SUM(i.quantidade * i.valor_unitario), 0), 2)
                    AS faturamento_total,
                ROUND(COALESCE(SUM(CASE WHEN i.custo_unitario IS NOT NULL
                    THEN i.quantidade * i.valor_unitario ELSE 0 END), 0), 2)
                    AS faturamento_com_custo,
                ROUND(COALESCE(SUM(i.quantidade * i.custo_unitario), 0), 2)
                    AS custo_das_mercadorias,
                SUM(CASE WHEN i.custo_unitario IS NULL
                    THEN i.quantidade ELSE 0 END) AS unidades_sem_custo
            FROM itens_vendas i
            JOIN vendas v ON v.id = i.venda_id
            WHERE date(v.data, 'localtime') BETWEEN ? AND ?
        """, periodo.parametros).fetchone()

    lucro_bruto = round(
        linha["faturamento_com_custo"] - linha["custo_das_mercadorias"], 2
    )
    margem_bruta = 0
    if linha["faturamento_com_custo"]:
        margem_bruta = round(
            lucro_bruto / linha["faturamento_com_custo"] * 100, 2
        )

    return ResumoRentabilidade(
        faturamento_total=linha["faturamento_total"],
        faturamento_com_custo=linha["faturamento_com_custo"],
        custo_das_mercadorias=linha["custo_das_mercadorias"],
        lucro_bruto=lucro_bruto,
        margem_bruta_percentual=margem_bruta,
        unidades_sem_custo=linha["unidades_sem_custo"] or 0,
    )


def resumo_potencial_estoque():
    """Calcula faturamento e lucro bruto potencial do estoque ativo com custo conhecido."""
    with conexao() as conn:
        linha = conn.execute("""
            SELECT
                ROUND(COALESCE(SUM(CASE WHEN custo_medio IS NOT NULL
                    THEN estoque * preco ELSE 0 END), 0), 2) AS faturamento,
                ROUND(COALESCE(SUM(CASE WHEN custo_medio IS NOT NULL
                    THEN estoque * custo_medio ELSE 0 END), 0), 2) AS custo,
                SUM(CASE WHEN estoque > 0 AND custo_medio IS NULL
                    THEN 1 ELSE 0 END) AS produtos_sem_custo
            FROM produtos
            WHERE ativo = 1 AND estoque > 0
        """).fetchone()

    lucro_bruto = round(linha["faturamento"] - linha["custo"], 2)
    margem_bruta = 0
    if linha["faturamento"]:
        margem_bruta = round(lucro_bruto / linha["faturamento"] * 100, 2)

    return ResumoPotencialEstoque(
        faturamento_potencial=linha["faturamento"],
        custo_estimado=linha["custo"],
        lucro_bruto_potencial=lucro_bruto,
        margem_bruta_percentual=margem_bruta,
        produtos_sem_custo=linha["produtos_sem_custo"] or 0,
    )