from pydantic import BaseModel

from app.schemas.comum import DataHoraUTC, SchemaSaida


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # validade em segundos


class UsuarioResposta(SchemaSaida):
    id: int
    username: str
    ativo: bool
    criado_em: DataHoraUTC
