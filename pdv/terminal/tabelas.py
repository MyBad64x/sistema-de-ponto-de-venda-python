"""Tabelas exibidas no terminal."""

from pdv.terminal.utilitarios import cortar, data_br, dinheiro


def mostrar_produtos(produtos, mostrar_status=False):
    if not produtos:
        print("\nNenhum produto cadastrado.")
        return

    largura = 70 if mostrar_status else 60
    print("\n" + "=" * largura)
    cabecalho = f"{'ID':<5}| {'PRODUTO':<25}| {'PREÇO':<14}| {'ESTOQUE':<8}"
    if mostrar_status:
        cabecalho += "| STATUS"
    print(cabecalho)
    print("=" * largura)

    for produto in produtos:
        linha = (
            f"{produto['id']:<5}"
            f"| {cortar(produto['nome'], 24):<25}"
            f"| {dinheiro(produto['preco']):<14}"
            f"| {produto['estoque']:<8}"
        )
        if mostrar_status:
            linha += "| " + ("Ativo" if produto["ativo"] else "Inativo")
        print(linha)

    print("=" * largura)


def mostrar_produtos_gerenciais(produtos):
    if not produtos:
        print("\nNenhum produto encontrado.")
        return

    largura = 132
    print("\n" + "=" * largura)
    print(
        f"{'ID':<5}| {'PRODUTO':<22}| {'PREÇO':>12}| {'CUSTO':>12}| "
        f"{'LUCRO/UN.':>12}| {'MARGEM':>9}| {'ESTOQUE':>8}| ÚLTIMA ATIVIDADE"
    )
    print("=" * largura)

    for produto in produtos:
        custo = _dinheiro_ou_traco(produto["custo_medio"])
        lucro = _dinheiro_ou_traco(produto["lucro_bruto_unitario"])
        margem = (
            "-" if produto["margem_bruta_percentual"] is None
            else f"{produto['margem_bruta_percentual']:.2f}%"
        )
        atividade = produto["ultima_atividade"] or "sem data"
        print(
            f"{produto['id']:<5}| {cortar(produto['nome'], 21):<22}| "
            f"{dinheiro(produto['preco']):>12}| {custo:>12}| {lucro:>12}| "
            f"{margem:>9}| {produto['estoque']:>8}| {atividade}"
        )

    print("=" * largura)


def mostrar_compras(compras):
    if not compras:
        print("\nNenhuma compra encontrada.")
        return

    largura = 132
    print("\n" + "=" * largura)
    print(
        f"{'COMPRA':<8}| {'DATA':<17}| {'FORNECEDOR':<24}| {'REFERÊNCIA':<18}| "
        f"{'PRODUTO':<22}| {'QTD':>5}| {'CUSTO/UN.':>12}| TOTAL"
    )
    print("=" * largura)

    for compra in compras:
        print(
            f"{compra['compra_id']:<8}| {compra['data_compra']:<17}| "
            f"{cortar(compra['fornecedor'] or '-', 23):<24}| "
            f"{cortar(compra['referencia'] or '-', 17):<18}| "
            f"{cortar(compra['produto'], 21):<22}| {compra['quantidade']:>5}| "
            f"{_dinheiro_ou_traco(compra['custo_unitario']):>12}| "
            f"{_dinheiro_ou_traco(compra['total_item'])}"
        )

    print("=" * largura)


def mostrar_carrinho(itens, total):
    if not itens:
        print("\nCarrinho vazio.")
        return

    print("\n" + "=" * 72)
    print(f"{'ID':<5}| {'PRODUTO':<25}| {'QTD':<5}| {'UNITÁRIO':<14}| SUBTOTAL")
    print("=" * 72)

    for item in itens:
        print(
            f"{item.id_produto:<5}"
            f"| {cortar(item.nome, 24):<25}"
            f"| {item.quantidade:<5}"
            f"| {dinheiro(item.preco_unitario):<14}"
            f"| {dinheiro(item.subtotal)}"
        )

    print("=" * 72)
    print(f"TOTAL DO CARRINHO: {dinheiro(total)}")
    print("=" * 72)


def mostrar_movimentacoes(movimentacoes):
    if not movimentacoes:
        print("\nNenhuma movimentação encontrada.")
        return

    largura = 110
    print("\n" + "=" * largura)
    print(
        f"{'ID':<5}| {'PRODUTO':<25}| {'TIPO':<8}| {'QTD':<6}"
        f"| {'OBSERVAÇÃO':<35}| DATA"
    )
    print("=" * largura)

    for mov in movimentacoes:
        quantidade = f"{mov['quantidade']:+d}"  # +5 / -3
        print(
            f"{mov['id']:<5}"
            f"| {cortar(mov['produto'], 24):<25}"
            f"| {mov['tipo']:<8}"
            f"| {quantidade:<6}"
            f"| {cortar(mov['observacao'], 34):<35}"
            f"| {mov['data']}"
        )

    print("=" * largura)


def _linha_valor(rotulo, valor, observacao=""):
    print(f"  {rotulo:<22}{dinheiro(valor):>15}  {observacao}".rstrip())


def mostrar_resumo_caixa(resumo, titulo):
    print("\n" + "=" * 50)
    print(titulo)
    print("=" * 50)
    print(f"Caixa #{resumo.id_caixa} - aberto em {resumo.data_abertura}")

    print(f"\nVENDAS ({resumo.quantidade_vendas})")
    if not resumo.vendas_por_forma:
        print("  Nenhuma venda.")
    for forma, total in resumo.vendas_por_forma.items():
        _linha_valor(forma, total)
    _linha_valor("Total", resumo.total_vendas)

    print("\nDINHEIRO NA GAVETA")
    _linha_valor("Valor inicial", resumo.valor_inicial)
    _linha_valor("+ Vendas em dinheiro", resumo.vendas_dinheiro)
    _linha_valor("+ Suprimentos", resumo.suprimentos)
    _linha_valor("- Sangrias", resumo.sangrias)
    _linha_valor("= Esperado", resumo.dinheiro_esperado)

    if resumo.valor_contado is not None:
        if resumo.diferenca > 0:
            situacao = "SOBRA"
        elif resumo.diferenca < 0:
            situacao = "FALTA"
        else:
            situacao = "OK"

        _linha_valor("Contado", resumo.valor_contado)
        _linha_valor("Diferença", resumo.diferenca, situacao)

    print("=" * 50)


def _dinheiro_ou_traco(valor):
    return "-" if valor is None else dinheiro(valor)


def mostrar_historico_caixas(caixas):
    if not caixas:
        print("\nNenhum caixa registrado.")
        return

    largura = 104
    print("\n" + "=" * largura)
    print(
        f"{'ID':<5}| {'ABERTURA':<17}| {'FECHAMENTO':<17}| {'VENDAS':<7}"
        f"| {'TOTAL VENDAS':<14}| {'ESPERADO':<14}| {'CONTADO':<14}| DIFERENÇA"
    )
    print("=" * largura)

    for caixa in caixas:
        print(
            f"{caixa['id']:<5}"
            f"| {caixa['abertura']:<17}"
            f"| {caixa['fechamento'] or 'ABERTO':<17}"
            f"| {caixa['quantidade_vendas']:<7}"
            f"| {dinheiro(caixa['total_vendas']):<14}"
            f"| {_dinheiro_ou_traco(caixa['esperado']):<14}"
            f"| {_dinheiro_ou_traco(caixa['contado']):<14}"
            f"| {_dinheiro_ou_traco(caixa['diferenca'])}"
        )

    print("=" * largura)


def mostrar_resumo_vendas(resumo):
    if resumo.quantidade_vendas == 0:
        print("\nNenhuma venda no período.")
        return

    print("\n" + "=" * 60)
    print(f"{'FORMA DE PAGAMENTO':<22}| {'VENDAS':<7}| {'TOTAL':<15}| %")
    print("=" * 60)

    for linha in resumo.por_forma:
        percentual = f"{linha['total'] / resumo.total * 100:.1f}%".replace(".", ",")
        print(
            f"{linha['forma_pagamento']:<22}"
            f"| {linha['quantidade']:<7}"
            f"| {dinheiro(linha['total']):<15}"
            f"| {percentual}"
        )

    print("=" * 60)
    print(f"Vendas       : {resumo.quantidade_vendas}")
    print(f"Total        : {dinheiro(resumo.total)}")
    print(f"Ticket médio : {dinheiro(resumo.ticket_medio)}")
    print("=" * 60)


def mostrar_produtos_mais_vendidos(ranking):
    if not ranking:
        print("\nNenhuma venda no período.")
        return

    print("\n" + "=" * 60)
    print(f"{'#':<4}| {'PRODUTO':<25}| {'QTD':<8}| FATURAMENTO")
    print("=" * 60)

    for posicao, linha in enumerate(ranking, start=1):
        print(
            f"{posicao:<4}"
            f"| {cortar(linha['nome'], 24):<25}"
            f"| {linha['quantidade']:<8}"
            f"| {dinheiro(linha['faturamento'])}"
        )

    print("=" * 60)


def mostrar_vendas_por_dia(dias, largura_barra=30):
    if not dias:
        print("\nNenhuma venda no período.")
        return

    maior_total = max(linha["total"] for linha in dias)

    print("\n" + "=" * 75)
    print(f"{'DIA':<12}| {'VENDAS':<7}| {'TOTAL':<15}|")
    print("=" * 75)

    for linha in dias:
        # a barra do maior dia ocupa a largura toda; as outras são proporcionais
        tamanho = round(linha["total"] / maior_total * largura_barra) if maior_total > 0 else 0
        print(
            f"{data_br(linha['dia']):<12}"
            f"| {linha['quantidade']:<7}"
            f"| {dinheiro(linha['total']):<15}"
            f"| {'█' * tamanho}"
        )

    print("=" * 75)


def mostrar_backups(backups):
    if not backups:
        print("\nNenhum backup encontrado.")
        return

    print("\n" + "=" * 70)
    print(f"{'#':<4}| {'DATA':<17}| {'TAMANHO':<11}| ARQUIVO")
    print("=" * 70)

    for numero, backup in enumerate(backups, start=1):
        print(
            f"{numero:<4}"
            f"| {backup.criado_em:%d/%m/%Y %H:%M} "
            f"| {backup.tamanho_kb:>7} KB "
            f"| {backup.caminho.name}"
        )

    print("=" * 70)
