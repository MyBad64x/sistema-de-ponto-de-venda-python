import os
#limpa o terminal
def limpar_tela():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

#evita que uma mensagem desapareça imediatamente ao voltar para o menu.
def pausar():
    input("\nPressione ENTER para continuar...")

#impede ValueError ao digitar letras.
def ler_inteiro(
        mensagem,
        minimo=None,
        maximo=None
):
    while True:
        try:
            valor = int(input(mensagem))

            if minimo is not None and valor < minimo:
                
                if minimo == 0:
                    print("\nO valor não pode ser negativo.")
                elif minimo == 1:
                    print("\nO valor deve ser maior que zero.")
                else:
                    print(f"\nO valor deve ser maior ou igual a {minimo}.")

                continue

            if maximo is not None and valor > maximo:
                print(f"\nO valor deve ser menor ou igual a {maximo}.")
                continue

            return valor
        
        except ValueError:
            print("\nDigite um número inteiro válido.")

#faz o mesmo para valores como preço.
def ler_decimal(
        mensagem,
        minimo=None,
        maximo=None
):
    while True:
        try:
            valor = float(input(mensagem))

            if minimo is not None and valor < minimo:

                if minimo == 0:
                    print("\nO valor não pode ser negativo.")
                elif minimo == 1:
                    print("\nO valor deve ser maior que zero.")
                else:
                    print(f"\nO valor deve ser maior ou igual a {minimo}.")

                continue

            if maximo is not None and valor > maximo:
                print(f"\nO valor deve ser menor ou igual a {maximo}.")
                continue

            return valor
        
        except ValueError:
            print("\nDigite um número válido.")