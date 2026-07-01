from banco import conectar


#função de abrir o caixa
def abrir_caixa(valor_inicial):
    #checagem caso ja exista um caixa aberto
    if caixa_aberto():
        print("Já existe um caixa aberto!")
        return

    conn = conectar()
    cursor = conn.cursor()
    #formato da tabela do caixa
    cursor.execute("""
        INSERT INTO caixa(
            valor_inicial,
            status
        )
        VALUES (?, ?)
    """, (
        valor_inicial,
        "ABERTO"
    ))

    conn.commit()
    conn.close()
    #checagem se o caixa foi realmente aberto
    print("Caixa aberto com sucesso!")

#função para quando o caixa está aberto
def caixa_aberto():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM caixa
        WHERE status = 'ABERTO'
    """)

    caixa = cursor.fetchone()

    conn.close()

    return caixa

#função para fechar o caixa
def fechar_caixa():

    caixa = caixa_aberto()
    #funcão de checagem caso tente fechar um caixa que não existe
    if caixa is None:
        print("Nenhum caixa aberto!")
        return
    
    conn = conectar()
    cursor = conn.cursor()

    valor_inicial = caixa[2]

    cursor.execute("""
        SELECT COALESCE(
            SUM(valor_total),
            0
        )
        FROM vendas
        WHERE caixa_id = ?
    """, (
        caixa[0],
    ))

    total_vendas = cursor.fetchone()[0]

    valor_final = valor_inicial + total_vendas

    print("\n" + "=" * 50)
    print("FECHAMENTO DE CAIXA")
    print("=" * 50)

    print(f"Valor inicial : R$ {valor_inicial:.2f}")
    print(f"Total vendas  : R$ {total_vendas:.2f}")
    print(f"Saldo final   : R$ {valor_final:.2f}")

    print("=" * 50)

    cursor.execute("""
        UPDATE caixa
        SET
            valor_final = ?,
            data_fechamento = CURRENT_TIMESTAMP,
            status = 'FECHADO'
        WHERE id = ?
    """, (
        valor_final,
        caixa[0]
    ))

    conn.commit()
    conn.close()

    print("Caixa fechado com sucesso!")