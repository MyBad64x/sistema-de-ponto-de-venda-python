# Revisão de código — setembro de 2026

Revisão feita ao retomar o projeto na versão 1.2.1. Cada erro abaixo foi
reproduzido rodando o sistema, corrigido na v1.2.2 e ganhou um teste em
`testes/` para não voltar. O objetivo deste arquivo é registrar **por que**
cada coisa estava errada, para servir de aprendizado.

## Erros que impediam o sistema de funcionar

### 1. O banco nunca era criado
`criar_tabelas()` só rodava executando `banco.py` direto. Quem clonava o
projeto e rodava `python main.py` recebia `no such table: produtos` na
primeira ação.

**Lição:** o ponto de entrada do programa precisa preparar tudo que ele usa.
Agora `main.py` chama `criar_tabelas()` antes do menu.

### 2. Nenhuma venda finalizava e fechar o caixa derrubava o sistema
`vendas.py` fazia `INSERT INTO vendas(caixa_id, ...)` e `caixa.py` fazia
`WHERE caixa_id = ?`, mas a tabela `vendas` não tinha essa coluna. O código
evoluiu e o banco ficou para trás.

**Lição:** `CREATE TABLE IF NOT EXISTS` não altera uma tabela que já existe.
Quando uma coluna nova é necessária, é preciso uma **migração**
(`ALTER TABLE ... ADD COLUMN`) para os bancos que já existem. Veja
`_atualizar_banco_antigo()` em `pdv/banco.py`.

### 3. Vendia além do estoque e gravava o estoque errado
Com estoque 5, adicionar 3 + 3 do mesmo produto criava duas linhas no
carrinho. A conferência olhava cada linha sozinha (3 ≤ 5, ok) e deixava vender
6. Pior: a baixa de estoque lia o produto com `buscar_produto()`, que abre
**outra conexão** e não enxerga as alterações ainda não confirmadas da venda.
As duas linhas calculavam `5 - 3 = 2`, e o estoque terminava em 2 em vez de −1.

**Lições:**
- o carrinho agora é um dicionário `{id_produto: quantidade}`, então o mesmo
  produto nunca aparece duas vezes;
- dentro de uma transação, tudo precisa usar a mesma conexão;
- `UPDATE ... SET estoque = estoque - ?` deixa o banco fazer a conta com o
  valor mais atual, em vez de calcular no Python com um valor lido antes.

### 4. Quantidade negativa era aceita
Vender −4 gerava uma venda de R$ −40,00 e aumentava o estoque.
`ler_inteiro` já tinha o parâmetro `minimo`, mas o menu não usava.

**Lição:** valide nas duas pontas. O terminal pede `minimo=1` para dar uma
mensagem amigável, e a regra de negócio recusa de novo, porque amanhã outra
interface pode chamar a função sem passar pelo terminal.

### 5. Desativar um ID inexistente derrubava o sistema
```python
if produto is None:
    print("Produto não encontrado")
                                    # faltava um return aqui
if produto[4] == 0:                 # None[4] -> TypeError
```
E a mensagem de sucesso era `print("Produto '{produto[1]}' ...")` sem o `f`,
então aparecia literalmente `{produto[1]}` na tela.

### 6. Produto desativado podia ser vendido
`buscar_produto()` devolve o produto mesmo desativado, e o carrinho não
conferia a coluna `ativo`.

## Problemas menores

- **Editar produto alterava o estoque sem registrar movimentação**, então o
  histórico deixava de bater com o estoque. Agora editar muda só nome e preço;
  estoque só muda por Entrada ou Ajuste. Um teste confere que a soma das
  movimentações de cada produto é igual ao estoque dele.
- **Estoque atualizado e movimentação gravados em conexões separadas**: se a
  segunda falhasse, o estoque mudava sem registro. Agora é uma transação só.
- **Mensagens sumiam da tela**: depois de `print("Produto não encontrado!")`
  vinha `continue`, o laço voltava ao topo e `limpar_tela()` apagava a mensagem
  antes de alguém ler. O mesmo com "Opção inválida" e "Em desenvolvimento".
  Agora `executar_menu()` pausa em um lugar só.
- **O banco dependia da pasta atual**: `"database/loja.db"` é relativo a
  onde o terminal está, não a onde o código está. Rodar de outra pasta criava
  um banco novo e vazio.
- **Arredondamento de `float`**: 0,1 × 3 era gravado como
  `0.30000000000000004`. Os totais agora são arredondados para 2 casas.
- **Datas em UTC**: o SQLite grava `CURRENT_TIMESTAMP` em UTC (3 horas à
  frente de Brasília). As consultas agora convertem com
  `datetime(coluna, 'localtime')`.
- **Preço com vírgula** (`12,50`) era recusado.

## Mudanças de organização

- **Regras de negócio separadas da interface.** Antes, `cadastrar_produto()`
  fazia `print("Produto cadastrado com sucesso!")`. Isso impede testar a
  função e impede reaproveitá-la numa interface gráfica. Agora as funções de
  `pdv/` devolvem resultados ou levantam `ErroPDV`, e só `pdv/terminal/`
  conversa com o usuário.
- **`conexao()` como gerenciador de contexto** (`with conexao() as conn:`)
  garante commit, rollback e fechamento, que antes eram repetidos (e às vezes
  esquecidos) em cada função.
- **Colunas pelo nome**: `produto["estoque"]` em vez de `produto[3]`. Se a
  ordem das colunas mudar, o código continua certo.
- **Funções perigosas removidas**: `zerar_estoque()` zerava o estoque de todos
  os produtos e `limpar_movimentacoes()` apagava todo o histórico, ambas sem
  registro. Não eram usadas; continuam no histórico do Git se precisar.

## Pontos para a próxima etapa

- **Saldo do caixa**: o fechamento soma todas as vendas ao valor inicial, mas
  PIX e cartão não entram na gaveta. O fechamento deveria separar por forma
  de pagamento e conferir só o dinheiro (junto com sangria e suprimento).
- **Dinheiro em centavos**: guardar valores como inteiros em centavos
  (`1250` em vez de `12.50`) elimina de vez os problemas de `float`.
- **Chaves estrangeiras**: as tabelas não declaram `FOREIGN KEY`, então o banco
  aceitaria uma venda apontando para um caixa que não existe.
