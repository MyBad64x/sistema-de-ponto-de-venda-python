# PDV Python

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
- Finalização de venda com escolha da forma de pagamento
- Aviso de estoque insuficiente, com opção de vender mesmo assim

**Caixa**
- - Abertura, sangria, suprimento, status e fechamento com conferência do dinheiro

**Geral**
- Banco de dados SQLite criado automaticamente
- Interface em terminal com menus
- Testes automáticos

## Tecnologias utilizadas

- Python 3.9+
- SQLite / SQL
- pytest (testes automáticos)
- Git

## Estrutura do projeto

```
sistema-de-ponto-de-venda-python/
│
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

## Como rodar os testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Os testes usam um banco temporário e não mexem no `database/loja.db`.

## Objetivos do projeto

Além de desenvolver um sistema funcional para um pequeno comércio, este projeto também tem como objetivo servir como estudo e prática de:

- Organização de projetos em Python
- SQL e SQLite
- Versionamento com Git
- Testes automáticos
- Boas práticas de programação
- Evolução contínua de software

## Próximas funcionalidades

- Histórico de caixas
- Relatórios (vendas por período, produtos mais vendidos)
- Troco no pagamento em dinheiro
- Login de usuários
- Backup do banco de dados
- Impressão de comprovantes
- Interface gráfica

## Autor

Desenvolvido por Alberto Zgraia Neto (MyBad64x).
