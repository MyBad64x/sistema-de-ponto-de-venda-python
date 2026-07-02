# PDV Python

Sistema de Ponto de Venda (PDV) desenvolvido em Python com SQLite.

Este é meu primeiro projeto completo de software, criado com o objetivo de colocar em prática conceitos de programação, banco de dados e organização de código. O projeto também está sendo utilizado como base para um sistema destinado a um pequeno comércio, por isso continua em desenvolvimento e recebe melhorias constantes.

## Funcionalidades

Atualmente o sistema possui:

- Cadastro de produtos
- Edição de produtos
- Desativação de produtos
- Listagem de produtos
- Controle de estoque
- Entrada de estoque
- Ajuste de estoque
- Histórico de movimentações
- Carrinho de compras
- Finalização de vendas
- Controle de caixa
- Registro de movimentações de estoque
- Banco de dados SQLite
- Interface em terminal com menus

## Tecnologias utilizadas

- Python 3
- SQLite
- SQL
- Git (em desenvolvimento)

## Estrutura do projeto

```
PDV_LOJA/
│
├── banco.py
├── caixa.py
├── carrinho.py
├── movimentacoes_estoque.py
├── produtos.py
├── vendas.py
├── main.py
│
├── database/
├── testes/
└── docs/
```

## Como executar

1. Clone este repositório.

```bash
git clone https://github.com/SEU-USUARIO/pdv-python.git
```

2. Acesse a pasta do projeto.

```bash
cd pdv-python
```

3. Execute o arquivo principal.

```bash
python main.py
```

## Objetivos do projeto

Além de desenvolver um sistema funcional para um pequeno comércio, este projeto também tem como objetivo servir como estudo e prática de:

- Organização de projetos em Python
- SQL e SQLite
- Versionamento com Git
- Boas práticas de programação
- Evolução contínua de software

## Próximas funcionalidades

- Fechamento de caixa aprimorado
- Relatórios
- Login de usuários
- Interface gráfica
- Impressão de comprovantes
- Backup do banco de dados

## Autor

Desenvolvido por Alberto Zgraia Neto (MyBad64x).