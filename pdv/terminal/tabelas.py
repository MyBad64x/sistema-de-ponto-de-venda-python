"""Tabelas exibidas no terminal."""

from pdv.terminal.utilitarios import cortar, dinheiro


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


def mostrar_resumo_caixa(resumo, titulo):
    print("\n" + "=" * 50)
    print(titulo)
    print("=" * 50)
    print(f"Caixa         : #{resumo.id_caixa} (aberto em {resumo.data_abertura})")
    print(f"Valor inicial : {dinheiro(resumo.valor_inicial)}")
    print(f"Vendas        : {resumo.quantidade_vendas} ({dinheiro(resumo.total_vendas)})")
    print(f"Saldo         : {dinheiro(resumo.saldo)}")
    print("=" * 50)
