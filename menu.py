#título com nome do sistema e versão atual
NOME_SISTEMA = "PDV Python"
VERSAO = "1.2.0"

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

        if opcao == "1":
            print("\nEm desenvolvimento.")

        elif opcao == "2":
            print("\nEm desenvolvimento.")

        elif opcao == "3":
            print("\nEm desenvolvimento.")

        elif opcao == "4":
            print("\nEm desenvolvimento.")

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
            print("\nEm desenvolvimento.")

        elif opcao == "2":
            print("\nEm desenvolvimento.")

        elif opcao == "3":
            print("\nEm desenvolvimento.")

        elif opcao == "4":
            print("\nEm desenvolvimento.")

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

        if opcao == "1":
            print("\nEm desenvolvimento.")

        elif opcao == "2":
            print("\nEm desenvolvimento.")

        elif opcao == "3":
            print("\nEm desenvolvimento.")

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
            print("\nEm desenvolvimento.")

        elif opcao == "2":
            print("\nEm desenvolvimento.")

        elif opcao == "3":
            print("\nEm desenvolvimento.")

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