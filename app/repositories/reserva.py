from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Reserva, StatusReserva
from app.repositories.base import RepositorioBase


class ReservaRepositorio(RepositorioBase[Reserva]):
    modelo = Reserva

    def obter_detalhado(self, id_: int) -> Reserva | None:
        """Carrega a reserva já com hóspede e quarto (uma única consulta com JOIN)."""
        consulta = (
            select(Reserva)
            .options(joinedload(Reserva.hospede), joinedload(Reserva.quarto))
            .where(Reserva.id == id_)
        )
        return self.db.scalar(consulta)

    def buscar(
        self,
        *,
        status: StatusReserva | None,
        hospede_id: int | None,
        quarto_id: int | None,
        checkin_de: date | None,
        checkin_ate: date | None,
        skip: int,
        limit: int,
    ) -> list[Reserva]:
        consulta = select(Reserva)
        if status is not None:
            consulta = consulta.where(Reserva.status == status)
        if hospede_id is not None:
            consulta = consulta.where(Reserva.hospede_id == hospede_id)
        if quarto_id is not None:
            consulta = consulta.where(Reserva.quarto_id == quarto_id)
        if checkin_de is not None:
            consulta = consulta.where(Reserva.data_checkin >= checkin_de)
        if checkin_ate is not None:
            consulta = consulta.where(Reserva.data_checkin <= checkin_ate)
        return self.listar(consulta, skip, limit)

    def buscar_conflito(
        self, quarto_id: int, checkin: date, checkout: date, excluir_id: int | None = None
    ) -> Reserva | None:
        """Retorna uma reserva não cancelada do quarto que cruze o período, se houver.

        Dois períodos se sobrepõem quando um começa antes do outro terminar.
        Check-out e check-in no mesmo dia não conflitam.
        """
        consulta = select(Reserva).where(
            Reserva.quarto_id == quarto_id,
            Reserva.status != StatusReserva.CANCELADA,
            Reserva.data_checkin < checkout,
            Reserva.data_checkout > checkin,
        )
        if excluir_id is not None:
            consulta = consulta.where(Reserva.id != excluir_id)
        return self.db.scalar(consulta.limit(1))
