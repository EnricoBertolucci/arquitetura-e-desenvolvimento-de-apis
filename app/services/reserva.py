from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import Conflito, DadosInvalidos, RecursoNaoEncontrado
from app.models import Quarto, Reserva, StatusReserva
from app.repositories.hospede import HospedeRepositorio
from app.repositories.quarto import QuartoRepositorio
from app.repositories.reserva import ReservaRepositorio
from app.schemas.reserva import ReservaAtualizacao, ReservaCriacao


def calcular_valor_total(preco_diaria: Decimal, checkin: date, checkout: date) -> Decimal:
    """Número de diárias (noites) multiplicado pelo preço da diária."""
    return preco_diaria * (checkout - checkin).days


class ReservaServico:
    def __init__(self, db: Session) -> None:
        self.repo = ReservaRepositorio(db)
        self.quartos = QuartoRepositorio(db)
        self.hospedes = HospedeRepositorio(db)

    # --- consultas -------------------------------------------------------

    def listar(
        self,
        *,
        status: StatusReserva | None = None,
        hospede_id: int | None = None,
        quarto_id: int | None = None,
        data_de: date | None = None,
        data_ate: date | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Reserva]:
        if data_de and data_ate and data_ate < data_de:
            raise DadosInvalidos("data_ate", "Deve ser igual ou posterior a data_de.")
        return self.repo.buscar(
            status=status,
            hospede_id=hospede_id,
            quarto_id=quarto_id,
            checkin_de=data_de,
            checkin_ate=data_ate,
            skip=skip,
            limit=limit,
        )

    def listar_do_hospede(
        self, hospede_id: int, status: StatusReserva | None = None, skip: int = 0, limit: int = 20
    ) -> list[Reserva]:
        if self.hospedes.obter(hospede_id) is None:
            raise RecursoNaoEncontrado(f"Hóspede {hospede_id} não encontrado.")
        return self.listar(status=status, hospede_id=hospede_id, skip=skip, limit=limit)

    def obter(self, reserva_id: int) -> Reserva:
        reserva = self.repo.obter_detalhado(reserva_id)
        if reserva is None:
            raise RecursoNaoEncontrado(f"Reserva {reserva_id} não encontrada.")
        return reserva

    # --- validações de regra de negócio ----------------------------------

    def _obter_quarto_reservavel(self, quarto_id: int) -> Quarto:
        quarto = self.quartos.obter(quarto_id)
        if quarto is None:
            raise RecursoNaoEncontrado(f"Quarto {quarto_id} não encontrado.")
        if not quarto.ativo:
            raise Conflito(f"O quarto {quarto.numero} está inativo e não aceita reservas.")
        return quarto

    @staticmethod
    def _validar_capacidade(quarto: Quarto, qtd_hospedes: int) -> None:
        if qtd_hospedes > quarto.capacidade:
            raise DadosInvalidos(
                "qtd_hospedes",
                f"O quarto {quarto.numero} comporta no máximo {quarto.capacidade} hóspede(s).",
            )

    def _validar_disponibilidade(
        self, quarto: Quarto, checkin: date, checkout: date, excluir_id: int | None = None
    ) -> None:
        conflito = self.repo.buscar_conflito(quarto.id, checkin, checkout, excluir_id=excluir_id)
        if conflito is not None:
            raise Conflito(
                f"O quarto {quarto.numero} já possui reserva entre "
                f"{conflito.data_checkin.isoformat()} e {conflito.data_checkout.isoformat()}."
            )

    # --- escrita ---------------------------------------------------------

    def criar(self, dados: ReservaCriacao) -> Reserva:
        if self.hospedes.obter(dados.hospede_id) is None:
            raise RecursoNaoEncontrado(f"Hóspede {dados.hospede_id} não encontrado.")
        quarto = self._obter_quarto_reservavel(dados.quarto_id)
        self._validar_capacidade(quarto, dados.qtd_hospedes)
        self._validar_disponibilidade(quarto, dados.data_checkin, dados.data_checkout)

        reserva = Reserva(
            **dados.model_dump(),
            status=StatusReserva.CONFIRMADA,
            valor_total=calcular_valor_total(quarto.preco_diaria, dados.data_checkin, dados.data_checkout),
        )
        self.repo.adicionar(reserva)
        return self.obter(reserva.id)

    def atualizar(self, reserva_id: int, dados: ReservaAtualizacao) -> Reserva:
        reserva = self.obter(reserva_id)
        if reserva.status != StatusReserva.CONFIRMADA:
            raise Conflito(
                f"A reserva {reserva_id} está {reserva.status.value} e não pode mais ser alterada."
            )

        alteracoes = dados.model_dump(exclude_unset=True)

        # Valores finais = enviados no PATCH ou, na ausência, os já gravados.
        quarto_id = alteracoes.get("quarto_id", reserva.quarto_id)
        checkin = alteracoes.get("data_checkin", reserva.data_checkin)
        checkout = alteracoes.get("data_checkout", reserva.data_checkout)
        qtd_hospedes = alteracoes.get("qtd_hospedes", reserva.qtd_hospedes)
        status = alteracoes.get("status", reserva.status)

        mudou_quarto = quarto_id != reserva.quarto_id
        mudou_periodo = checkin != reserva.data_checkin or checkout != reserva.data_checkout

        quarto = self._obter_quarto_reservavel(quarto_id) if mudou_quarto else reserva.quarto

        if checkin != reserva.data_checkin and checkin < date.today():
            raise DadosInvalidos("data_checkin", "A data de check-in não pode estar no passado.")
        if checkout <= checkin:
            raise DadosInvalidos("data_checkout", "A data de check-out deve ser posterior à data de check-in.")
        self._validar_capacidade(quarto, qtd_hospedes)

        if (mudou_quarto or mudou_periodo) and status != StatusReserva.CANCELADA:
            self._validar_disponibilidade(quarto, checkin, checkout, excluir_id=reserva_id)

        if mudou_quarto or mudou_periodo:
            alteracoes["valor_total"] = calcular_valor_total(quarto.preco_diaria, checkin, checkout)

        self.repo.atualizar(reserva, alteracoes)
        return self.obter(reserva_id)

    def remover(self, reserva_id: int) -> None:
        self.repo.remover(self.obter(reserva_id))
