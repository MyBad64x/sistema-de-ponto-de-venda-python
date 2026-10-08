# PDV Python
[![Testes](https://github.com/MyBad64x/sistema-de-ponto-de-venda-python/actions/workflows/testes.yml/badge.svg)](https://github.com/MyBad64x/sistema-de-ponto-de-venda-python/actions/workflows/testes.yml)

Sistema de Ponto de Venda (PDV) desenvolvido em Python com SQLite.

Este é meu primeiro projeto completo de software, criado com o objetivo de colocar em prática conceitos de programação, banco de dados e organização de código. O projeto também está sendo utilizado como base para um sistema destinado a um pequeno comércio, por isso continua em desenvolvimento e recebe melhorias constantes.

## Funcionalidades

**Login e usuários**
- Primeiro acesso com cadastro do primeiro usuário dono
- Autenticação por login e senha
- Senha armazenada em hash seguro com PBKDF2-HMAC-SHA256
- Perfis de acesso: dono e operador
- Operador sem acesso a relatórios e ajuste de estoque

**Produtos**
- Cadastro, edição, listagem, desativação e reativação de produtos
- Cadastro de código de barras e busca operacional por código ou nome

**Estoque**
- Reposição por leitura, com registro de custo, fornecedor e referência de compra
- Contagem de estoque por leitura e ajuste manual de inventário, perdas e quebras
- Histórico de todas as movimentações (entradas, ajustes e vendas)
- Área da dona para consultar compras, filtrar estoque e simular preços com custo e lucro bruto

**Vendas**
- Carrinho de compras (adicionar, remover, limpar)
- Leitura de código adiciona uma unidade; é possível desfazer a última leitura
- Finalização de venda com escolha da forma de pagamento e troco no pagamento em dinheiro
- Aviso de estoque insuficiente, com opção de vender mesmo assim
- Comprovante não fiscal em texto, salvo em arquivo e consultável pelo menu de vendas

**Caixa**
- Abertura, sangria, suprimento, status, fechamento com conferência do dinheiro e histórico de caixas

**Relatórios**
- Resumo de vendas, produtos mais vendidos e vendas por dia, por período
- Lucro bruto realizado por período e potencial do estoque atual, na área de gestão da dona

**Geral**
- Banco de dados SQLite criado automaticamente
- Interface em terminal com menus
- Interface desktop experimental com login e janela inicial
- Testes automáticos
- Backup automático ao fechar o caixa, backup manual e restauração
- Login de usuários com perfis de acesso

## Tecnologias utilizadas

- Python 3.10+
- SQLite / SQL
- PySide6 (interface desktop experimental)
- pytest (testes automáticos)
- pytest-qt (testes da interface desktop)
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
│   ├── gestao.py            # consultas administrativas de estoque e rentabilidade
│   ├── precificacao.py      # cálculos de lucro bruto e percentuais
│   ├── backup.py            # backup e restauração do banco
│   ├── comprovante.py       # comprovante de venda em texto
│   │
│   ├── desktop/             # interface desktop experimental em PySide6
│   │   ├── app.py           # inicialização da interface desktop
│   │   ├── login.py         # login e primeiro acesso
│   │   └── janela_principal.py # janela base após autenticação
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

## Interface desktop experimental

Instale as dependências de execução e abra a interface desktop:

```bash
pip install -r requirements.txt
python -m pdv.desktop
```

Esta primeira etapa inclui login, cadastro do primeiro usuário dono e a janela base. Os fluxos completos continuam disponíveis pelo terminal com `python main.py` enquanto são migrados para a interface desktop.

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

- Registro de despesas operacionais, como energia, e taxas de pagamento, se solicitado.
- Interface gráfica

## Autor

Desenvolvido por Alberto Zgraia Neto (MyBad64x).
