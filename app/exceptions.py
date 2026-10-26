"""Exceções de domínio e handlers globais de erro.

Todas as respostas de erro da API seguem o mesmo formato JSON:

    {"detail": "mensagem"}                                   # erros em geral
    {"detail": "Dados inválidos.", "erros": [{"campo", "mensagem"}]}  # validação

As camadas de serviço lançam as exceções abaixo sem conhecer HTTP; os handlers
registrados em `registrar_handlers` as convertem no código de status adequado.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.comum import ErroDeCampo

logger = logging.getLogger(__name__)

MENSAGEM_DADOS_INVALIDOS = "Dados inválidos."


class ErroAPI(Exception):
    """Base das exceções de domínio: carrega o código HTTP e a mensagem."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class RecursoNaoEncontrado(ErroAPI):
    status_code = status.HTTP_404_NOT_FOUND


class Conflito(ErroAPI):
    """Violação de unicidade ou de regra de negócio (sobreposição, dependências)."""

    status_code = status.HTTP_409_CONFLICT


class DadosInvalidos(ErroAPI):
    """Erro de validação que depende do banco (ex.: capacidade do quarto)."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, campo: str, mensagem: str) -> None:
        super().__init__(MENSAGEM_DADOS_INVALIDOS)
        self.erros = [{"campo": campo, "mensagem": mensagem}]


class NaoAutenticado(ErroAPI):
    status_code = status.HTTP_401_UNAUTHORIZED


class AcessoNegado(ErroAPI):
    status_code = status.HTTP_403_FORBIDDEN


# Tradução das mensagens padrão do Pydantic (em inglês) para português.
_MENSAGENS_PYDANTIC: dict[str, str] = {
    "missing": "Campo obrigatório.",
    "extra_forbidden": "Campo não permitido.",
    "string_type": "Deve ser um texto.",
    "string_too_short": "Deve ter no mínimo {min_length} caractere(s).",
    "string_too_long": "Deve ter no máximo {max_length} caractere(s).",
    "string_pattern_mismatch": "Formato inválido.",
    "int_type": "Deve ser um número inteiro.",
    "int_parsing": "Deve ser um número inteiro.",
    "int_from_float": "Deve ser um número inteiro.",
    "float_type": "Deve ser um número.",
    "float_parsing": "Deve ser um número.",
    "decimal_type": "Deve ser um número.",
    "decimal_parsing": "Deve ser um número.",
    "decimal_max_digits": "Deve ter no máximo {max_digits} dígitos.",
    "decimal_max_places": "Deve ter no máximo {decimal_places} casas decimais.",
    "decimal_whole_digits": "Deve ter no máximo {whole_digits} dígitos antes da vírgula.",
    "bool_type": "Deve ser verdadeiro ou falso.",
    "bool_parsing": "Deve ser verdadeiro ou falso.",
    "date_type": "Deve ser uma data no formato AAAA-MM-DD.",
    "date_parsing": "Deve ser uma data no formato AAAA-MM-DD.",
    "date_from_datetime_parsing": "Deve ser uma data no formato AAAA-MM-DD.",
    "date_from_datetime_inexact": "Deve ser uma data, sem horário.",
    "greater_than": "Deve ser maior que {gt}.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than": "Deve ser menor que {lt}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "model_attributes_type": "Deve ser um objeto JSON.",
    "dict_type": "Deve ser um objeto JSON.",
    "model_type": "Deve ser um objeto JSON.",
}


def _formatar_erro_validacao(erro: dict[str, Any]) -> dict[str, str]:
    # A localização vem como ("body", "campo") ou ("query", "campo"); o prefixo
    # é descartado para que o cliente veja apenas o nome do campo.
    partes = [str(p) for p in erro.get("loc", ()) if p not in ("body", "query", "path", "header")]
    campo = ".".join(partes) or "corpo"

    tipo = erro.get("type", "")
    contexto = erro.get("ctx") or {}

    if tipo == "json_invalid":
        return {"campo": "corpo", "mensagem": "JSON malformado."}

    if tipo == "value_error" and "error" in contexto:
        # Mensagem escrita pelos validadores dos schemas.
        excecao = contexto["error"]
        if isinstance(excecao, ErroDeCampo):
            campo = excecao.campo
        mensagem = str(excecao)
    elif tipo == "value_error" and "reason" in contexto:
        # Erro do validador de e-mail (EmailStr).
        mensagem = "E-mail inválido."
    elif tipo == "enum":
        opcoes = str(contexto.get("expected", "")).replace(" or ", " ou ")
        mensagem = f"Valor inválido. Opções: {opcoes}."
    elif tipo in _MENSAGENS_PYDANTIC:
        try:
            mensagem = _MENSAGENS_PYDANTIC[tipo].format(**contexto)
        except (KeyError, IndexError):
            mensagem = erro.get("msg", "Valor inválido.")
    else:
        mensagem = erro.get("msg", "Valor inválido.")

    return {"campo": campo, "mensagem": mensagem}


async def _tratar_erro_api(_request: Request, exc: ErroAPI) -> JSONResponse:
    conteudo: dict[str, Any] = {"detail": exc.detail}
    if isinstance(exc, DadosInvalidos):
        conteudo["erros"] = exc.erros

    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, NaoAutenticado) else None
    return JSONResponse(status_code=exc.status_code, content=conteudo, headers=headers)


async def _tratar_erro_validacao(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # O FastAPI responde 422 por padrão; a API adota 400 para dados inválidos.
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": MENSAGEM_DADOS_INVALIDOS,
            "erros": [_formatar_erro_validacao(e) for e in exc.errors()],
        },
    )


async def _tratar_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Erros gerados pelo próprio framework (rota inexistente, método não permitido...).
    mensagens = {
        status.HTTP_404_NOT_FOUND: "Rota não encontrada.",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Método HTTP não permitido para esta rota.",
    }
    detail = exc.detail if exc.detail not in (None, "Not Found", "Method Not Allowed") else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail or mensagens.get(exc.status_code, "Erro na requisição.")},
        headers=getattr(exc, "headers", None),
    )


async def _tratar_integridade(_request: Request, exc: IntegrityError) -> JSONResponse:
    # Rede de segurança: os serviços já verificam unicidade e dependências antes
    # de gravar, mas o banco é a última barreira (ex.: duas requisições simultâneas).
    logger.warning("Violação de integridade no banco: %s", exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "A operação viola uma restrição de integridade dos dados."},
    )


async def _tratar_erro_inesperado(_request: Request, exc: Exception) -> JSONResponse:
    # O detalhe técnico vai apenas para o log do servidor, nunca para o cliente.
    logger.exception("Erro inesperado", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor."},
    )


def registrar_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ErroAPI, _tratar_erro_api)
    app.add_exception_handler(RequestValidationError, _tratar_erro_validacao)
    app.add_exception_handler(StarletteHTTPException, _tratar_http_exception)
    app.add_exception_handler(IntegrityError, _tratar_integridade)
    app.add_exception_handler(Exception, _tratar_erro_inesperado)
