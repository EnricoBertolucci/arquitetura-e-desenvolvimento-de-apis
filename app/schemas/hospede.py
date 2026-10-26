from datetime import date
from typing import Annotated

from pydantic import EmailStr, Field, field_validator

from app.schemas.comum import (
    DataHoraUTC,
    SchemaAtualizacao,
    SchemaEntrada,
    SchemaSaida,
    cpf_valido,
    somente_digitos,
)

Nome = Annotated[str, Field(min_length=3, max_length=120, examples=["Maria Oliveira"])]
Cpf = Annotated[
    str,
    Field(description="CPF com ou sem máscara; é armazenado somente com dígitos.", examples=["529.982.247-25"]),
]
Email = Annotated[EmailStr, Field(max_length=254, examples=["maria.oliveira@example.com"])]
Telefone = Annotated[str, Field(description="DDD + número, com ou sem máscara.", examples=["(41) 99999-0000"])]


def _validar_cpf(valor: str) -> str:
    cpf = somente_digitos(valor)
    if not cpf_valido(cpf):
        raise ValueError("CPF inválido.")
    return cpf


def _validar_telefone(valor: str) -> str:
    telefone = somente_digitos(valor)
    if len(telefone) not in (10, 11):
        raise ValueError("Telefone deve ter 10 ou 11 dígitos (DDD + número).")
    return telefone


def _validar_nascimento(valor: date) -> date:
    if valor >= date.today():
        raise ValueError("A data de nascimento deve estar no passado.")
    return valor


class HospedeCriacao(SchemaEntrada):
    nome: Nome
    cpf: Cpf
    email: Email
    telefone: Telefone | None = None
    data_nascimento: date | None = None

    @field_validator("cpf")
    @classmethod
    def _cpf(cls, valor: str) -> str:
        return _validar_cpf(valor)

    @field_validator("email")
    @classmethod
    def _email(cls, valor: str) -> str:
        return valor.lower()

    @field_validator("telefone")
    @classmethod
    def _telefone(cls, valor: str | None) -> str | None:
        return _validar_telefone(valor) if valor else None

    @field_validator("data_nascimento")
    @classmethod
    def _nascimento(cls, valor: date | None) -> date | None:
        return _validar_nascimento(valor) if valor else None


class HospedeAtualizacao(SchemaAtualizacao):
    campos_nao_nulos = ("nome", "cpf", "email")

    nome: Nome | None = None
    cpf: Cpf | None = None
    email: Email | None = None
    telefone: Telefone | None = None
    data_nascimento: date | None = None

    @field_validator("cpf")
    @classmethod
    def _cpf(cls, valor: str | None) -> str | None:
        return _validar_cpf(valor) if valor is not None else None

    @field_validator("email")
    @classmethod
    def _email(cls, valor: str | None) -> str | None:
        return valor.lower() if valor else valor

    @field_validator("telefone")
    @classmethod
    def _telefone(cls, valor: str | None) -> str | None:
        return _validar_telefone(valor) if valor else None

    @field_validator("data_nascimento")
    @classmethod
    def _nascimento(cls, valor: date | None) -> date | None:
        return _validar_nascimento(valor) if valor else None


class HospedeResposta(SchemaSaida):
    id: int
    nome: str
    cpf: str
    email: str
    telefone: str | None
    data_nascimento: date | None
    criado_em: DataHoraUTC
    atualizado_em: DataHoraUTC


class HospedeResumo(SchemaSaida):
    """Representação reduzida do hóspede, embutida nas reservas."""

    id: int
    nome: str
    email: str
