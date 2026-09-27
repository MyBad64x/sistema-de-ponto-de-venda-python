"""Backup e restauração do banco de dados.

Os backups ficam em database/backups/, ao lado do loja.db, com a data e a hora no
nome: loja_2026-09-27_14-08-33.db. Cada backup é um banco SQLite completo, que
pode ser aberto sozinho.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from pdv.banco import caminho_banco, criar_tabelas
from pdv.erros import ErroPDV

MANTER_BACKUPS = 30
TABELAS_OBRIGATORIAS = {"produtos", "vendas", "caixa"}


@dataclass
class InfoBackup:
    caminho: object  # Path do arquivo
    criado_em: datetime
    tamanho_kb: int


def pasta_backups():
    return caminho_banco().parent / "backups"


def _copiar_banco(de, para):
    """Copia um banco SQLite para outro com a API de backup do próprio SQLite.

    Diferente de copiar o arquivo, ela gera uma cópia consistente mesmo que o
    banco esteja aberto por outra conexão no meio de uma gravação.
    """
    origem = sqlite3.connect(de)
    destino = sqlite3.connect(para)
    try:
        origem.backup(destino)
    finally:
        destino.close()
        origem.close()


def fazer_backup(agora=None, apagar_antigos=True):
    """Cria um backup do banco atual e devolve o caminho do arquivo criado.

    Depois, apaga os backups mais antigos, mantendo só os MANTER_BACKUPS mais recentes.
    """
    agora = agora or datetime.now()
    pasta = pasta_backups()

    # sem ":" no nome, porque o Windows não aceita esse caractere em arquivos
    nome = f"loja_{agora:%Y-%m-%d_%H-%M-%S}"
    destino = pasta / f"{nome}.db"

    # dois backups no mesmo segundo: loja_..._2.db, loja_..._3.db
    contador = 2
    while destino.exists():
        destino = pasta / f"{nome}_{contador}.db"
        contador += 1

    # erros de disco (sem espaço, sem permissão...) viram ErroPDV com mensagem clara
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        _copiar_banco(caminho_banco(), destino)
    except (OSError, sqlite3.Error) as erro:
        raise ErroPDV(f"Não foi possível fazer o backup: {erro}")

    if apagar_antigos:
        _apagar_antigos()

    return destino


def _arquivos_de_backup():
    """Arquivos de backup do mais antigo para o mais recente.

    O nome começa com a data no formato ano-mês-dia, então a ordem alfabética
    é também a ordem cronológica.
    """
    return sorted(pasta_backups().glob("loja_*.db"))


def _apagar_antigos():
    arquivos = _arquivos_de_backup()
    for arquivo in arquivos[:-MANTER_BACKUPS]:
        arquivo.unlink()


def listar_backups():
    """Backups do mais recente para o mais antigo."""
    backups = []

    for arquivo in reversed(_arquivos_de_backup()):
        info = arquivo.stat()
        backups.append(InfoBackup(
            caminho=arquivo,
            criado_em=datetime.fromtimestamp(info.st_mtime),
            tamanho_kb=max(1, round(info.st_size / 1024)),
        ))

    return backups


def _validar_backup(caminho):
    if not caminho.exists():
        raise ErroPDV(f"Arquivo de backup não encontrado: {caminho.name}")

    try:
        conn = sqlite3.connect(caminho)
        try:
            tabelas = {
                linha[0]
                for linha in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        raise ErroPDV(f"{caminho.name} não é um banco de dados válido.")

    if not TABELAS_OBRIGATORIAS <= tabelas:
        raise ErroPDV(f"{caminho.name} não é um backup do PDV.")


def restaurar_backup(caminho):
    """Substitui o banco atual pelo backup escolhido.

    Antes, faz um backup do estado atual; se a restauração foi um engano,
    dá para voltar restaurando esse backup. Devolve o caminho dele.
    """
    _validar_backup(caminho)

    # sem apagar antigos: se o backup escolhido for o mais antigo, a limpeza
    # automática o apagaria antes de ele ser restaurado
    backup_de_seguranca = fazer_backup(apagar_antigos=False)
    _copiar_banco(caminho, caminho_banco())

    # um backup de uma versão anterior do sistema pode precisar de migração
    criar_tabelas()

    return backup_de_seguranca
