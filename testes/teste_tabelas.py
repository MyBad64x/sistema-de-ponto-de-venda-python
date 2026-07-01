from banco import conectar

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")

tabelas = cursor.fetchall()

print("Tabelas encontradas:")
print(tabelas)

conn.close()