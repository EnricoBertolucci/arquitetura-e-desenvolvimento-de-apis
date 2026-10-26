from datetime import date
from typing import Annotated

from pydantic import Field, ValidationInfo, field_validator

from app.models.enums import StatusReserva
from app.schemas.comum import DataHoraUTC, Dinheiro, SchemaAtualizacao, SchemaEntrada, SchemaSaida
from app.schemas.hospede import HospedeResumo
from app.schemas.quarto import QuartoResumo

IdPositivo = Annotated[int, Field(ge=1, examples=[1])]
QtdHospedes = Annotated[int, Field(ge=1, le=10, description="Não pode exceder a capacidade do quarto.", examples=[2])]
Observacoes = Annotated[str, Field(max_length=500, examples=["Chegada prevista após as 22h."])]


class ReservaCriacao(SchemaEntrada):
    """Dados para criar uma reserva. O valor total é calculado pelo servidor."""

    hospede_id: IdPositivo
    quarto_id: IdPositivo
    data_checkin: date = Field(examples=["2026-12-20"])
    data_checkout: date = Field(examples=["2026-12-23"])
    qtd_hospedes: QtdHospedes
    observacoes: Observacoes | None = None

    @field_validator("data_checkin")
    @classmethod
    def _checkin_futuro(cls, valor: date) -> date:
        if valor < date.today():
            raise ValueError("A data de check-in não pode estar no passado.")
        return valor

    @field_validator("data_checkout")
    @classmethod
    def _checkout_apos_checkin(cls, valor: date, info: ValidationInfo) -> date:
        checkin = info.data.get("data_checkin")
        if checkin is not None and valor <= checkin:
            raise ValueError("A data de check-out deve ser posterior à data de check-in.")
        return valor


class ReservaAtualizacao(SchemaAtualizacao):
    """Alteração parcial da reserva (o hóspede da reserva não pode ser trocado).

    A consistência entre as datas é verificada no serviço, combinando os
    valores enviados com os já gravados.
    """

    campos_nao_nulos = ("quarto_id", "data_checkin", "data_checkout", "qtd_hospedes", "status")

    quarto_id: IdPositivo | None = None
    data_checkin: date | None = None
    data_checkout: date | None = None
    qtd_hospedes: QtdHospedes | None = None
    status: StatusReserva | None = None
    observacoes: Observacoes | None = None


class ReservaResposta(SchemaSaida):
    id: int
    hospede_id: int
    quarto_id: int
    data_checkin: date
    data_checkout: date
    qtd_hospedes: int
    status: StatusReserva
    valor_total: Dinheiro
    observacoes: str | None
    criado_em: DataHoraUTC
    atualizado_em: DataHoraUTC


class ReservaDetalhe(ReservaResposta):
    """Reserva com os dados resumidos do hóspede e do quarto embutidos."""

    hospede: HospedeResumo
    quarto: QuartoResumo
