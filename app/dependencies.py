"""Dependências injetadas nas rotas pelo FastAPI (`Depends`)."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decodificar_token
from app.db.session import get_db
from app.exceptions import AcessoNegado, NaoAutenticado
from app.models import Usuario

SessaoDB = Annotated[Session, Depends(get_db)]

# Lê o header "Authorization: Bearer <token>". O tokenUrl aponta para a rota de
# login e habilita o botão "Authorize" do Swagger. auto_error=False para que a
# própria API gere a resposta 401 no formato padrão de erros.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def obter_usuario_atual(db: SessaoDB, token: Annotated[str | None, Depends(esquema_oauth2)]) -> Usuario:
    """Valida o token JWT e retorna o usuário autenticado.

    401 → token ausente, inválido, expirado ou de usuário inexistente.
    403 → usuário válido, porém desativado.
    """
    if not token:
        raise NaoAutenticado("Token de acesso ausente. Faça login em /auth/login.")

    try:
        payload = decodificar_token(token)
    except jwt.ExpiredSignatureError:
        raise NaoAutenticado("Token de acesso expirado. Faça login novamente.") from None
    except jwt.InvalidTokenError:
        raise NaoAutenticado("Token de acesso inválido.") from None

    usuario = db.scalar(select(Usuario).where(Usuario.username == payload["sub"]))
    if usuario is None:
        raise NaoAutenticado("Token de acesso inválido.")
    if not usuario.ativo:
        raise AcessoNegado("Usuário inativo.")
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(obter_usuario_atual)]

# Para proteger rotas que não precisam do objeto do usuário.
exigir_autenticacao = Depends(obter_usuario_atual)
