"""Menus do terminal.

Cada menu é uma lista de opções (tecla, descrição, função). A função
executar_menu cuida do que é igual em todos: limpar a tela, mostrar o
cabeçalho, ler a opção, mostrar erros e pausar. Assim cada ação só precisa
se preocupar com o que ela faz.
"""

from getpass import getpass
from datetime import datetime

from pdv import NOME_SISTEMA, VERSAO
from pdv.banco import conexao
from pdv.backup import fazer_backup, listar_backups, restaurar_backup
from pdv.caixa import (
    DINHEIRO,
    abrir_caixa,
    detalhar_caixa,
    fechar_caixa,
    listar_caixas,
    registrar_sangria,
    registrar_suprimento,
    resumo_caixa_aberto,
)
from pdv.carrinho import Carrinho
from pdv.comprovante import gerar_comprovante, salvar_comprovante
from pdv.erros import ErroPDV, EstoqueInsuficiente
from pdv.gestao import (
    listar_compras,
    listar_produtos_gestao,
    resumo_potencial_estoque,
    resumo_rentabilidade,
)
from pdv.estoque import (
    ajustar_estoque,
    ajustar_estoque_em_lote,
    registrar_compra as registrar_compra_estoque,
)
from pdv.movimentacoes import listar_movimentacoes
from pdv.produtos import (
    ativar_produto,
    buscar_produto,
    buscar_produto_por_codigo_barras,
    buscar_produtos_por_nome,
    cadastrar_produto,
    desativar_produto,
    editar_produto,
    listar_produtos,
)
from pdv.relatorios import (
    Periodo,
    periodo_hoje,
    periodo_mes_atual,
    periodo_ultimos_dias,
    produtos_mais_vendidos,
    resumo_vendas,
    vendas_por_dia,
)
from pdv.terminal.tabelas import (
    mostrar_backups,
    mostrar_carrinho,
    mostrar_compras,
    mostrar_historico_caixas,
    mostrar_movimentacoes,
    mostrar_produtos,
    mostrar_produtos_gerenciais,
    mostrar_resumo_caixa,
    mostrar_produtos_mais_vendidos,
    mostrar_resumo_vendas,
    mostrar_vendas_por_dia,
)
from pdv.terminal.utilitarios import (
    data_br,
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
    ler_data,
)
from pdv.usuarios import autenticar, criar_usuario
from pdv.vendas import FORMAS_PAGAMENTO, finalizar_venda
from pdv.precificacao import calcular_rentabilidade

# a venda em andamento (fica na memória até ser finalizada)
carrinho = Carrinho()

MOVIMENTACOES_NA_TELA = 50
CAIXAS_NA_TELA = 20
PRODUTOS_NO_RANKING = 10


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


# ---------------------------------------------------------------- login

def _usuario_existe():
    with conexao() as conn:
        total = conn.execute("SELECT COUNT(*) FROM usuarios WHERE ativo = 1").fetchone()[0]
    return total > 0


def _criar_primeiro_usuario():
    print("\nCadastro do primeiro usuário dono")
    nome = ler_texto("Nome: ")
    login = ler_texto("Login: ")
    senha = getpass("Senha (mínimo 8 caracteres): ")

    try:
        criar_usuario(nome, login, senha, "dono")
    except ErroPDV as erro:
        print(f"\n{erro}")
        pausar()
        return None

    print("\nUsuário dono criado com sucesso.")
    pausar()
    return autenticar(login, senha)


def menu_login():
    if not _usuario_existe():
        print("\nNenhum usuário cadastrado.")
        print("Cadastre o primeiro usuário dono para continuar.")
        usuario = _criar_primeiro_usuario()
        if usuario is None:
            return None
        return usuario

    while True:
        limpar_tela()
        cabecalho("LOGIN")
        login = input("\nLogin: ").strip()
        senha = getpass("Senha: ")

        usuario = autenticar(login, senha)
        if usuario is None:
            print("\nLogin ou senha inválidos.")
            if not confirmar("Tentar novamente?"):
                return None
            continue

        print(f"\nBem-vindo(a), {usuario['nome']}!")
        pausar()
        return usuario


# ---------------------------------------------------------------- menu principal

def _opcoes_menu(usuario):
    if usuario["perfil"] == "dono":
        return [
            ("1", "Produtos", menu_produtos),
            ("2", "Vendas", menu_vendas),
            ("3", "Estoque", menu_estoque),
            ("4", "Caixa", menu_caixa),
            ("5", "Relatórios", menu_relatorios),
            ("6", "Backup", menu_backup),
            ("7", "Usuários", menu_usuarios),
        ]

    return [
        ("1", "Produtos", menu_produtos),
        ("2", "Vendas", menu_vendas),
        ("3", "Caixa", menu_caixa),
    ]


def menu_principal(usuario):
    executar_menu(
        f"{NOME_SISTEMA} - v{VERSAO} - {usuario['perfil'].title()}",
        _opcoes_menu(usuario),
        texto_sair="Sair",
        pausar_apos_acao=False,
    )
    print("\nEncerrando o sistema...")


# ---------------------------------------------------------------- usuários

def menu_usuarios():
    executar_menu("USUÁRIOS", [
        ("1", "Cadastrar usuário", cadastrar_usuario),
        ("2", "Listar usuários", listar_usuarios),
    ])


def cadastrar_usuario():
    nome = ler_texto("\nNome: ")
    login = ler_texto("Login: ")
    perfil = escolher("\nPerfil: ", ("dono", "operador"))
    senha = getpass("Senha: ")

    id_usuario = criar_usuario(nome, login, senha, perfil)
    print(f"\nUsuário '{nome}' cadastrado com o ID {id_usuario}.")


def listar_usuarios():
    with conexao() as conn:
        usuarios = conn.execute(
            """
            SELECT id, nome, login, perfil, ativo
            FROM usuarios
            ORDER BY nome
            """
        ).fetchall()

    if not usuarios:
        print("\nNenhum usuário cadastrado.")
        return

    print("\nUSUÁRIOS:")
    for usuario in usuarios:
        status = "Ativo" if usuario["ativo"] else "Inativo"
        print(f"{usuario['id']} - {usuario['nome']} | {usuario['login']} | {usuario['perfil']} | {status}")


# ---------------------------------------------------------------- produtos

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
        ("1", "Compra/reposição", entrada),
        ("2", "Movimentações", movimentacoes),
        ("3", "Contagem por leitura", ajustar_por_contagem),
        ("4", "Ajuste manual", ajuste),
        ("5", "Gestão e precificação", menu_gestao_estoque),
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


def menu_relatorios():
    executar_menu("RELATÓRIOS", [
        ("1", "Resumo de vendas", relatorio_resumo),
        ("2", "Produtos mais vendidos", relatorio_produtos),
        ("3", "Vendas por dia", relatorio_por_dia),
        ("4", "Lucro bruto por período", relatorio_rentabilidade),
    ])


def menu_gestao_estoque():
    executar_menu("GESTÃO DE ESTOQUE", [
        ("1", "Produtos, filtros e ordenação", consultar_produtos_gestao),
        ("2", "Histórico de compras", consultar_compras),
        ("3", "Precificar produto", precificar_produto),
        ("4", "Potencial do estoque atual", mostrar_potencial_estoque),
    ])


def menu_backup():
    executar_menu("BACKUP", [
        ("1", "Fazer backup agora", backup_agora),
        ("2", "Ver backups", ver_backups),
        ("3", "Restaurar backup", restaurar),
    ])


# ---------------------------------------------------------------- produtos

def cadastrar():
    nome = ler_texto("\nNome do produto: ")
    preco = ler_decimal("Preço: R$ ", minimo=0)
    estoque = ler_inteiro("Estoque inicial: ", minimo=0)
    codigo_barras = ler_texto("Código de barras (ENTER para ignorar): ", obrigatorio=False)

    id_produto = cadastrar_produto(nome, preco, estoque, codigo_barras)
    print(f"\nProduto '{nome}' cadastrado com o ID {id_produto}.")


def listar():
    mostrar_produtos(listar_produtos())


def _pedir_produto(mensagem="\nID do produto: "):
    id_produto = ler_inteiro(mensagem, minimo=1)
    produto = buscar_produto(id_produto)
    if produto is None:
        raise ErroPDV(f"Produto {id_produto} não encontrado.")
    return produto


def _produto_por_entrada(entrada):
    """Resolve leitura de código de barras ou busca parcial pelo nome."""
    entrada = (entrada or "").strip()
    if not entrada:
        raise ErroPDV("Informe um código de barras, nome ou ID de produto.")

    produto = buscar_produto_por_codigo_barras(entrada, incluir_inativos=True)

    if produto is not None:
        if not produto["ativo"]:
            raise ErroPDV(f"O produto '{produto['nome']}' está desativado.")
        return produto

    resultados = buscar_produtos_por_nome(entrada)
    if not resultados:
        raise ErroPDV(f"Nenhum produto encontrado para '{entrada}'.")
    if len(resultados) == 1:
        return resultados[0]

    print("\nMais de um produto encontrado:")
    mostrar_produtos(resultados)
    id_produto = ler_inteiro("ID do produto desejado: ", minimo=1)
    produto = next((item for item in resultados if item["id"] == id_produto), None)
    if produto is None:
        raise ErroPDV("O ID escolhido não está entre os resultados da busca.")
    return produto


def editar():
    mostrar_produtos(listar_produtos())
    produto = _pedir_produto()

    print("\n(ENTER mantém o valor atual)")
    nome = ler_texto(f"Nome [{produto['nome']}]: ", padrao=produto["nome"])
    preco = ler_decimal(
        f"Preço [{dinheiro(produto['preco'])}]: R$ ", minimo=0, padrao=produto["preco"]
    )
    codigo_atual = produto["codigo_barras"] or "sem código"
    codigo_barras = ler_texto(
        f"Código de barras [{codigo_atual}] (ENTER mantém, - remove): ",
        obrigatorio=False,
    )
    if codigo_barras == "-":
        codigo_barras = ""
    elif not codigo_barras:
        codigo_barras = None

    editar_produto(produto["id"], nome, preco, codigo_barras)
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
    print("\nLeia o código de barras ou digite o nome. ENTER encerra; - desfaz a última unidade.")

    while True:
        entrada = input("\nProduto: ").strip()
        if not entrada:
            return
        if entrada == "-":
            id_produto = carrinho.desfazer_ultima_adicao()
            produto = buscar_produto(id_produto)
            print(f"Adição desfeita: {produto['nome']}.")
            continue

        try:
            produto = _produto_por_entrada(entrada)
            item = carrinho.adicionar(produto["id"], 1)
        except ErroPDV as erro:
            print(f"\n{erro}")
            continue

        print(f"{item.nome}: {item.quantidade} un. ({dinheiro(item.subtotal)})")
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

    valor_recebido = None
    if forma_pagamento == DINHEIRO:
        valor_recebido = _pedir_valor_recebido(carrinho.total())

    try:
        resultado = finalizar_venda(carrinho, forma_pagamento, valor_recebido=valor_recebido)
    except EstoqueInsuficiente as erro:
        print(f"\n{erro}")
        if not confirmar("Vender mesmo assim, deixando o estoque negativo?"):
            print("\nVenda não finalizada. O carrinho foi mantido.")
            return
        resultado = finalizar_venda(
            carrinho,
            forma_pagamento,
            permitir_estoque_negativo=True,
            valor_recebido=valor_recebido,
        )

    print(f"\nVENDA #{resultado.id_venda} FINALIZADA")
    print(f"Total: {dinheiro(resultado.total)}")
    print(f"Pagamento: {resultado.forma_pagamento}")

    if resultado.troco is not None:
        print(f"Recebido: {dinheiro(resultado.valor_recebido)}")
        print(f"\n>>> TROCO: {dinheiro(resultado.troco)} <<<")

    _mostrar_comprovante(resultado.id_venda)

    if resultado.estoques_negativos:
        print("\n=== ALERTA DE ESTOQUE ===")
        for nome, estoque in resultado.estoques_negativos:
            print(f"{nome} ficou com o estoque {estoque}")
        print("\nRegistre uma entrada ou ajuste de estoque.")


def _mostrar_comprovante(id_venda):
    """Mostra o cupom e o salva em arquivo. A venda já está gravada: se o arquivo
    não puder ser salvo, só avisa, sem desfazer nada."""
    print("\n" + gerar_comprovante(id_venda))

    try:
        caminho = salvar_comprovante(id_venda)
    except OSError as erro:
        print(f"Não foi possível salvar o comprovante: {erro}")
    else:
        print(f"Comprovante salvo em: {caminho}")


def _pedir_valor_recebido(total):
    """Pergunta quanto o cliente entregou, repetindo enquanto for menor que o total."""
    print(f"\nTotal a pagar: {dinheiro(total)}")

    while True:
        valor = ler_decimal("Valor recebido (ENTER = valor exato): R$ ", minimo=0, padrao=total)

        if valor >= total:
            return valor

        print(f"\nValor menor que o total. Faltam {dinheiro(total - valor)}.")


def limpar():
    if carrinho.esta_vazio():
        print("\nO carrinho já está vazio.")
    elif confirmar("\nLimpar o carrinho?"):
        carrinho.limpar()
        print("\nCarrinho limpo.")


# ---------------------------------------------------------------- estoque

def entrada():
    print("\nLeia os produtos recebidos ou digite o nome. Cada leitura adiciona uma unidade; ENTER conclui; - desfaz.")
    itens = {}
    adicoes = []
    custos_iniciais = {}

    while True:
        entrada = input("\nProduto: ").strip()
        if not entrada:
            break
        if entrada == "-":
            if not adicoes:
                print("Não há leitura para desfazer.")
                continue
            id_produto = adicoes.pop()
            itens[id_produto]["quantidade"] -= 1
            if itens[id_produto]["quantidade"] == 0:
                del itens[id_produto]
                custos_iniciais.pop(id_produto, None)
            print("Última unidade removida da compra.")
            continue

        try:
            produto = _produto_por_entrada(entrada)
        except ErroPDV as erro:
            print(f"\n{erro}")
            continue

        item = itens.get(produto["id"])
        if item is None:
            if produto["estoque"] > 0 and produto["custo_medio"] is None:
                custo_inicial = ler_decimal(
                    f"Custo unitário do estoque atual de {produto['nome']}: R$ ",
                    minimo=0,
                )
                custos_iniciais[produto["id"]] = custo_inicial

            custo_unitario = ler_decimal(
                f"Custo unitário da compra de {produto['nome']}: R$ ", minimo=0
            )
            item = {"quantidade": 0, "custo_unitario": custo_unitario}
            itens[produto["id"]] = item

        item["quantidade"] += 1
        adicoes.append(produto["id"])
        print(f"{produto['nome']}: {item['quantidade']} un. recebidas.")

    if not itens:
        print("\nNenhum produto foi incluído na compra.")
        return

    fornecedor = ler_texto("Fornecedor (opcional): ", obrigatorio=False)
    referencia = ler_texto("Referência do comprovante (opcional): ", obrigatorio=False)
    observacao = ler_texto("Observação (opcional): ", obrigatorio=False)
    id_compra = registrar_compra_estoque(
        [
            (id_produto, item["quantidade"], item["custo_unitario"])
            for id_produto, item in itens.items()
        ],
        fornecedor=fornecedor,
        referencia=referencia,
        observacao=observacao,
        custos_iniciais=custos_iniciais,
    )
    print(f"\nCompra #{id_compra} registrada.")


def ajustar_por_contagem():
    print("\nLeia cada unidade contada ou digite o nome. ENTER conclui; - desfaz a última leitura.")
    contagens = {}
    adicoes = []

    while True:
        entrada = input("\nProduto: ").strip()
        if not entrada:
            break
        if entrada == "-":
            if not adicoes:
                print("Não há leitura para desfazer.")
                continue
            id_produto = adicoes.pop()
            contagens[id_produto] -= 1
            if contagens[id_produto] == 0:
                del contagens[id_produto]
            print("Última unidade removida da contagem.")
            continue

        try:
            produto = _produto_por_entrada(entrada)
        except ErroPDV as erro:
            print(f"\n{erro}")
            continue

        contagens[produto["id"]] = contagens.get(produto["id"], 0) + 1
        adicoes.append(produto["id"])
        print(f"{produto['nome']}: {contagens[produto['id']]} un. contadas.")

    if not contagens:
        print("\nNenhum produto foi contado.")
        return

    print("\nContagem informada:")
    for id_produto, quantidade in contagens.items():
        produto = buscar_produto(id_produto)
        print(f"{produto['nome']}: contado {quantidade}, no sistema {produto['estoque']}.")

    if not confirmar("Aplicar os ajustes desta contagem?"):
        print("\nContagem cancelada; o estoque não foi alterado.")
        return

    resultados = ajustar_estoque_em_lote(contagens, "Contagem por código de barras")
    for resultado in resultados:
        print(
            f"{resultado.nome_produto}: "
            f"{resultado.estoque_anterior} -> {resultado.estoque_atual}"
        )


def ajuste():
    mostrar_produtos(listar_produtos())
    produto = _produto_por_entrada(input("\nCódigo de barras ou nome do produto: "))
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

    # o caixa já está fechado; se o backup falhar, só avisa
    try:
        caminho = fazer_backup()
        print(f"Backup automático criado: {caminho.name}")
    except ErroPDV as erro:
        print(f"\nATENÇÃO: {erro}")
        print("Faça um backup manual em Backup > Fazer backup agora.")


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


# ---------------------------------------------------------------- relatórios

def _escolher_periodo():
    print("\nPeríodo:")
    opcao = escolher("Escolha: ", ("Hoje", "Últimos 7 dias", "Este mês", "Outro período"))

    if opcao == "Hoje":
        return periodo_hoje()
    if opcao == "Últimos 7 dias":
        return periodo_ultimos_dias(7)
    if opcao == "Este mês":
        return periodo_mes_atual()

    inicio = ler_data("\nData inicial (dd/mm/aaaa): ")
    fim = ler_data("Data final (dd/mm/aaaa): ")
    return Periodo(inicio, fim)


def _titulo_periodo(titulo, periodo):
    if periodo.inicio == periodo.fim:
        print(f"\n{titulo} - {data_br(periodo.inicio)}")
    else:
        print(f"\n{titulo} - {data_br(periodo.inicio)} a {data_br(periodo.fim)}")


def relatorio_resumo():
    periodo = _escolher_periodo()
    _titulo_periodo("RESUMO DE VENDAS", periodo)
    mostrar_resumo_vendas(resumo_vendas(periodo))


def relatorio_produtos():
    periodo = _escolher_periodo()
    _titulo_periodo(f"TOP {PRODUTOS_NO_RANKING} PRODUTOS", periodo)
    mostrar_produtos_mais_vendidos(produtos_mais_vendidos(periodo, PRODUTOS_NO_RANKING))


def relatorio_por_dia():
    periodo = _escolher_periodo()
    _titulo_periodo("VENDAS POR DIA", periodo)
    mostrar_vendas_por_dia(vendas_por_dia(periodo))


def relatorio_rentabilidade():
    periodo = _escolher_periodo()
    _titulo_periodo("LUCRO BRUTO DAS VENDAS", periodo)
    resumo = resumo_rentabilidade(periodo)

    print(f"\nFaturamento no período: {dinheiro(resumo.faturamento_total)}")
    print(f"Faturamento com custo conhecido: {dinheiro(resumo.faturamento_com_custo)}")
    print(f"Custo das mercadorias: {dinheiro(resumo.custo_das_mercadorias)}")
    print(f"Lucro bruto: {dinheiro(resumo.lucro_bruto)}")
    print(f"Margem bruta: {resumo.margem_bruta_percentual:.2f}%")
    if resumo.unidades_sem_custo:
        print(f"Unidades vendidas sem custo conhecido: {resumo.unidades_sem_custo}")


def consultar_produtos_gestao():
    filtros = {
        "Todos": None,
        "Parados há mais de 30 dias": "parados",
        "Cadastrados nos últimos 30 dias": "recentes",
        "Sem custo conhecido": "sem_custo",
    }
    ordenacoes = {
        "Nome": "nome",
        "Mais recentes": "recentes",
        "Maior preço": "preco_maior",
        "Menor preço": "preco_menor",
        "Maior custo": "custo_maior",
        "Menor custo": "custo_menor",
        "Maior lucro por unidade": "lucro_maior",
        "Menor lucro por unidade": "lucro_menor",
        "Maior margem": "margem_maior",
        "Menor margem": "margem_menor",
        "Maior estoque": "estoque_maior",
        "Menor estoque": "estoque_menor",
    }

    filtro = escolher("Filtro: ", tuple(filtros))
    ordenacao = escolher("Ordenar por: ", tuple(ordenacoes))
    produtos = listar_produtos_gestao(
        filtro=filtros[filtro], ordenar_por=ordenacoes[ordenacao]
    )
    mostrar_produtos_gerenciais(produtos)


def _ler_data_opcional(mensagem):
    texto = ler_texto(mensagem, obrigatorio=False)
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError as erro:
        raise ErroPDV("Data inválida. Use dd/mm/aaaa.") from erro


def consultar_compras():
    fornecedor = ler_texto("Fornecedor (ENTER para todos): ", obrigatorio=False)
    referencia = ler_texto("Referência (ENTER para todas): ", obrigatorio=False)
    inicio = _ler_data_opcional("Data inicial (dd/mm/aaaa, ENTER para ignorar): ")
    fim = _ler_data_opcional("Data final (dd/mm/aaaa, ENTER para ignorar): ")
    compras = listar_compras(fornecedor, referencia, inicio, fim)
    mostrar_compras(compras)


def _mostrar_calculo_preco(preco, custo):
    rentabilidade = calcular_rentabilidade(preco, custo)
    if rentabilidade is None:
        print("Custo desconhecido. Registre uma compra para calcular a rentabilidade.")
        return

    print(f"Lucro bruto por unidade: {dinheiro(rentabilidade.lucro_bruto_unitario)}")
    if rentabilidade.margem_bruta_percentual is None:
        print("Margem bruta: não calculável com preço zero.")
    else:
        print(f"Margem bruta sobre a venda: {rentabilidade.margem_bruta_percentual:.2f}%")
    if rentabilidade.acrescimo_sobre_custo_percentual is None:
        print("Acréscimo sobre custo: não calculável com custo zero.")
    else:
        print(f"Acréscimo sobre custo: {rentabilidade.acrescimo_sobre_custo_percentual:.2f}%")


def precificar_produto():
    entrada = input("\nCódigo de barras ou nome do produto: ")
    produto = _produto_por_entrada(entrada)

    print(f"\n{produto['nome']}")
    print(f"Custo médio: {dinheiro(produto['custo_medio']) if produto['custo_medio'] is not None else 'desconhecido'}")
    print(f"Preço atual: {dinheiro(produto['preco'])}")
    _mostrar_calculo_preco(produto["preco"], produto["custo_medio"])

    novo_preco = ler_decimal("Novo preço de venda: R$ ", minimo=0)
    print("\nResultado com o novo preço:")
    _mostrar_calculo_preco(novo_preco, produto["custo_medio"])

    if confirmar("Salvar o novo preço?"):
        editar_produto(produto["id"], produto["nome"], novo_preco)
        print("\nPreço atualizado.")
    else:
        print("\nPreço não alterado.")


def mostrar_potencial_estoque():
    resumo = resumo_potencial_estoque()
    print("\nPOTENCIAL DO ESTOQUE ATUAL (CUSTOS CONHECIDOS)")
    print(f"Faturamento potencial: {dinheiro(resumo.faturamento_potencial)}")
    print(f"Custo estimado: {dinheiro(resumo.custo_estimado)}")
    print(f"Lucro bruto potencial: {dinheiro(resumo.lucro_bruto_potencial)}")
    print(f"Margem bruta potencial: {resumo.margem_bruta_percentual:.2f}%")
    if resumo.produtos_sem_custo:
        print(f"Produtos em estoque sem custo conhecido: {resumo.produtos_sem_custo}")


# ---------------------------------------------------------------- backup

def backup_agora():
    caminho = fazer_backup()
    print(f"\nBackup criado: {caminho.name}")
    print(f"Pasta: {caminho.parent}")


def ver_backups():
    mostrar_backups(listar_backups())


def restaurar():
    if not carrinho.esta_vazio():
        raise ErroPDV("Há itens no carrinho. Finalize a venda ou limpe o carrinho antes.")

    backups = listar_backups()
    mostrar_backups(backups)

    if not backups:
        return

    id_backup = ler_inteiro("\nID do backup para restaurar: ", minimo=1)
    if confirmar(f"Restaurar backup #{id_backup}?"):
        restaurar_backup(id_backup)
        print("\nBackup restaurado.")