from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reserva import Reserva


class Hospede(TimestampMixin, Base):
    __tablename__ = "hospedes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # CPF e telefone são guardados apenas com dígitos (sem máscara).
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(11))
    data_nascimento: Mapped[date | None] = mapped_column(Date)

    reservas: Mapped[list[Reserva]] = relationship(back_populates="hospede")
