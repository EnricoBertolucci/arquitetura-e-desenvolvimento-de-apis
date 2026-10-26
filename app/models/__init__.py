"""Importa todos os modelos para registrá-los nos metadados da `Base`.

O Alembic lê `Base.metadata` para gerar as migrations; um modelo não
importado aqui não seria enxergado por ele.
"""

from app.models.enums import StatusReserva, TipoQuarto
from app.models.hospede import Hospede
from app.models.quarto import Quarto
from app.models.reserva import Reserva
from app.models.usuario import Usuario

__all__ = ["Hospede", "Quarto", "Reserva", "StatusReserva", "TipoQuarto", "Usuario"]
