"""Tipos e validadores reutilizados pelos schemas."""

import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, model_validator

# Valores monetários: Decimal na validação (sem erro de arredondamento) e
# número no JSON de saída.
Dinheiro = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]



def _assumir_utc(valor: datetime) -> datetime:
    # O SQLite não guarda fuso horário; as datas de auditoria são gravadas em UTC.
    return valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor


DataHoraUTC = Annotated[datetime, AfterValidator(_assumir_utc)]


class ErroDeCampo(ValueError):
    """Erro de validação em nível de modelo que se refere a um campo específico."""

    def __init__(self, campo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.campo = campo


class SchemaEntrada(BaseModel):
    """Base dos schemas de entrada: remove espaços extras e rejeita campos desconhecidos."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class SchemaAtualizacao(SchemaEntrada):
    """Base dos schemas de PATCH.

    Todos os campos são opcionais (o cliente envia só o que quer alterar), mas
    os listados em `campos_nao_nulos` não podem ser enviados como `null`, pois
    são obrigatórios no banco.
    """

    campos_nao_nulos: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _rejeitar_nulos(self):
        for campo in self.campos_nao_nulos:
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ErroDeCampo(campo, "Não pode ser nulo.")
        return self

    @model_validator(mode="after")
    def _exigir_algum_campo(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class SchemaSaida(BaseModel):
    """Base dos schemas de resposta: lê os dados diretamente dos objetos ORM."""

    model_config = ConfigDict(from_attributes=True)


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def cpf_valido(cpf: str) -> bool:
    """Valida os dois dígitos verificadores de um CPF com 11 dígitos."""
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[tamanho]):
            return False
    return True


PaginacaoSkip = Annotated[int, Field(ge=0, description="Quantidade de registros a pular.")]
PaginacaoLimit = Annotated[int, Field(ge=1, le=100, description="Quantidade máxima de registros (1 a 100).")]
