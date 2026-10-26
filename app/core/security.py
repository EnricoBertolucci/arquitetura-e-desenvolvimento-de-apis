"""Funções de segurança: hash e verificação de senhas com bcrypt.

O bcrypt gera um "salt" aleatório por senha e é propositalmente lento,
dificultando ataques de força bruta caso o banco seja exposto.
"""

import bcrypt

# O bcrypt considera no máximo 72 bytes da senha.
TAMANHO_MAXIMO_SENHA_BYTES = 72


def gerar_hash_senha(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > TAMANHO_MAXIMO_SENHA_BYTES:
        raise ValueError("A senha excede o limite de 72 bytes do bcrypt.")
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        # Senha acima do limite ou hash em formato inválido.
        return False
