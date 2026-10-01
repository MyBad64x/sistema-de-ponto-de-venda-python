"""Regras de negócio para cadastro e autenticação e usuários."""

import hashlib
import hmac
import secrets
import sqlite3

from pdv.banco import conexao
from pdv.erros import ErroPDV


ALGORITMO_HASH = "pbkdf2_sha256"
ITERACOES_HASH = 600_000
TAMANHO_SALT = 16
TAMANHO_HASH = 32
PERFIS_VALIDOS = ("dono", "operador")


def _gerar_hash(senha):
    salt = secrets.token_bytes(TAMANHO_SALT)
    resultado = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        ITERACOES_HASH,
        dklen=TAMANHO_HASH,
    )

    return(
        f"{ALGORITMO_HASH}${ITERACOES_HASH}"
        f"${salt.hex()}${resultado.hex()}"
    )


def _senha_confere(senha, senha_hash):
    try:
        algoritmo, texto_iteracoes, texto_salt, texto_hash = senha_hash.split("$")

        if algoritmo != ALGORITMO_HASH:
            return False

        iteracoes = int(texto_iteracoes)
        salt = bytes.fromhex(texto_salt)
        hash_esperado = bytes.fromhex(texto_hash)

        if (
            iteracoes <= 0
            or len(salt) != TAMANHO_SALT
            or len(hash_esperado) != TAMANHO_HASH 
        ):
            return False

        hash_calculado = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            salt,
            iteracoes,
            dklen=len(hash_esperado),
        )

        return hmac.compare_digest(hash_calculado, hash_esperado)

    except (TypeError, ValueError):
        return False


def _validar_texto(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ErroPDV(f"{campo} não pode ficar vazio.")


def _validar_senha(senha):
    if not isinstance(senha, str) or len(senha) < 8:
        raise ErroPDV("A senha deve ter pelo menos 8 caracteres.")


def criar_usuario(nome, login, senha, perfil):
    """Cria um usuário e retorna seu ID."""

    _validar_texto(nome, "O nome")
    _validar_texto(login, "O login")
    _validar_senha(senha)

    nome = nome.strip()
    login = login.strip().lower()

    if perfil not in PERFIS_VALIDOS:
        raise ErroPDV("Perfil de usuário inválido.")

    senha_hash = _gerar_hash(senha)

    try:
        with conexao() as conn:
            cursor = conn.execute(
                """
                INSERT INTO usuarios(nome, login, senha_hash, perfil)
                VALUES (?, ?, ?, ?)
                """,
                (nome, login, senha_hash, perfil)
            )
            return cursor.lastrowid

    except sqlite3.IntegrityError as erro:
        if "usuarios.login" in str(erro) or "UNIQUE constraint" in str(erro):
            raise ErroPDV("Este login já está cadastrado.") from erro
        raise


def autenticar(login, senha):
    """Retorna os dados do usuário autenticado ou None."""

    if not isinstance(login, str) or not isinstance(senha, str):
        return None

    login = login.strip().lower()

    if not login or not senha:
        return None

    with conexao() as conn:
        usuario = conn.execute(
            """
            SELECT id, nome, login, senha_hash, perfil, ativo
            FROM usuarios
            WHERE login = ?
            """,
            (login,),
        ).fetchone()

    if usuario is None or not usuario["ativo"]:
        return None

    if not _senha_confere(senha, usuario["senha_hash"]):
        return None

    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "login": usuario["login"],
        "perfil": usuario["perfil"],
        "ativo": usuario["ativo"],
    }