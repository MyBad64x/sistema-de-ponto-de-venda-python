from banco import conectar

#função para registrar movimentações do estoque
def registrar_movimentacao(
    produto_id,
    tipo,
    quantidade,
    observacao=""
):

    conn = conectar()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO movimentacoes_estoque(
                produto_id,
                tipo,
                quantidade,
                observacao
            )
            VALUES (?, ?, ?, ?)
        """, (
            produto_id,
            tipo,
            quantidade,
            observacao
        ))

        conn.commit()

    except Exception as erro:

        conn.rollback()

        print(
            f"Erro ao registrar movimentação: {erro}"
        )

    finally:

        conn.close()


def registrar_movimentacao_cursor(
        cursor,
        produto_id,
        tipo,
        quantidade,
        observacao=""
):
    
    cursor.execute("""
        INSERT INTO movimentacoes_estoque(
            produto_id,
            tipo,
            quantidade,
            observacao
        )
        VALUES (?, ?, ?, ?)
    """, (
        produto_id,
        tipo,
        quantidade,
        observacao
    ))

#função para listar as movimentações feitas no estoque
def listar_movimentacoes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            m.id,
            p.nome,
            m.tipo,
            m.quantidade,
            m.observacao,
            m.data_movimentacao
        FROM movimentacoes_estoque m
        JOIN produtos p
            ON p.id = m.produto_id
        ORDER BY m.id DESC
    """)

    movimentacoes = cursor.fetchall()

    conn.close()

    #função caso não haja movimentações
    if len(movimentacoes) == 0:
        print("Nenhuma movimentação encontrada.")
        return
    #embelezamento da tabela
    print("\n" + "=" * 120)
    print("MOVIMENTAÇÕES DE ESTOQUE")
    print("=" * 120)

    print(
        f"{'ID':<5}"
        f"| {'PRODUTO':<25}"
        f"| {'TIPO':<15}"
        f"| {'QTD':<8}"
        f"| {'OBSERVAÇÃO':<35}"
        f"| DATA"
    )

    print("=" * 120)

    for movimentacao in movimentacoes:

        qtd = movimentacao[3]

        if qtd > 0:
            qtd = f"+{qtd}"
        else:
            qtd = str(qtd)

        print(
            f"{movimentacao[0]:<5}"
            f"| {movimentacao[1]:<25}"
            f"| {movimentacao[2]:<15}"
            f"| {qtd:<8}"
            f"| {movimentacao[4]:<35}"
            f"| {movimentacao[5]}"
        )

    print("=" * 120)

#função para limpar o histórico de movimentação do estoque
def limpar_movimentacoes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM movimentacoes_estoque
    """)

    conn.commit()
    conn.close()

    print("Movimentações removidas.")