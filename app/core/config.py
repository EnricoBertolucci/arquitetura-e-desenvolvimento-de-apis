"""Configurações da aplicação lidas de variáveis de ambiente (arquivo .env).

Centralizar a configuração aqui evita valores sensíveis (chave JWT, senhas)
espalhados pelo código e permite trocar o ambiente sem alterar o fonte.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Hotel API"
    app_version: str = "1.0.0"

    database_url: str = "sqlite:///./hotel.db"

    # Sem valor padrão: a aplicação não sobe sem uma chave definida no ambiente.
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=60, gt=0)

    # Lista separada por vírgula, ex.: "http://localhost:3000,http://localhost:5173"
    cors_origins: str = ""

    admin_username: str | None = None
    admin_password: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única (cacheada) das configurações."""
    return Settings()
