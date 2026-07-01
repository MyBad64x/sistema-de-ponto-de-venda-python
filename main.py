from banco import conectar

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
    SELECT *
    FROM vendas
""")

for venda in cursor.fetchall():
    print(venda)

conn.close()