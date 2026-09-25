from pdv.banco import criar_tabelas
from pdv.terminal.menu import menu_principal


def main():
    criar_tabelas()

    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou fim da entrada: sai sem mostrar erro na tela
        print("\n\nEncerrando o sistema...")


if __name__ == "__main__":
    main()
