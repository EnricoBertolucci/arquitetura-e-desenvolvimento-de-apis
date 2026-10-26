from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, Integer, Numeric, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoQuarto
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reserva import Reserva


class Quarto(TimestampMixin, Base):
    __tablename__ = "quartos"
    __table_args__ = (
        CheckConstraint("capacidade BETWEEN 1 AND 10", name="capacidade_valida"),
        CheckConstraint("preco_diaria > 0", name="preco_diaria_positivo"),
        CheckConstraint("andar >= 0", name="andar_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    tipo: Mapped[TipoQuarto] = mapped_column(
        Enum(
            TipoQuarto,
            name="tipo",
            native_enum=False,
            length=20,
            create_constraint=True,
            validate_strings=True,
        ), nullable=False
    )
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    andar: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(500))
    # Quarto inativo (ex.: em manutenção) não aceita novas reservas.
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)

    reservas: Mapped[list[Reserva]] = relationship(back_populates="quarto")
