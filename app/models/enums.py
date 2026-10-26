"""Enumerações de domínio usadas pelos modelos e schemas."""

from enum import StrEnum


class TipoQuarto(StrEnum):
    SOLTEIRO = "SOLTEIRO"
    CASAL = "CASAL"
    DUPLO = "DUPLO"
    SUITE = "SUITE"


class StatusReserva(StrEnum):
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    CONCLUIDA = "CONCLUIDA"
