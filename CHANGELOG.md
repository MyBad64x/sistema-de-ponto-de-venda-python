# Changelog

Todas as alterações importantes deste projeto serão documentadas neste arquivo.

Este projeto segue um processo contínuo de evolução, com novas funcionalidades sendo adicionadas a cada versão.

Versão [x.y.z]
x= versão total do projeto, caso de grandes mudanças
y= adição de features novas no projeto
z= correção de bugs no projeto

---

## [1.10.0] - 2026-10-01

### Adicionado

- Sistema de login de usuários.
- Tabela de usuários com senha armazenada em hash.
- Primeiro usuário dono obrigatório no primeiro acesso.
- Perfis de acesso: `dono` e `operador`.
- Operador sem acesso a relatórios e ajuste de estoque.

### Alterado

- Fluxo de inicialização agora começa com autenticação antes do menu principal.
- README atualizado para documentar login e permissões.

### Segurança

- Senhas nunca são gravadas em texto puro; o sistema usa hash PBKDF2 com salt aleatório.

---

## [1.9.0] - 2026-09-30

### Adicionado

- Comprovante de venda: ao finalizar a venda, o sistema mostra um cupom em texto (itens, total, pagamento e troco) e o salva em `database/comprovantes/`.
- Testes automáticos no GitHub Actions a cada pull request e a cada merge na `main` (Linux e Windows, Python 3.10 e 3.14).

### Alterado

- Versão mínima do Python passou a ser a 3.10 (a 3.9 deixou de ter suporte em outubro de 2025).

---

## [1.8.0] - 2026-09-27

### Adicionado

- Backup do banco de dados pelo menu (Backup > Fazer backup agora) e automático ao fechar o caixa.
- Lista de backups com data e tamanho; são mantidos os 30 mais recentes.
- Restauração de backup, com validação do arquivo e backup de segurança do estado atual antes.

### Alterado

- A pasta `database/backups/` é ignorada pelo Git.

---

## [1.7.0] - 2026-09-26

### Adicionado

- Troco no pagamento em dinheiro: o operador informa o valor recebido (ENTER = valor exato) e o sistema mostra o troco.
- A venda guarda o valor recebido e o troco.

### Alterado

- `finalizar_venda()` aceita `valor_recebido`, que só vale para pagamento em dinheiro.

---

## [1.6.0] - 2026-09-26

### Adicionado

- Menu de relatórios com escolha de período (hoje, últimos 7 dias, este mês ou datas informadas).
- Resumo de vendas: total, quantidade, ticket médio e divisão por forma de pagamento.
- Produtos mais vendidos: top 10 por quantidade, com faturamento pelo preço do momento da venda.
- Vendas por dia, com barra proporcional ao total.

---

## [1.5.0] - 2026-09-26

### Adicionado

- Histórico de caixas: lista os últimos 20 caixas com abertura, fechamento, vendas, valor esperado, contado e diferença.
- Resumo completo de qualquer caixa do histórico, aberto ou fechado.

### Removido

- Função `em_desenvolvimento` do menu (todas as opções do caixa estão implementadas).

---

## [1.4.0] - 2026-09-25

### Adicionado

- Sangria (retirada) e suprimento (entrada) de dinheiro no caixa, com motivo obrigatório.
- Conferência no fechamento: o operador informa o valor contado na gaveta e o sistema mostra sobra ou falta.
- Resumo do caixa separado por forma de pagamento.

### Alterado

- O dinheiro esperado na gaveta considera só dinheiro físico: valor inicial + vendas em dinheiro + suprimentos − sangrias.
- `fechar_caixa()` passou a exigir o valor contado.

### Corrigido

- O fechamento somava vendas em PIX e cartão ao dinheiro da gaveta.

---

## [1.3.0] - 2026-09-25

### Adicionado

- Testes automáticos com pytest (`testes/`), usando banco temporário.
- Reativar produto desativado.
- Remover um item do carrinho.
- Status do caixa mostra valor inicial, quantidade e total de vendas.
- Forma de pagamento escolhida de uma lista (Dinheiro, PIX, Cartão de débito, Cartão de crédito).
- Venda com estoque insuficiente pergunta se deve vender mesmo assim.
- Confirmação antes de desativar produto, limpar carrinho e fechar caixa.
- Estoque inicial do cadastro entra no histórico de movimentações.

### Alterado

- Código organizado no pacote `pdv/` com a interface em `pdv/terminal/`.
- Regras de negócio não usam mais `print`/`input`: devolvem resultados e levantam `ErroPDV`.
- Conexão com o banco centralizada em `conexao()` (commit, rollback e fechamento automáticos).
- Colunas acessadas pelo nome (`produto["nome"]`) em vez do índice (`produto[1]`).
- Editar produto altera só nome e preço; estoque muda apenas por Entrada ou Ajuste.
- Valores aceitam vírgula (12,50) e são exibidos no padrão brasileiro (R$ 1.234,50).
- Datas exibidas no horário local.
- Produtos listados em ordem alfabética; movimentações mostram as 50 mais recentes.

### Corrigido

- Alteração de estoque e registro da movimentação agora são gravados na mesma transação.
- Mensagens de erro não somem mais da tela antes de serem lidas.
- Ctrl+C encerra o sistema sem mostrar erro.

### Removido

- `zerar_estoque` e `limpar_movimentacoes` (não eram usadas e apagavam dados sem registro).
- `testes/teste_tabelas.py` (substituído pelos testes automáticos).

---

## [1.2.2] - 2026-09-25

### Corrigido

- O banco não era criado ao rodar o `main.py` (erro `no such table: produtos`).
- Toda venda falhava e fechar o caixa derrubava o sistema: faltava a coluna `caixa_id` na tabela `vendas`. Bancos antigos recebem a coluna automaticamente.
- O mesmo produto adicionado duas vezes no carrinho permitia vender além do estoque e gravava o estoque errado.
- Quantidade zero ou negativa era aceita no carrinho e na entrada de estoque.
- Desativar um ID inexistente derrubava o sistema; a mensagem de sucesso não mostrava o nome do produto.
- Produto desativado podia ser vendido.
- Preço, estoque e valor do caixa aceitavam valores negativos.
- O banco dependia da pasta de onde o programa era executado.
- Total da venda gravado com erro de arredondamento (ex.: 0.30000000000000004).

---

## [1.2.1] - 2026-06-30

### Adicionado

- Integração completa dos menus com as funcionalidades do sistema.
- Módulo de Produtos totalmente operacional.
- Módulo de Estoque totalmente operacional.
- Módulo de Caixa totalmente operacional.
- Módulo de Vendas totalmente operacional.

### Alterado

- O `main.py` passou a utilizar exclusivamente a navegação por menus.
- Melhorias na organização da interface do terminal.

### Corrigido

- Validação de IDs de produtos antes de executar operações.
- Tratamento para tentativa de desativação de produtos inexistentes ou já desativados.

---

## [1.1.0]

### Adicionado

- Controle de caixa.
- Carrinho de compras.
- Finalização de vendas.
- Controle de estoque.
- Entrada de estoque.
- Ajuste de estoque.
- Registro de movimentações de estoque.
- Melhorias na organização do código.

---

## [1.0.0]

### Adicionado

- Estrutura inicial do projeto.
- Banco de dados SQLite.
- Cadastro de produtos.
- Listagem de produtos.
