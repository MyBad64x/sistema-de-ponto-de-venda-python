NOME_SISTEMA = "PDV Python"
VERSAO = "1.1.0"

print("\n" + "=" * 40)
print(f"{NOME_SISTEMA} - v{VERSAO}".center(40))
print("=" * 40)

def menu_principal():

    while True:

        print("\n" + "=" * 40)
        print("         PDV PYTHON")
        print("=" * 40)

        print("1 - Produtos")
        print("2 - Vendas")
        print("3 - Estoque")
        print("4 - Caixa")
        print("0 - Sair")

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            print("\nMódulo de Produtos em desenvolvimento.")

        elif opcao == "2":
            print("\nMódulo de Vendas em desenvolvimento.")

        elif opcao == "3":
            print("\nMódulo de Estoque em desenvolvimento.")

        elif opcao == "4":
            print("\nMódulo de Caixa em desenvolvimento.")

        elif opcao == "0":
            print("\nEncerrando o sistema...")
            break

        else:
            print("\nOpção inválida!")