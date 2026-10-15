"""Ponto de entrada da Hotel API.

Executar com:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

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
    allow_credentials=False,
)


@app.get("/", tags=["Status"], summary="Verifica se a API está no ar")
def status_api() -> dict[str, str]:
    return {"status": "ok", "api": settings.app_name, "versao": settings.app_version}
