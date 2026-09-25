"""Carrinho de compras da venda em andamento.

O carrinho fica só na memória (não vai para o banco) até a venda ser finalizada.
"""

from dataclasses import dataclass

from pdv.caixa import caixa_aberto
from pdv.erros import ErroPDV
from pdv.produtos import buscar_produto


@dataclass
class ItemCarrinho:
    id_produto: int
    nome: str
    quantidade: int
    preco_unitario: float
    estoque: int

    @property
    def subtotal(self):
        return round(self.preco_unitario * self.quantidade, 2)


class Carrinho:

    def __init__(self):
        # {id_produto: quantidade} -> o mesmo produto nunca aparece em duas linhas
        self.itens = {}

    def adicionar(self, id_produto, quantidade):
        """Adiciona (ou soma) um produto e devolve a linha atualizada do carrinho."""
        if quantidade <= 0:
            raise ErroPDV("A quantidade deve ser maior que zero.")

        if caixa_aberto() is None:
            raise ErroPDV("Abra o caixa antes de iniciar uma venda.")

        produto = buscar_produto(id_produto)
        if produto is None:
            raise ErroPDV(f"Produto {id_produto} não encontrado.")
        if not produto["ativo"]:
            raise ErroPDV(f"O produto '{produto['nome']}' está desativado.")

        self.itens[id_produto] = self.itens.get(id_produto, 0) + quantidade

        return self._montar_item(produto)

    def remover(self, id_produto):
        if id_produto not in self.itens:
            raise ErroPDV("Esse produto não está no carrinho.")
        del self.itens[id_produto]

    def limpar(self):
        self.itens.clear()

    def esta_vazio(self):
        return len(self.itens) == 0

    def detalhar(self):
        """Linhas do carrinho com o preço atual de cada produto."""
        return [self._montar_item(buscar_produto(id_produto)) for id_produto in self.itens]

    def total(self):
        return round(sum(item.subtotal for item in self.detalhar()), 2)

    def _montar_item(self, produto):
        return ItemCarrinho(
            id_produto=produto["id"],
            nome=produto["nome"],
            quantidade=self.itens[produto["id"]],
            preco_unitario=produto["preco"],
            estoque=produto["estoque"],
        )
