"""PDV Python - sistema de ponto de venda com SQLite.

O pacote é dividido em duas camadas:

- módulos de regra de negócio (produtos, estoque, caixa, carrinho, vendas):
  validam os dados, gravam no banco e devolvem resultados. Não usam print nem input.
- pdv.terminal: a interface de terminal, que lê o que o usuário digita,
  chama as regras de negócio e mostra os resultados.

Essa separação permite testar as regras sozinhas e, no futuro, trocar o
terminal por uma interface gráfica sem reescrever a lógica.
"""

NOME_SISTEMA = "PDV Python"
VERSAO = "1.4.0"
