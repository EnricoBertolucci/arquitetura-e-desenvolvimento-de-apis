from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import SessaoDB
from app.models import StatusReserva
from app.routers.respostas import respostas
from app.schemas.comum import PaginacaoLimit, PaginacaoSkip
from app.schemas.hospede import HospedeAtualizacao, HospedeCriacao, HospedeResposta
from app.schemas.reserva import ReservaResposta
from app.services.hospede import HospedeServico
from app.services.reserva import ReservaServico

router = APIRouter(prefix="/hospedes", tags=["Hóspedes"])


@router.get(
    "",
    response_model=list[HospedeResposta],
    summary="Lista hóspedes com filtros",
    responses=respostas(400),
)
def listar_hospedes(
    db: SessaoDB,
    nome: Annotated[
        str | None, Query(max_length=120, description="Parte do nome (sem diferenciar maiúsculas).")
    ] = None,
    cpf: Annotated[str | None, Query(max_length=14, description="CPF com ou sem máscara.")] = None,
    email: Annotated[str | None, Query(max_length=254)] = None,
    skip: PaginacaoSkip = 0,
    limit: PaginacaoLimit = 20,
):
    return HospedeServico(db).listar(nome=nome, cpf=cpf, email=email, skip=skip, limit=limit)


@router.get(
    "/{hospede_id}",
    response_model=HospedeResposta,
    summary="Consulta um hóspede",
    responses=respostas(404),
)
def obter_hospede(hospede_id: int, db: SessaoDB):
    return HospedeServico(db).obter(hospede_id)


@router.get(
    "/{hospede_id}/reservas",
    response_model=list[ReservaResposta],
    summary="Lista as reservas de um hóspede",
    responses=respostas(400, 404),
)
def listar_reservas_do_hospede(
    hospede_id: int,
    db: SessaoDB,
    status_reserva: Annotated[StatusReserva | None, Query(alias="status")] = None,
    skip: PaginacaoSkip = 0,
    limit: PaginacaoLimit = 20,
):
    return ReservaServico(db).listar_do_hospede(hospede_id, status=status_reserva, skip=skip, limit=limit)


@router.post(
    "",
    response_model=HospedeResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um hóspede",
    description="O CPF é validado pelos dígitos verificadores e armazenado sem máscara.",
    responses=respostas(400, 409),
)
def criar_hospede(dados: HospedeCriacao, response: Response, db: SessaoDB):
    hospede = HospedeServico(db).criar(dados)
    response.headers["Location"] = f"/hospedes/{hospede.id}"
    return hospede


@router.patch(
    "/{hospede_id}",
    response_model=HospedeResposta,
    summary="Atualiza parcialmente um hóspede",
    responses=respostas(400, 404, 409),
)
def atualizar_hospede(hospede_id: int, dados: HospedeAtualizacao, db: SessaoDB):
    return HospedeServico(db).atualizar(hospede_id, dados)


@router.delete(
    "/{hospede_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um hóspede",
    description="Hóspedes com reservas não podem ser excluídos (409).",
    responses=respostas(404, 409),
)
def remover_hospede(hospede_id: int, db: SessaoDB) -> Response:
    HospedeServico(db).remover(hospede_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
