from banco import conectar
from movimentacoes_estoque import registrar_movimentacao

#função para cadastrar os produtos
def cadastrar_produto(nome, preco, estoque):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos(nome, preco, estoque)
        VALUES (?, ?, ?)
    """, (nome, preco, estoque))

    conn.commit()
    conn.close()

    print("Produto cadastrado com sucesso!")

#função para listar os produtos cadastrados no estoque
def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM produtos
        WHERE ativo = 1
    """)

    produtos = cursor.fetchall()

    if len(produtos) == 0:
        print("Nenhum produto cadastrado.")
    else:
        print("\n" + "=" * 60)
        print(
            f"{'ID':<5}"
            f"| {'PRODUTO':<20}"
            f"| {'PREÇO':<10}"
            f"| {'ESTOQUE':<8}"
            f"| STATUS"
        )
        print("=" * 60)

        for produto in produtos:

            status = "Ativo" if produto[4] == 1 else "Inativo"

            print(
                f"{produto[0]:<5}"
                f"| {produto[1]:<20}"
                f"| R$ {produto[2]:<7.2f}"
                f"| {produto[3]:<8}"
                f"| {status}"
            )

        print("=" * 60)

    conn.close()

    return produtos

#função para buscar produto via id
def buscar_produto(id_produto):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM produtos
        WHERE id = ?
    """, (id_produto,))

    produto = cursor.fetchone()

    conn.close()

    return produto 

#função para atualização de estoque
def atualizar_estoque(id_produto, novo_estoque):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET estoque = ?
        WHERE id = ?
    """, (novo_estoque, id_produto))

    conn.commit()
    conn.close()

#função para zerar o estoque ao invés de deleta-lo
def zerar_estoque():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET estoque = 0
    """)

    conn.commit()
    conn.close()

    print("Estoque zerado!")

#função de desativar produto ao invés de excluir totalmente(facilita no gerenciamento poupando tempo)
def desativar_produto(id_produto):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET ativo = 0
        WHERE id = ?
    """, (id_produto,))

    conn.commit()
    conn.close()

    print("Produto desativado!")

#função para ativar produto que estava desativado
def ativar_produto(id_produto):
    
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET ativo = 1
        WHERE id = ?
    """, (id_produto,))

    conn.commit()
    conn.close()

    print("Produto reativado!")

#função de mostrar produto que entrou no depósito
def entrada_estoque(
    id_produto,
    quantidade,
    observacao=""
):
    
    produto = buscar_produto(id_produto)

    if produto is None:
        print("Produto não encontrado!")
        return
    
    novo_estoque = produto[3] + quantidade

    atualizar_estoque(
        id_produto,
        novo_estoque
    )

    registrar_movimentacao(
        id_produto,
        "ENTRADA",
        quantidade,
        observacao
    )

    print(
        f"Entrada registrada: "
        f"{produto[1]} (+{quantidade})"
    )

#função que ajusta o estoque caso haja o produto no estoque e está em quantidade errada
def ajustar_estoque(
        id_produto,
        novo_estoque,
        observacao=""
):
    
    produto = buscar_produto(id_produto)

    if produto is None:
        print("Produto não encontrado!")
        return
    
    estoque_atual = produto[3]

    diferenca = novo_estoque - estoque_atual

    if diferenca == 0:
        print("Nenhum ajuste necessário.")
        return
    
    atualizar_estoque(
        id_produto,
        novo_estoque
    )

    registrar_movimentacao(
        id_produto,
        "AJUSTE",
        diferenca,
        observacao
    )

    print(
        f"Ajuste realizado: "
        f"{produto[1]} "
        f"({estoque_atual} -> {novo_estoque})"
    )