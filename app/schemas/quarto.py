from typing import Annotated

from pydantic import Field, field_validator

from app.models.enums import TipoQuarto
from app.schemas.comum import DataHoraUTC, Dinheiro, SchemaAtualizacao, SchemaEntrada, SchemaSaida

NumeroQuarto = Annotated[
    str,
    Field(
        min_length=1,
        max_length=10,
        pattern=r"^[0-9A-Za-z-]+$",
        description="Identificação do quarto: letras, números e hífen.",
        examples=["101"],
    ),
]
Capacidade = Annotated[int, Field(ge=1, le=10, description="Número máximo de hóspedes.", examples=[2])]
PrecoDiaria = Annotated[
    Dinheiro, Field(gt=0, max_digits=10, decimal_places=2, description="Valor da diária em reais.", examples=[250.0])
]
Andar = Annotated[int, Field(ge=0, le=200, examples=[1])]
Descricao = Annotated[str, Field(max_length=500, examples=["Cama queen-size e varanda."])]


class QuartoCriacao(SchemaEntrada):
    numero: NumeroQuarto
    tipo: TipoQuarto
    capacidade: Capacidade
    preco_diaria: PrecoDiaria
    andar: Andar
    descricao: Descricao | None = None
    ativo: bool = True

    @field_validator("numero")
    @classmethod
    def _normalizar_numero(cls, valor: str) -> str:
        return valor.upper()


class QuartoAtualizacao(SchemaAtualizacao):
    campos_nao_nulos = ("numero", "tipo", "capacidade", "preco_diaria", "andar", "ativo")

    numero: NumeroQuarto | None = None
    tipo: TipoQuarto | None = None
    capacidade: Capacidade | None = None
    preco_diaria: PrecoDiaria | None = None
    andar: Andar | None = None
    descricao: Descricao | None = None
    ativo: bool | None = None

    @field_validator("numero")
    @classmethod
    def _normalizar_numero(cls, valor: str | None) -> str | None:
        return valor.upper() if valor else valor


class QuartoResposta(SchemaSaida):
    id: int
    numero: str
    tipo: TipoQuarto
    capacidade: int
    preco_diaria: Dinheiro
    andar: int
    descricao: str | None
    ativo: bool
    criado_em: DataHoraUTC
    atualizado_em: DataHoraUTC


class QuartoResumo(SchemaSaida):
    """Representação reduzida do quarto, embutida nas reservas."""

    id: int
    numero: str
    tipo: TipoQuarto
    preco_diaria: Dinheiro
