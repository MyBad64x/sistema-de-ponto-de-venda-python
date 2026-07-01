from caixa import caixa_aberto

carrinho = []

from produtos import buscar_produto

#função para adicionar item no carrinho de compras
def adicionar_item(id_produto, quantidade):

    if caixa_aberto() is None:
        print("Abra o caixa antes de iniciar uma venda!")
        return

    produto = buscar_produto(id_produto)

    if produto is None:
        print("Produto não encontrado!")
        return
    
    carrinho.append((id_produto, quantidade))

    print(f"{produto[1]} adicionado ao carrinho!")

#função para listar os itens que estão adicionados ou não no carrinho de compras
def listar_itens():
    if len(carrinho) == 0:
        print("Carrinho vazio!")
        return
    
    total = 0
    
    print("\n" + "=" * 80)
    print("CARRINHO")
    print("=" * 80)

    print(
        f"{'ID':<5}"
        f"| {'PRODUTO':<25}"
        f"| {'QTD':<5}"
        f"| {'UNITÁRIO':<12}"
        f"| {'SUBTOTAL':<12}"
    )

    print("=" * 80)

    for id_produto, quantidade in carrinho:

        produto = buscar_produto(id_produto)

        subtotal = produto[2] * quantidade

        total += subtotal

        print(
            f"{id_produto:<5}"
            f"| {produto[1]:<25}"
            f"| {quantidade:<5}"
            f"| R$ {produto[2]:<8.2f}"
            f"| R$ {subtotal:<8.2f}"
        )

    print("=" * 80)
    print(f"TOTAL DO CARRINHO: R$ {total:.2f}")
    print("=" * 80)

#função para limpar o carrinho
def limpar_carrinho():

    carrinho.clear()

    print("Carrinho limpo!")


def obter_carrinho():
    return carrinho