from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import criar_token_acesso, gerar_hash_senha, verificar_senha
from app.dependencies import SessaoDB, UsuarioAtual
from app.exceptions import AcessoNegado, NaoAutenticado
from app.models import Usuario
from app.routers.respostas import respostas
from app.schemas.auth import Token, UsuarioResposta

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Hash usado quando o usuário não existe, para que a resposta leve o mesmo tempo
# de quando a senha está errada (dificulta descobrir usernames válidos).
_HASH_FICTICIO = gerar_hash_senha("senha-ficticia-para-tempo-constante")


@router.post(
    "/login",
    response_model=Token,
    summary="Autentica o usuário e retorna um token JWT",
    description=(
        "Recebe `username` e `password` como formulário (`application/x-www-form-urlencoded`, "
        "padrão OAuth2). O token retornado deve ser enviado nas rotas protegidas no header "
        "`Authorization: Bearer <token>`."
    ),
    responses=respostas(400, 401, 403),
)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessaoDB) -> Token:
    usuario = db.scalar(select(Usuario).where(Usuario.username == form.username))
    senha_correta = verificar_senha(form.password, usuario.senha_hash if usuario else _HASH_FICTICIO)

    # Mesma mensagem para usuário inexistente e senha errada.
    if usuario is None or not senha_correta:
        raise NaoAutenticado("Usuário ou senha incorretos.")
    if not usuario.ativo:
        raise AcessoNegado("Usuário inativo.")

    settings = get_settings()
    return Token(
        access_token=criar_token_acesso(usuario.username),
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UsuarioResposta,
    summary="Retorna o usuário autenticado",
    responses=respostas(401, 403),
)
def usuario_logado(usuario: UsuarioAtual):
    return usuario
