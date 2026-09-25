"""Erros de regra de negócio do PDV.

As funções de negócio levantam (raise) estes erros em vez de imprimir mensagens.
Quem chama decide o que fazer: o terminal mostra a mensagem, os testes verificam
que o erro aconteceu, uma futura interface gráfica pode abrir uma janela de aviso.
"""


class ErroPDV(Exception):
    """Erro esperado de uso do sistema (dado inválido, operação não permitida)."""


class EstoqueInsuficiente(ErroPDV):
    """A venda pediria mais unidades do que há em estoque."""

    def __init__(self, nome_produto, disponivel, pedido):
        self.nome_produto = nome_produto
        self.disponivel = disponivel
        self.pedido = pedido
        super().__init__(
            f"Estoque insuficiente para {nome_produto} "
            f"(disponível: {disponivel}, no carrinho: {pedido})."
        )
