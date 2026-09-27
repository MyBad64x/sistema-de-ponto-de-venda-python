import sqlite3
from datetime import datetime, timedelta

import pytest

from pdv.backup import fazer_backup, listar_backups, pasta_backups, restaurar_backup
from pdv.erros import ErroPDV
from pdv.produtos import cadastrar_produto, listar_produtos

UMA_DATA = datetime(2026, 9, 27, 14, 8, 33)


def _nomes_dos_produtos(caminho=None):
    """Produtos do banco atual ou, se passar um caminho, de um arquivo de backup."""
    if caminho is None:
        return [produto["nome"] for produto in listar_produtos()]

    conn = sqlite3.connect(caminho)
    try:
        return [linha[0] for linha in conn.execute("SELECT nome FROM produtos ORDER BY nome")]
    finally:
        conn.close()


# ---------------------------------------------------------------- fazer backup

def test_backup_cria_arquivo_com_data_e_hora_no_nome():
    caminho = fazer_backup(agora=UMA_DATA)

    assert caminho.exists()
    assert caminho.parent == pasta_backups()
    assert caminho.name == "loja_2026-09-27_14-08-33.db"


def test_backup_tem_os_dados_do_momento_em_que_foi_feito(coca):
    caminho = fazer_backup()

    cadastrar_produto("Depois do backup", 1, 0)

    assert _nomes_dos_produtos(caminho) == ["Coca-Cola 2L"]
    assert _nomes_dos_produtos() == ["Coca-Cola 2L", "Depois do backup"]


def test_dois_backups_no_mesmo_segundo_nao_se_sobrescrevem():
    primeiro = fazer_backup(agora=UMA_DATA)
    segundo = fazer_backup(agora=UMA_DATA)

    assert primeiro.name == "loja_2026-09-27_14-08-33.db"
    assert segundo.name == "loja_2026-09-27_14-08-33_2.db"


def test_mantem_so_os_backups_mais_recentes(monkeypatch):
    monkeypatch.setattr("pdv.backup.MANTER_BACKUPS", 3)

    for dia in range(5):
        fazer_backup(agora=UMA_DATA + timedelta(days=dia))

    nomes = [backup.caminho.name for backup in listar_backups()]

    assert nomes == [
        "loja_2026-10-01_14-08-33.db",
        "loja_2026-09-30_14-08-33.db",
        "loja_2026-09-29_14-08-33.db",
    ]


def test_falha_de_disco_vira_erro_do_pdv(monkeypatch):
    def disco_cheio(de, para):
        raise OSError("No space left on device")

    monkeypatch.setattr("pdv.backup._copiar_banco", disco_cheio)

    with pytest.raises(ErroPDV, match="Não foi possível fazer o backup"):
        fazer_backup()


def test_listar_sem_backups():
    assert listar_backups() == []


# ---------------------------------------------------------------- restaurar

def test_restaurar_volta_os_dados_do_backup(coca):
    backup = fazer_backup(agora=UMA_DATA)
    cadastrar_produto("Cadastrado depois", 1, 0)

    restaurar_backup(backup)

    assert _nomes_dos_produtos() == ["Coca-Cola 2L"]


def test_restaurar_faz_backup_do_estado_atual_antes(coca):
    backup = fazer_backup(agora=UMA_DATA)
    cadastrar_produto("Cadastrado depois", 1, 0)

    seguranca = restaurar_backup(backup)

    # o estado de antes da restauração não se perdeu
    assert _nomes_dos_produtos(seguranca) == ["Cadastrado depois", "Coca-Cola 2L"]


def test_restaurar_o_backup_mais_antigo_com_a_pasta_cheia(monkeypatch, coca):
    """A limpeza automática não pode apagar o backup que está sendo restaurado."""
    monkeypatch.setattr("pdv.backup.MANTER_BACKUPS", 3)

    mais_antigo = fazer_backup(agora=UMA_DATA)
    cadastrar_produto("Depois", 1, 0)
    fazer_backup(agora=UMA_DATA + timedelta(days=1))
    fazer_backup(agora=UMA_DATA + timedelta(days=2))

    restaurar_backup(mais_antigo)

    assert _nomes_dos_produtos() == ["Coca-Cola 2L"]


def test_restaurar_arquivo_inexistente():
    with pytest.raises(ErroPDV, match="não encontrado"):
        restaurar_backup(pasta_backups() / "loja_nao_existe.db")


def test_restaurar_arquivo_que_nao_e_banco(tmp_path, coca):
    falso = tmp_path / "falso.db"
    falso.write_text("isto não é um banco de dados")

    with pytest.raises(ErroPDV, match="não é um banco de dados válido"):
        restaurar_backup(falso)

    assert _nomes_dos_produtos() == ["Coca-Cola 2L"]  # nada mudou


def test_restaurar_banco_que_nao_e_do_pdv(tmp_path, coca):
    outro = tmp_path / "outro.db"
    conn = sqlite3.connect(outro)
    conn.execute("CREATE TABLE clientes(id INTEGER)")
    conn.commit()
    conn.close()

    with pytest.raises(ErroPDV, match="não é um backup do PDV"):
        restaurar_backup(outro)

    assert _nomes_dos_produtos() == ["Coca-Cola 2L"]
