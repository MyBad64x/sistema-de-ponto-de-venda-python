"""Funções de apoio para ler e mostrar dados no terminal."""

import os

LARGURA = 60


def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def pausar():
    """Evita que uma mensagem desapareça imediatamente ao voltar para o menu."""
    input("\nPressione ENTER para continuar...")


def cabecalho(titulo, largura=LARGURA):
    print("\n" + "=" * largura)
    print(titulo.center(largura))
    print("=" * largura)


def mostrar_opcoes(opcoes):
    for numero, descricao in opcoes:
        print(f"{numero} - {descricao}")


def cortar(texto, largura):
    """Encurta textos longos para não desalinhar as tabelas."""
    texto = str(texto)
    return texto if len(texto) <= largura else texto[: largura - 1] + "…"


def dinheiro(valor):
    """Formata no padrão brasileiro: 1234.5 -> 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _mensagem_minimo(minimo):
    if minimo == 0:
        return "O valor não pode ser negativo."
    if minimo == 1:
        return "O valor deve ser maior que zero."
    return f"O valor deve ser maior ou igual a {minimo}."


def _ler_numero(mensagem, converter, erro, minimo, maximo, padrao):
    while True:
        texto = input(mensagem).strip()

        # ENTER vazio mantém o valor atual (usado na edição)
        if texto == "" and padrao is not None:
            return padrao

        try:
            valor = converter(texto)
        except ValueError:
            print(f"\n{erro}")
            continue

        if minimo is not None and valor < minimo:
            print(f"\n{_mensagem_minimo(minimo)}")
            continue

        if maximo is not None and valor > maximo:
            print(f"\nO valor deve ser menor ou igual a {maximo}.")
            continue

        return valor


def ler_inteiro(mensagem, minimo=None, maximo=None, padrao=None):
    """Lê um número inteiro, repetindo a pergunta até receber um valor válido."""
    return _ler_numero(
        mensagem, int, "Digite um número inteiro válido.", minimo, maximo, padrao
    )


def ler_decimal(mensagem, minimo=None, maximo=None, padrao=None):
    """Lê um valor decimal. Aceita vírgula ou ponto: 12,50 ou 12.50."""
    return _ler_numero(
        mensagem,
        lambda texto: float(texto.replace(",", ".")),
        "Digite um número válido (ex.: 12,50).",
        minimo,
        maximo,
        padrao,
    )


def ler_texto(mensagem, obrigatorio=True, padrao=None):
    while True:
        texto = input(mensagem).strip()

        if texto == "" and padrao is not None:
            return padrao

        if texto or not obrigatorio:
            return texto

        print("\nEste campo não pode ficar vazio.")


def escolher(mensagem, opcoes):
    """Mostra uma lista numerada e devolve o item escolhido."""
    for numero, opcao in enumerate(opcoes, start=1):
        print(f"{numero} - {opcao}")

    indice = ler_inteiro(mensagem, minimo=1, maximo=len(opcoes))
    return opcoes[indice - 1]


def confirmar(mensagem):
    resposta = input(f"{mensagem} (s/n): ").strip().lower()
    return resposta in ("s", "sim")
