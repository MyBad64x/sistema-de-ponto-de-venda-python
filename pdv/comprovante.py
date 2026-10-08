"""Comprovante não fiscal de venda, exibido no terminal e salvo em arquivo.

Não é documento fiscal. O texto é montado por uma função pura (montar_texto),
que só recebe dados; buscar_venda lê do banco e salvar_comprovante grava o arquivo.
O comprovante também pode ser consultado pelo menu de vendas, usando os dados do banco.
Os arquivos ficam em database/comprovantes/, ao lado do loja.db.
"""

from pdv import NOME_SISTEMA
from pdv.banco import caminho_banco, conexao
from pdv.erros import ErroPDV

LARGURA = 40


def pasta_comprovantes():
    return caminho_banco().parent / "comprovantes"


def _dinheiro(valor):
    """1234.5 -> 'R$ 1.234,50' (o mesmo padrão do terminal, sem depender dele)."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _linha(esquerda, direita, largura):
    """Texto à esquerda e valor à direita, na mesma linha."""
    espaco = max(1, largura - len(esquerda) - len(direita))
    return esquerda + " " * espaco + direita


def _cortar(texto, largura):
    return texto if len(texto) <= largura else texto[: largura - 1] + "…"


def buscar_venda(id_venda):
    """Lê a venda e seus itens do banco. Devolve (venda, itens)."""
    with conexao() as conn:
        venda = conn.execute("""
            SELECT id, valor_total, forma_pagamento, valor_recebido, troco,
                   strftime('%d/%m/%Y %H:%M', data, 'localtime') AS data
            FROM vendas
            WHERE id = ?
        """, (id_venda,)).fetchone()

        if venda is None:
            raise ErroPDV(f"Venda {id_venda} não encontrada.")

        itens = conn.execute("""
            SELECT p.nome, i.quantidade, i.valor_unitario
            FROM itens_vendas i
            JOIN produtos p ON p.id = i.produto_id
            WHERE i.venda_id = ?
            ORDER BY i.id
        """, (id_venda,)).fetchall()

    return dict(venda), [dict(item) for item in itens]


def listar_comprovantes(id_venda=None, inicio=None, fim=None, forma_pagamento=None, limite=50):
    """Lista vendas para consulta de comprovantes, sem depender dos arquivos TXT."""
    if id_venda is not None and id_venda <= 0:
        raise ErroPDV("O número da venda deve ser maior que zero.")
    if inicio and fim and inicio > fim:
        raise ErroPDV("A data inicial não pode ser depois da data final.")
    if limite <= 0:
        raise ErroPDV("O limite de resultados deve ser maior que zero.")

    consulta = """
        SELECT
            id,
            strftime('%d/%m/%Y %H:%M', data, 'localtime') AS data,
            valor_total,
            forma_pagamento
        FROM vendas
        WHERE 1 = 1
    """
    parametros = []

    if id_venda is not None:
        consulta += " AND id = ?"
        parametros.append(id_venda)
    if inicio:
        consulta += " AND date(data, 'localtime') >= ?"
        parametros.append(inicio.isoformat())
    if fim:
        consulta += " AND date(data, 'localtime') <= ?"
        parametros.append(fim.isoformat())
    if forma_pagamento:
        consulta += " AND forma_pagamento = ?"
        parametros.append(forma_pagamento)

    consulta += " ORDER BY data DESC, id DESC LIMIT ?"
    parametros.append(limite)

    with conexao() as conn:
        return conn.execute(consulta, parametros).fetchall()


def montar_texto(venda, itens, largura=LARGURA):
    """Monta o texto do cupom. Não acessa o banco nem o disco."""
    borda = "=" * largura
    traco = "-" * largura

    linhas = [
        borda,
        NOME_SISTEMA.center(largura),
        "COMPROVANTE DE VENDA".center(largura),
        "(não é documento fiscal)".center(largura),
        borda,
        _linha(f"Venda #{venda['id']}", venda["data"], largura),
        traco,
    ]

    for item in itens:
        subtotal = round(item["quantidade"] * item["valor_unitario"], 2)
        linhas.append(_cortar(item["nome"], largura))
        linhas.append(_linha(
            f"  {item['quantidade']} x {_dinheiro(item['valor_unitario'])}",
            _dinheiro(subtotal),
            largura,
        ))

    linhas.append(traco)
    linhas.append(_linha("TOTAL", _dinheiro(venda["valor_total"]), largura))
    linhas.append(_linha("Pagamento", venda["forma_pagamento"], largura))

    if venda["troco"] is not None:
        linhas.append(_linha("Recebido", _dinheiro(venda["valor_recebido"]), largura))
        linhas.append(_linha("Troco", _dinheiro(venda["troco"]), largura))

    linhas += [borda, "Obrigado pela preferência!".center(largura), borda]

    return "\n".join(linhas) + "\n"


def gerar_comprovante(id_venda):
    """Texto do comprovante de uma venda já gravada."""
    venda, itens = buscar_venda(id_venda)
    return montar_texto(venda, itens)


def salvar_comprovante(id_venda):
    """Grava o comprovante em database/comprovantes/venda_000123.txt e devolve o caminho."""
    texto = gerar_comprovante(id_venda)

    pasta = pasta_comprovantes()
    pasta.mkdir(parents=True, exist_ok=True)

    caminho = pasta / f"venda_{id_venda:06d}.txt"
    caminho.write_text(texto, encoding="utf-8")
    return caminho