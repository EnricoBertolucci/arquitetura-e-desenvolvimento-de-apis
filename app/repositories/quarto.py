from datetime import date
from decimal import Decimal

from sqlalchemy import exists, select

from app.models import Quarto, Reserva, StatusReserva, TipoQuarto
from app.repositories.base import RepositorioBase


class QuartoRepositorio(RepositorioBase[Quarto]):
    modelo = Quarto

    def buscar(
        self,
        *,
        tipo: TipoQuarto | None,
        capacidade_min: int | None,
        preco_max: Decimal | None,
        ativo: bool | None,
        livre_de: date | None,
        livre_ate: date | None,
        skip: int,
        limit: int,
    ) -> list[Quarto]:
        consulta = select(Quarto)
        if tipo is not None:
            consulta = consulta.where(Quarto.tipo == tipo)
        if capacidade_min is not None:
            consulta = consulta.where(Quarto.capacidade >= capacidade_min)
        if preco_max is not None:
            consulta = consulta.where(Quarto.preco_diaria <= preco_max)
        if ativo is not None:
            consulta = consulta.where(Quarto.ativo == ativo)
        if livre_de is not None and livre_ate is not None:
            # Disponível = ativo e sem reserva válida que cruze o período pedido.
            ocupado = exists().where(
                Reserva.quarto_id == Quarto.id,
                Reserva.status != StatusReserva.CANCELADA,
                Reserva.data_checkin < livre_ate,
                Reserva.data_checkout > livre_de,
            )
            consulta = consulta.where(Quarto.ativo.is_(True), ~ocupado)
        return self.listar(consulta, skip, limit)

    def numero_em_uso(self, numero: str, excluir_id: int | None = None) -> bool:
        return self.existe(Quarto.numero == numero, excluir_id=excluir_id)

    def possui_reservas(self, quarto_id: int) -> bool:
        return self.db.scalar(select(Reserva.id).where(Reserva.quarto_id == quarto_id).limit(1)) is not None
