"""Documentação (OpenAPI) das respostas de erro, reutilizada pelas rotas."""

from typing import Any

from pydantic import BaseModel


class ErroResposta(BaseModel):
    detail: str


class ErroCampo(BaseModel):
    campo: str
    mensagem: str


class ErroValidacaoResposta(BaseModel):
    detail: str
    erros: list[ErroCampo]


_DESCRICOES: dict[int, tuple[str, type[BaseModel]]] = {
    400: ("Dados inválidos.", ErroValidacaoResposta),
    401: ("Token ausente, inválido ou expirado.", ErroResposta),
    403: ("Usuário sem permissão (inativo).", ErroResposta),
    404: ("Recurso não encontrado.", ErroResposta),
    409: ("Conflito com o estado atual dos dados.", ErroResposta),
}


def respostas(*codigos: int) -> dict[int | str, dict[str, Any]]:
    return {c: {"description": _DESCRICOES[c][0], "model": _DESCRICOES[c][1]} for c in codigos}
