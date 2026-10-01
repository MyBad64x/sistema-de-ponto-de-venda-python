import sqlite3

import pytest

from pdv.banco import conexao
from pdv.erros import ErroPDV
from pdv.usuarios import autenticar, criar_usuario


def test_cria_usuario_e_nao_expoe_senha():
    id_usuario = criar_usuario(
        " Alberto ",
        " Alberto ",
        "senha-segura",
        "dono",
    )

    with conexao() as conn:
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (id_usuario,),
        ).fetchone()

    assert usuario["nome"] == "Alberto"
    assert usuario["login"] == "alberto"
    assert usuario["perfil"] == "dono"
    assert usuario["senha_hash"] != "senha-segura"
    assert "senha-segura" not in usuario["senha_hash"]


def test_mesma_senha_usa_salts_diferentes():
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")
    criar_usuario("Operador", "operador", "senha-segura", "operador")

    with conexao() as conn:
        hashes = [
            linha["senha_hash"]
            for linha in conn.execute("SELECT senha_hash FROM usuarios")
        ]

    assert len(hashes) == 2
    assert hashes[0] != hashes[1]


def test_autentica_usuario_com_senha_correta():
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")

    usuario = autenticar("alberto", "senha-segura")

    assert usuario == {
        "id": 1,
        "nome": "Alberto",
        "login": "alberto",
        "perfil": "dono",
        "ativo": 1,
    }


@pytest.mark.parametrize("senha", ["senha-errada", "", "12345678"])
def test_rejeita_senha_incorreta(senha):
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")

    assert autenticar("alberto", senha) is None


def test_login_nao_existe():
    assert autenticar("inexistente", "senha-segura") is None


def test_login_ignora_maiusculas_e_espacos():
    criar_usuario("Alberto", "Alberto", "senha-segura", "dono")

    usuario = autenticar("  ALBERTO  ", "senha-segura")

    assert usuario["login"] == "alberto"


def test_usuario_inativo_nao_consegue_autenticar():
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")

    with conexao() as conn:
        conn.execute(
            "UPDATE usuarios SET ativo = 0 WHERE login = ?",
            ("alberto",),
        )

    assert autenticar("alberto", "senha-segura") is None


def test_login_duplicado_e_rejeitado():
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")

    with pytest.raises(ErroPDV, match="login já está cadastrado"):
        criar_usuario("Outro", "ALBERTO", "outra-senha", "operador")


@pytest.mark.parametrize(
    "nome, login, senha, perfil",
    [
        ("", "alberto", "senha-segura", "dono"),
        ("Alberto", "", "senha-segura", "dono"),
        ("Alberto", "alberto", "curta", "dono"),
        ("Alberto", "alberto", "senha-segura", "gerente"),
    ],
)
def test_rejeita_dados_invalidos(nome, login, senha, perfil):
    with pytest.raises(ErroPDV):
        criar_usuario(nome, login, senha, perfil)


def test_hash_malformado_falha_como_autenticacao():
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")

    with conexao() as conn:
        conn.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE login = ?",
            ("hash-invalido", "alberto"),
        )

    assert autenticar("alberto", "senha-segura") is None


def test_autenticacao_nao_retorna_hash_da_senha():
    criar_usuario("Alberto", "alberto", "senha-segura", "dono")

    usuario = autenticar("alberto", "senha-segura")

    assert "senha_hash" not in usuario


def test_banco_rejeita_perfil_invalido():
    with pytest.raises(sqlite3.IntegrityError):
        with conexao() as conn:
            conn.execute(
                """
                INSERT INTO usuarios(nome, login, senha_hash, perfil)
                VALUES (?, ?, ?, ?)
                """,
                ("Teste", "teste", "hash", "gerente"),
            )