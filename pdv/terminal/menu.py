"""Menus do terminal.

Cada menu é uma lista de opções (tecla, descrição, função). A função
executar_menu cuida do que é igual em todos: limpar a tela, mostrar o
cabeçalho, ler a opção, mostrar erros e pausar. Assim cada ação só precisa
se preocupar com o que ela faz.
"""

from pdv import NOME_SISTEMA, VERSAO
from pdv.caixa import (
    abrir_caixa,
    detalhar_caixa,
    fechar_caixa,
    listar_caixas,
    registrar_sangria,
    registrar_suprimento,
    resumo_caixa_aberto,
)
from pdv.carrinho import Carrinho
from pdv.erros import ErroPDV, EstoqueInsuficiente
from pdv.estoque import ajustar_estoque, entrada_estoque
from pdv.movimentacoes import listar_movimentacoes
from pdv.produtos import (
    ativar_produto,
    buscar_produto,
    cadastrar_produto,
    desativar_produto,
    editar_produto,
    listar_produtos,
)
from pdv.terminal.tabelas import (
    mostrar_carrinho,
    mostrar_historico_caixas,
    mostrar_movimentacoes,
    mostrar_produtos,
    mostrar_resumo_caixa,
)
from pdv.terminal.utilitarios import (
    cabecalho,
    confirmar,
    dinheiro,
    escolher,
    ler_decimal,
    ler_inteiro,
    ler_texto,
    limpar_tela,
    mostrar_opcoes,
    pausar,
)
from pdv.vendas import FORMAS_PAGAMENTO, finalizar_venda

# a venda em andamento (fica na memória até ser finalizada)
carrinho = Carrinho()

MOVIMENTACOES_NA_TELA = 50

CAIXAS_NA_TELA = 20


def executar_menu(titulo, opcoes, texto_sair="Voltar", pausar_apos_acao=True):
    acoes = {tecla: acao for tecla, _, acao in opcoes}

    while True:
        limpar_tela()
        cabecalho(titulo)
        mostrar_opcoes([(tecla, descricao) for tecla, descricao, _ in opcoes])
        mostrar_opcoes([("0", texto_sair)])

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "0":
            return

        acao = acoes.get(opcao)

        if acao is None:
            print("\nOpção inválida.")
            pausar()
            continue

        try:
            acao()
        except ErroPDV as erro:
            print(f"\n{erro}")
            pausar()
            continue

        if pausar_apos_acao:
            pausar()


# ---------------------------------------------------------------- menu principal

def menu_principal():
    executar_menu(
        f"{NOME_SISTEMA} - v{VERSAO}",
        [
            ("1", "Produtos", menu_produtos),
            ("2", "Vendas", menu_vendas),
            ("3", "Estoque", menu_estoque),
            ("4", "Caixa", menu_caixa),
        ],
        texto_sair="Sair",
        # as opções do menu principal abrem submenus; ao voltar deles não precisa pausar
        pausar_apos_acao=False,
    )
    print("\nEncerrando o sistema...")


def menu_produtos():
    executar_menu("PRODUTOS", [
        ("1", "Cadastrar produto", cadastrar),
        ("2", "Listar produtos", listar),
        ("3", "Editar produto", editar),
        ("4", "Desativar produto", desativar),
        ("5", "Reativar produto", reativar),
    ])


def menu_vendas():
    executar_menu("VENDAS", [
        ("1", "Adicionar produto ao carrinho", adicionar_ao_carrinho),
        ("2", "Ver carrinho", ver_carrinho),
        ("3", "Finalizar venda", finalizar),
        ("4", "Limpar carrinho", limpar),
        ("5", "Remover item do carrinho", remover_do_carrinho),
    ])


def menu_estoque():
    executar_menu("ESTOQUE", [
        ("1", "Entrada de estoque", entrada),
        ("2", "Ajuste de estoque", ajuste),
        ("3", "Movimentações", movimentacoes),
    ])


def menu_caixa():
    executar_menu("CAIXA", [
        ("1", "Abrir caixa", abrir),
        ("2", "Fechar caixa", fechar),
        ("3", "Status do caixa", status),
        ("4", "Sangria", sangria),
        ("5", "Suprimento", suprimento),
        ("6", "Histórico de caixas", historico),
    ])


# ---------------------------------------------------------------- produtos

def cadastrar():
    nome = ler_texto("\nNome do produto: ")
    preco = ler_decimal("Preço: R$ ", minimo=0)
    estoque = ler_inteiro("Estoque inicial: ", minimo=0)

    id_produto = cadastrar_produto(nome, preco, estoque)
    print(f"\nProduto '{nome}' cadastrado com o ID {id_produto}.")


def listar():
    mostrar_produtos(listar_produtos())


def _pedir_produto(mensagem="\nID do produto: "):
    id_produto = ler_inteiro(mensagem, minimo=1)
    produto = buscar_produto(id_produto)
    if produto is None:
        raise ErroPDV(f"Produto {id_produto} não encontrado.")
    return produto


def editar():
    mostrar_produtos(listar_produtos())
    produto = _pedir_produto()

    print("\n(ENTER mantém o valor atual)")
    nome = ler_texto(f"Nome [{produto['nome']}]: ", padrao=produto["nome"])
    preco = ler_decimal(
        f"Preço [{dinheiro(produto['preco'])}]: R$ ", minimo=0, padrao=produto["preco"]
    )

    editar_produto(produto["id"], nome, preco)
    print(f"\nProduto '{nome}' atualizado.")
    print("Para mudar o estoque, use Estoque > Entrada ou Ajuste.")


def desativar():
    mostrar_produtos(listar_produtos())
    produto = _pedir_produto("\nID do produto que deseja desativar: ")

    if confirmar(f"Desativar '{produto['nome']}'?"):
        desativar_produto(produto["id"])
        print(f"\nProduto '{produto['nome']}' desativado.")


def reativar():
    inativos = [p for p in listar_produtos(incluir_inativos=True) if not p["ativo"]]

    if not inativos:
        print("\nNão há produtos desativados.")
        return

    mostrar_produtos(inativos)
    produto = _pedir_produto("\nID do produto que deseja reativar: ")
    ativar_produto(produto["id"])
    print(f"\nProduto '{produto['nome']}' reativado.")


# ---------------------------------------------------------------- vendas

def adicionar_ao_carrinho():
    mostrar_produtos(listar_produtos())
    id_produto = ler_inteiro("\nID do produto: ", minimo=1)
    quantidade = ler_inteiro("Quantidade: ", minimo=1)

    item = carrinho.adicionar(id_produto, quantidade)
    print(f"\n{item.nome} no carrinho: {item.quantidade} un. ({dinheiro(item.subtotal)})")

    if item.quantidade > item.estoque:
        print(f"Atenção: só há {item.estoque} em estoque.")


def ver_carrinho():
    mostrar_carrinho(carrinho.detalhar(), carrinho.total())


def remover_do_carrinho():
    ver_carrinho()
    if carrinho.esta_vazio():
        return
    id_produto = ler_inteiro("\nID do produto a remover: ", minimo=1)
    carrinho.remover(id_produto)
    print("\nItem removido.")


def finalizar():
    if carrinho.esta_vazio():
        raise ErroPDV("O carrinho está vazio.")

    ver_carrinho()
    print("\nForma de pagamento:")
    forma_pagamento = escolher("Escolha: ", FORMAS_PAGAMENTO)

    try:
        resultado = finalizar_venda(carrinho, forma_pagamento)
    except EstoqueInsuficiente as erro:
        print(f"\n{erro}")
        if not confirmar("Vender mesmo assim, deixando o estoque negativo?"):
            print("\nVenda não finalizada. O carrinho foi mantido.")
            return
        resultado = finalizar_venda(carrinho, forma_pagamento, permitir_estoque_negativo=True)

    print(f"\nVENDA #{resultado.id_venda} FINALIZADA")
    print(f"Total: {dinheiro(resultado.total)}")
    print(f"Pagamento: {resultado.forma_pagamento}")

    if resultado.estoques_negativos:
        print("\n=== ALERTA DE ESTOQUE ===")
        for nome, estoque in resultado.estoques_negativos:
            print(f"{nome} ficou com o estoque {estoque}")
        print("\nRegistre uma entrada ou ajuste de estoque.")


def limpar():
    if carrinho.esta_vazio():
        print("\nO carrinho já está vazio.")
    elif confirmar("\nLimpar o carrinho?"):
        carrinho.limpar()
        print("\nCarrinho limpo.")


# ---------------------------------------------------------------- estoque

def entrada():
    mostrar_produtos(listar_produtos())
    produto = _pedir_produto()
    quantidade = ler_inteiro("Quantidade: ", minimo=1)
    observacao = ler_texto("Observação: ", obrigatorio=False)

    resultado = entrada_estoque(produto["id"], quantidade, observacao)
    print(
        f"\nEntrada registrada: {resultado.nome_produto} "
        f"({resultado.estoque_anterior} -> {resultado.estoque_atual})"
    )


def ajuste():
    mostrar_produtos(listar_produtos())
    produto = _pedir_produto()
    novo_estoque = ler_inteiro(f"Estoque contado (atual {produto['estoque']}): ", minimo=0)
    observacao = ler_texto("Motivo do ajuste: ", obrigatorio=False)

    resultado = ajustar_estoque(produto["id"], novo_estoque, observacao)
    print(
        f"\nAjuste realizado: {resultado.nome_produto} "
        f"({resultado.estoque_anterior} -> {resultado.estoque_atual})"
    )


def movimentacoes():
    print(f"\nÚltimas {MOVIMENTACOES_NA_TELA} movimentações:")
    mostrar_movimentacoes(listar_movimentacoes(limite=MOVIMENTACOES_NA_TELA))


# ---------------------------------------------------------------- caixa

def abrir():
    valor = ler_decimal("\nValor inicial do caixa: R$ ", minimo=0)
    id_caixa = abrir_caixa(valor)
    print(f"\nCaixa #{id_caixa} aberto com {dinheiro(valor)}.")


def fechar():
    if not carrinho.esta_vazio():
        raise ErroPDV("Há itens no carrinho. Finalize a venda ou limpe o carrinho antes.")

    resumo_caixa_aberto()  # dá erro aqui mesmo se não houver caixa aberto

    if not confirmar("\nFechar o caixa?"):
        return

    # conferência "às cegas": o operador conta antes de ver quanto era esperado
    print("\nConte todo o dinheiro da gaveta (cédulas e moedas).")
    valor_contado = ler_decimal("Valor contado: R$ ", minimo=0)

    resumo = fechar_caixa(valor_contado)
    mostrar_resumo_caixa(resumo, "FECHAMENTO DE CAIXA")
    print("Caixa fechado com sucesso!")


def status():
    mostrar_resumo_caixa(resumo_caixa_aberto(), "STATUS DO CAIXA")


def _movimentar_gaveta(titulo, registrar):
    """Pede valor e motivo e chama registrar_sangria ou registrar_suprimento."""
    resumo = resumo_caixa_aberto()

    print(f"\n{titulo}")
    print(f"Dinheiro na gaveta agora: {dinheiro(resumo.dinheiro_esperado)}")

    valor = ler_decimal("Valor: R$ ", minimo=0.01)
    motivo = ler_texto("Motivo: ")

    resumo = registrar(valor, motivo)
    print(f"\nRegistrado. Dinheiro na gaveta: {dinheiro(resumo.dinheiro_esperado)}")


def sangria():
    _movimentar_gaveta("SANGRIA (retirada de dinheiro)", registrar_sangria)


def suprimento():
    _movimentar_gaveta("SUPRIMENTO (entrada de dinheiro)", registrar_suprimento)


def historico():
    print(f"\nÚltimos {CAIXAS_NA_TELA} caixas:")
    caixas = listar_caixas(limite=CAIXAS_NA_TELA)
    mostrar_historico_caixas(caixas)

    if not caixas:
        return

    id_caixa = ler_inteiro("\nID do caixa para ver o resumo (ENTER para voltar): ", minimo=0, padrao=0)

    if id_caixa != 0:
        mostrar_resumo_caixa(detalhar_caixa(id_caixa), f"RESUMO DO CAIXA #{id_caixa}")
