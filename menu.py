from produtos import (
    listar_produtos, 
    cadastrar_produto,
    desativar_produto,
    editar_produto,
    buscar_produto
)
from produtos import (
    entrada_estoque,
    ajustar_estoque,
)
from movimentacoes_estoque import listar_movimentacoes
from caixa import (
    abrir_caixa,
    caixa_aberto,
    fechar_caixa
)
from carrinho import (
    adicionar_item,
    listar_itens,
    limpar_carrinho
)
from vendas import finalizar_venda
#título com nome do sistema e versão atual
NOME_SISTEMA = "PDV Python"
VERSAO = "1.2.1"

#função para alterar o cabeçalho inteiro sem ficar catando código em cada função
def cabecalho(titulo):

    largura = 50

    print("\n" + "=" * largura)
    print(titulo.center(largura))
    print("=" * largura)

#função para otimizar o código de listagem
def mostrar_opcoes(opcoes):
    for numero, descricao in opcoes:
        print(f"{numero} - {descricao}")

#função do menu principal para selecionar onde entrar
def menu_principal():

    while True:

        #função do cabecalho
        cabecalho(f"{NOME_SISTEMA} - v{VERSAO}")

        mostrar_opcoes([
            ("1", "Produtos"),
            ("2", "Vendas"),
            ("3", "Estoque"),
            ("4", "Caixa"),
            ("0", "Sair")
        ])

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            menu_produtos()

        elif opcao == "2":
            menu_vendas()

        elif opcao == "3":
            menu_estoque()

        elif opcao == "4":
            menu_caixa()

        elif opcao == "0":
            print("\nEncerrando o sistema...")
            break

        else:
            print("\nOpção inválida!")


#função para o módulo de produtos (1)
def menu_produtos():

    while True:

        #funcao do cabecalho
        cabecalho("PRODUTOS")

        mostrar_opcoes([
            ("1", "Cadastrar produto"),
            ("2", "Listar produto"),
            ("3", "Editar produto"),
            ("4", "Inativar produto"),
            ("0", "Voltar")
        ])

        opcao = input("\nEscolha uma opção: ")
        #cadastrar produto
        if opcao == "1":
            nome = input("\nNome do produto: ")
            preco = float(input("Preço: R$ "))
            estoque = int(input("Estoque inicial: "))

            cadastrar_produto(
                nome,
                preco,
                estoque
            )
        #listar produtos
        elif opcao == "2":
            listar_produtos()
        #editar produto
        elif opcao == "3":
            id_produto = int(input("\nID do produto: "))

            produto = buscar_produto(id_produto)
            if produto is None:
                print("\nProduto não encontrado!")
                continue

            nome = input("Novo nome: ")
            preco = float(input("Novo preço: R$ "))
            estoque = int(input("Novo estoque: "))

            editar_produto(
                id_produto,
                nome,
                preco,
                estoque
            )
        #inativar produto
        elif opcao == "4":
            listar_produtos()
            id_produto = int(input("\nID do produto que deseja desativar: "))
            desativar_produto(id_produto)
        #voltar
        elif opcao == "0":
            break

        else:
            print("\nOpção inválida.")


#função para o modulo de vendas
def menu_vendas():

    while True:

        #funcao do cabecalho
        cabecalho("VENDAS")

        mostrar_opcoes([
            ("1", "Adcionar produto ao carrinho"),
            ("2", "Ver carrinho"),
            ("3", "Finalizar venda"),
            ("4", "Limpar carrinho"),
            ("0", "Voltar")
        ])

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            listar_produtos()
            
            id_produto = int(input("\nID do produto: "))
            produto = buscar_produto(id_produto)

            if produto is None:
                print("\nProduto não encontrado!")
                continue

            quantidade = int(input("Quantidade: "))

            adicionar_item(
                id_produto,
                quantidade
            )

        elif opcao == "2":
            listar_itens()

        elif opcao == "3":
            forma_pagamento = input("\nForma de pagamento: ")
            finalizar_venda(
                forma_pagamento
            )

        elif opcao == "4":
            limpar_carrinho()

        elif opcao == "0":
            break

        else:
            print("\nOpção inválida.")

#função para o módulo de estoque
def menu_estoque():

    while True:

        #funcao do cabecalho
        cabecalho("ESTOQUE")

        mostrar_opcoes([
            ("1", "Entrada de estoque"),
            ("2", "Ajuste de estoque"),
            ("3", "Movimentações"),
            ("0", "Voltar")
        ])

        opcao = input("\nEscolha uma opção: ")
        #entrada estoque
        if opcao == "1":
            listar_produtos()

            id_produto = int(input("\nID do produto: "))
            quantidade = int(input("\nQuantidade: "))
            observacao = input("\nObservação: ")

            entrada_estoque(
                id_produto,
                quantidade,
                observacao
            )
        #ajuste de estoque
        elif opcao == "2":
            listar_produtos()

            id_produto = int(input("\nID do produto: "))
            novo_estoque = int(input("Novo estoque: "))
            observacao = input("Observação: ")

            ajustar_estoque(
                id_produto,
                novo_estoque,
                observacao
            )
        #movimentações estoque
        elif opcao == "3":
            listar_movimentacoes()
        #voltar
        elif opcao == "0":
            break

        else:
            print("\nOpção inválida.")


#função do modulo de caixa
def menu_caixa():

    while True:

        #funcao do cabecalho
        cabecalho("CAIXA")

        mostrar_opcoes([
            ("1", "Abrir caixa"),
            ("2", "Fechar caixa"),
            ("3", "Status do caixa"),
            ("4", "Sangria"),
            ("5", "Suprimento"),
            ("6", "Histórico de caixas"),
            ("0", "Voltar")
        ])

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            valor = float(input("\nValor inicial do caixa: R$ "))
            abrir_caixa(valor)

        elif opcao == "2":
            fechar_caixa()

        elif opcao == "3":
            caixa = caixa_aberto()
            if caixa is None:
                print("\nNenhum caixa está aberto.")
            else:
                print(f"\nCaixa aberto (ID {caixa[0]}).")

        elif opcao == "4":
            print("\nEm desenvolvimento.")

        elif opcao == "5":
            print("\nEm desenvolvimento.")

        elif opcao == "6":
            print("\nEm desenvolvimento.")

        elif opcao == "0":
            break

        else:
            print("\nOpção inválida.")