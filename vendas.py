from banco import conectar
from movimentacoes_estoque import registrar_movimentacao_cursor
from carrinho import obter_carrinho, limpar_carrinho
from produtos import buscar_produto
from caixa import caixa_aberto

#função de finalizar venda mostrando forma de pagamento, resultado da compra total, modificação de estoque e etc
def finalizar_venda(
    forma_pagamento,
    permitir_estoque_negativo=False
    ):

    caixa = caixa_aberto()

    if caixa is None:
        print("Abra o caixa primeiro!")
        return
    
    caixa_id = caixa[0]
    
    carrinho = obter_carrinho()

    if len(carrinho) == 0:
        print("Carrinho vazio!")
        return
    
    total = 0

    produtos_negativos = []

    for id_produto, quantidade in carrinho:

        produto = buscar_produto(id_produto)

        if produto is None:
            print(f"Produto {id_produto} não encontrado!")
            return
        
        estoque = produto[3]

        if quantidade > estoque:

            if not permitir_estoque_negativo:
                print(f"Estoque insuficiente para {produto[1]}")
                return
            
            print(f"ATENÇÃO: {produto[1]} será vendido com estoque negativo!")
        
        total += produto[2] * quantidade

    conn = conectar()

    sucesso = False

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO vendas(
                caixa_id,
                valor_total,
                forma_pagamento
            )
            VALUES (?, ?, ?)
        """, (
            caixa_id,
            total,
            forma_pagamento
        ))

        venda_id = cursor.lastrowid

        for id_produto, quantidade in carrinho:

            produto = buscar_produto(id_produto)

            cursor.execute("""
                INSERT INTO itens_vendas(
                    venda_id,
                    produto_id,
                    quantidade,
                    valor_unitario
                )
                VALUES (?, ?, ?, ?)
            """, (
                venda_id,
                id_produto,
                quantidade,
                produto[2]
            ))

            novo_estoque = produto[3] - quantidade

            if novo_estoque < 0:
                produtos_negativos.append(
                    (
                        produto[1],
                        novo_estoque
                    )
                )

            cursor.execute("""
                UPDATE produtos
                SET estoque = ?
                WHERE id = ?
            """, (
                novo_estoque,
                id_produto
            ))

            registrar_movimentacao_cursor(
                cursor,
                id_produto,
                "VENDA",
                -quantidade,
                f"Venda #{venda_id}"
            )


        conn.commit()
        sucesso = True

    except Exception as erro:

        conn.rollback()

        print(f"\nErro ao finalizar venda:")
        print(erro)

        return

    finally:

        conn.close()

    if sucesso:

        limpar_carrinho()

        print("\nVENDA FINALIZADA")
        print(f"Total: R$ {total:.2f}")
        print(f"Pagamento: {forma_pagamento}")

        if produtos_negativos:

            print("\n=== ALERTA DE ESTOQUE ===")

            for nome, estoque in produtos_negativos:

                print(f"{nome} ficou com o estoque {estoque}")

            print(
                "\nÉ necessário registrar uma entrada "
                "ou ajuste de estoque."
            )