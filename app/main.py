"""Ponto de entrada da Hotel API.

Executar com:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings
from app.exceptions import registrar_handlers
from app.routers import auth, hospedes, quartos, reservas

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST para gestão de quartos, hóspedes e reservas de um hotel.",
)

# CORS: somente as origens listadas em CORS_ORIGINS, com os métodos e
# cabeçalhos efetivamente usados pela API. O token JWT trafega no header
# Authorization (não em cookies), por isso allow_credentials=False.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    # Permite que o front-end leia o endereço do recurso criado (respostas 201).
    expose_headers=["Location"],
    allow_credentials=False,
    max_age=600,
)

registrar_handlers(app)

app.include_router(auth.router)
app.include_router(quartos.router)
app.include_router(hospedes.router)
app.include_router(reservas.router)


@app.get("/", tags=["Status"], summary="Verifica se a API está no ar")
def status_api() -> dict[str, str]:
    return {"status": "ok", "api": settings.app_name, "versao": settings.app_version}


def _gerar_openapi() -> dict:
    """Gera o OpenAPI sem as respostas 422 que o FastAPI adiciona por padrão.

    A API converte os erros de validação para 400 (ver app/exceptions.py), então
    o 422 nunca é retornado e não deve aparecer na documentação.
    """
    if app.openapi_schema:
        return app.openapi_schema

    esquema = get_openapi(
        title=app.title, version=app.version, description=app.description, routes=app.routes
    )
    for operacoes in esquema.get("paths", {}).values():
        for operacao in operacoes.values():
            operacao.get("responses", {}).pop("422", None)
    for nome in ("HTTPValidationError", "ValidationError"):
        esquema.get("components", {}).get("schemas", {}).pop(nome, None)

    app.openapi_schema = esquema
    return esquema


app.openapi = _gerar_openapi
