"""Funções de segurança: hash de senhas (bcrypt) e tokens de acesso (JWT).

O bcrypt gera um "salt" aleatório por senha e é propositalmente lento,
dificultando ataques de força bruta caso o banco seja exposto.

O JWT é assinado com a chave JWT_SECRET_KEY (HMAC-SHA256 por padrão): o
servidor não guarda sessão; a cada requisição ele confere a assinatura e a
validade (claim "exp") do token enviado no header Authorization.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

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


def criar_token_acesso(username: str, expira_em: timedelta | None = None) -> str:
    """Gera um JWT assinado cujo "sub" (subject) é o username do usuário."""
    settings = get_settings()
    agora = datetime.now(UTC)
    validade = expira_em if expira_em is not None else timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "iat": agora, "exp": agora + validade}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict[str, Any]:
    """Valida assinatura e expiração do token e retorna o payload.

    Lança `jwt.ExpiredSignatureError` se o token estiver expirado e
    `jwt.InvalidTokenError` para qualquer outro problema.
    """
    settings = get_settings()
    # A lista de algoritmos é fixa: impede que o token escolha o algoritmo
    # (ex.: "none") usado na verificação.
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "exp"]},
    )
