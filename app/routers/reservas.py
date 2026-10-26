from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import SessaoDB
from app.models import StatusReserva
from app.routers.respostas import respostas
from app.schemas.comum import PaginacaoLimit, PaginacaoSkip
from app.schemas.reserva import ReservaAtualizacao, ReservaCriacao, ReservaDetalhe, ReservaResposta
from app.services.reserva import ReservaServico

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.get(
    "",
    response_model=list[ReservaResposta],
    summary="Lista reservas com filtros",
    description="`data_de` e `data_ate` filtram pela data de check-in (intervalo inclusivo).",
    responses=respostas(400),
)
def listar_reservas(
    db: SessaoDB,
    status_reserva: Annotated[StatusReserva | None, Query(alias="status")] = None,
    hospede_id: Annotated[int | None, Query(ge=1)] = None,
    quarto_id: Annotated[int | None, Query(ge=1)] = None,
    data_de: Annotated[date | None, Query(description="Check-in a partir de (AAAA-MM-DD).")] = None,
    data_ate: Annotated[date | None, Query(description="Check-in até (AAAA-MM-DD).")] = None,
    skip: PaginacaoSkip = 0,
    limit: PaginacaoLimit = 20,
):
    return ReservaServico(db).listar(
        status=status_reserva,
        hospede_id=hospede_id,
        quarto_id=quarto_id,
        data_de=data_de,
        data_ate=data_ate,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{reserva_id}",
    response_model=ReservaDetalhe,
    summary="Consulta uma reserva",
    description="Retorna a reserva com os dados resumidos do hóspede e do quarto.",
    responses=respostas(404),
)
def obter_reserva(reserva_id: int, db: SessaoDB):
    return ReservaServico(db).obter(reserva_id)


@router.post(
    "",
    response_model=ReservaDetalhe,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma reserva",
    description=(
        "O `valor_total` é calculado pelo servidor (diárias × preço da diária). "
        "Retorna 409 se o quarto estiver inativo ou já reservado no período."
    ),
    responses=respostas(400, 404, 409),
)
def criar_reserva(dados: ReservaCriacao, response: Response, db: SessaoDB):
    reserva = ReservaServico(db).criar(dados)
    response.headers["Location"] = f"/reservas/{reserva.id}"
    return reserva


@router.patch(
    "/{reserva_id}",
    response_model=ReservaDetalhe,
    summary="Atualiza parcialmente uma reserva",
    description=(
        "Permite alterar quarto, datas, quantidade de hóspedes, status e observações. "
        'Ex.: `{"status": "CANCELADA"}`. Reservas canceladas ou concluídas não podem ser alteradas (409).'
    ),
    responses=respostas(400, 404, 409),
)
def atualizar_reserva(reserva_id: int, dados: ReservaAtualizacao, db: SessaoDB):
    return ReservaServico(db).atualizar(reserva_id, dados)


@router.delete(
    "/{reserva_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui uma reserva",
    description="Remoção definitiva. Para manter o histórico, prefira cancelar com PATCH.",
    responses=respostas(404),
)
def remover_reserva(reserva_id: int, db: SessaoDB) -> Response:
    ReservaServico(db).remover(reserva_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
