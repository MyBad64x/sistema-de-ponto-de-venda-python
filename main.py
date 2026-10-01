from pdv.banco import criar_tabelas
from pdv.terminal.menu import menu_login, menu_principal


def main():
    criar_tabelas()

    try:
        usuario = menu_login()
        if usuario is None:
            print("\nEncerrando o sistema...")
            return

        menu_principal(usuario)
    except (KeyboardInterrupt, EOFError):
        print("\n\nEncerrando o sistema...")


if __name__ == "__main__":
    main()