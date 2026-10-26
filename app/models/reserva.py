from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatusReserva
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.hospede import Hospede
    from app.models.quarto import Quarto


class Reserva(TimestampMixin, Base):
    """Vínculo entre um hóspede e um quarto em um período (N:1 com cada um)."""

    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint("data_checkout > data_checkin", name="periodo_valido"),
        CheckConstraint("qtd_hospedes >= 1", name="qtd_hospedes_positiva"),
        CheckConstraint("valor_total >= 0", name="valor_total_nao_negativo"),
        # Acelera a verificação de sobreposição de datas por quarto.
        Index("ix_reservas_quarto_periodo", "quarto_id", "data_checkin", "data_checkout"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # RESTRICT: o banco impede excluir hóspede/quarto que possua reservas,
    # preservando o histórico (a API também valida isso e responde 409).
    hospede_id: Mapped[int] = mapped_column(
        ForeignKey("hospedes.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    quarto_id: Mapped[int] = mapped_column(
        ForeignKey("quartos.id", ondelete="RESTRICT"), nullable=False
    )
    data_checkin: Mapped[date] = mapped_column(Date, nullable=False)
    data_checkout: Mapped[date] = mapped_column(Date, nullable=False)
    qtd_hospedes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StatusReserva] = mapped_column(
        Enum(
            StatusReserva,
            name="status",
            native_enum=False,
            length=20,
            create_constraint=True,
            validate_strings=True,
        ),
        default=StatusReserva.CONFIRMADA,
        server_default=StatusReserva.CONFIRMADA.value,
        index=True,
        nullable=False,
    )
    # Calculado pela aplicação: número de diárias x preço da diária do quarto.
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(String(500))

    hospede: Mapped[Hospede] = relationship(back_populates="reservas")
    quarto: Mapped[Quarto] = relationship(back_populates="reservas")
