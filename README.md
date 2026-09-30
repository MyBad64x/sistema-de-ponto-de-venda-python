# PDV Python
[![Testes](https://github.com/MyBad64x/sistema-de-ponto-de-venda-python/actions/workflows/testes.yml/badge.svg)](https://github.com/MyBad64x/sistema-de-ponto-de-venda-python/actions/workflows/testes.yml)

Sistema de Ponto de Venda (PDV) desenvolvido em Python com SQLite.

Este é meu primeiro projeto completo de software, criado com o objetivo de colocar em prática conceitos de programação, banco de dados e organização de código. O projeto também está sendo utilizado como base para um sistema destinado a um pequeno comércio, por isso continua em desenvolvimento e recebe melhorias constantes.

## Funcionalidades

**Produtos**
- Cadastro, edição, listagem, desativação e reativação de produtos

**Estoque**
- Entrada de estoque (chegada de mercadoria)
- Ajuste de estoque (inventário, perdas, quebras)
- Histórico de todas as movimentações (entradas, ajustes e vendas)

**Vendas**
- Carrinho de compras (adicionar, remover, limpar)
- Finalização de venda com escolha da forma de pagamento e troco no pagamento em dinheiro
- Aviso de estoque insuficiente, com opção de vender mesmo assim
- Comprovante em texto ao finalizar a venda, salvo em arquivo e pronto para imprimir

**Caixa**
- Abertura, sangria, suprimento, status, fechamento com conferência do dinheiro e histórico de caixas

**Relatórios**
- Resumo de vendas, produtos mais vendidos e vendas por dia, por período

**Geral**
- Banco de dados SQLite criado automaticamente
- Interface em terminal com menus
- Testes automáticos
- Backup automático ao fechar o caixa, backup manual e restauração

## Tecnologias utilizadas

- Python 3.10+
- SQLite / SQL
- pytest (testes automáticos)
- GitHub Actions (testes automáticos a cada pull request)
- Git

## Estrutura do projeto

```
sistema-de-ponto-de-venda-python/
├── .github/workflows/       # testes automáticos no GitHub (CI)
├── main.py                  # ponto de entrada: cria o banco e abre o menu
│
├── pdv/                     # código do sistema
│   ├── banco.py             # conexão, criação e atualização das tabelas
│   ├── erros.py             # erros de regra de negócio (ErroPDV)
│   ├── produtos.py          # cadastro de produtos
│   ├── estoque.py           # entrada e ajuste de estoque
│   ├── movimentacoes.py     # histórico de movimentações
│   ├── caixa.py             # abertura e fechamento de caixa
│   ├── carrinho.py          # carrinho da venda em andamento
│   ├── vendas.py            # finalização de vendas
│   ├── relatorios.py        # relatórios de vendas por período
│   ├── backup.py            # backup e restauração do banco
│   ├── comprovante.py       # comprovante de venda em texto
│   │
│   └── terminal/            # interface de terminal
│       ├── menu.py          # menus e ações
│       ├── tabelas.py       # tabelas exibidas na tela
│       └── utilitarios.py   # leitura de números/textos, formatação
│
├── testes/                  # testes automáticos (pytest)
├── docs/                    # anotações e revisões
└── database/                # criado automaticamente (fora do Git)
```

Os módulos de `pdv/` contêm as **regras de negócio** e não usam `print` nem `input`: recebem dados, validam, gravam no banco e devolvem resultados (ou levantam `ErroPDV` quando algo não é permitido). Toda a conversa com o usuário fica em `pdv/terminal/`. Assim as regras podem ser testadas sozinhas e, no futuro, a interface de terminal pode ser trocada por uma gráfica sem reescrever a lógica.

## Como executar

1. Clone este repositório.

```bash
git clone https://github.com/MyBad64x/sistema-de-ponto-de-venda-python.git
```

2. Acesse a pasta do projeto.

```bash
cd sistema-de-ponto-de-venda-python
```

3. Execute o arquivo principal.

```bash
python main.py
```

O banco é criado em `database/loja.db` na primeira execução. Bancos criados por versões anteriores são atualizados automaticamente.

## Backups

Os backups ficam em `database/backups/`, um arquivo por backup, com a data e a hora no nome. O sistema faz um backup automático a cada fechamento de caixa e mantém os 30 mais recentes.

Os backups ficam no mesmo computador que o banco, então não protegem contra perda ou defeito do disco. De vez em quando, copie a pasta `database/backups/` para um pendrive ou para a nuvem.

## Como rodar os testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Os testes usam um banco temporário e não mexem no `database/loja.db`.

Os testes também rodam automaticamente no GitHub a cada pull request e a cada merge na `main`, no Linux e no Windows, com Python 3.10 e 3.14.

## Objetivos do projeto

Além de desenvolver um sistema funcional para um pequeno comércio, este projeto também tem como objetivo servir como estudo e prática de:

- Organização de projetos em Python
- SQL e SQLite
- Versionamento com Git
- Testes automáticos
- Boas práticas de programação
- Evolução contínua de software

## Próximas funcionalidades

- Login de usuários
- Impressão de comprovantes
- Interface gráfica

## Autor

Desenvolvido por Alberto Zgraia Neto (MyBad64x).
