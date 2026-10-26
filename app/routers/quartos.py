from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import SessaoDB
from app.models import TipoQuarto
from app.routers.respostas import respostas
from app.schemas.comum import PaginacaoLimit, PaginacaoSkip
from app.schemas.quarto import QuartoAtualizacao, QuartoCriacao, QuartoResposta
from app.services.quarto import QuartoServico

router = APIRouter(prefix="/quartos", tags=["Quartos"])


@router.get(
    "",
    response_model=list[QuartoResposta],
    summary="Lista quartos com filtros",
    description=(
        "Catálogo público de quartos. Com `disponivel_de` e `disponivel_ate`, retorna apenas os "
        "quartos ativos sem reserva no período (check-out no dia do check-in é permitido)."
    ),
    responses=respostas(400),
)
def listar_quartos(
    db: SessaoDB,
    tipo: TipoQuarto | None = None,
    capacidade_min: Annotated[int | None, Query(ge=1, le=10)] = None,
    preco_max: Annotated[Decimal | None, Query(gt=0, description="Diária máxima.")] = None,
    ativo: bool | None = None,
    disponivel_de: Annotated[date | None, Query(description="Início do período (AAAA-MM-DD).")] = None,
    disponivel_ate: Annotated[date | None, Query(description="Fim do período (AAAA-MM-DD).")] = None,
    skip: PaginacaoSkip = 0,
    limit: PaginacaoLimit = 20,
):
    return QuartoServico(db).listar(
        tipo=tipo,
        capacidade_min=capacidade_min,
        preco_max=preco_max,
        ativo=ativo,
        disponivel_de=disponivel_de,
        disponivel_ate=disponivel_ate,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{quarto_id}",
    response_model=QuartoResposta,
    summary="Consulta um quarto",
    responses=respostas(404),
)
def obter_quarto(quarto_id: int, db: SessaoDB):
    return QuartoServico(db).obter(quarto_id)


@router.post(
    "",
    response_model=QuartoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um quarto",
    responses=respostas(400, 409),
)
def criar_quarto(dados: QuartoCriacao, response: Response, db: SessaoDB):
    quarto = QuartoServico(db).criar(dados)
    response.headers["Location"] = f"/quartos/{quarto.id}"
    return quarto


@router.patch(
    "/{quarto_id}",
    response_model=QuartoResposta,
    summary="Atualiza parcialmente um quarto",
    description='Envie apenas os campos a alterar. Ex.: `{"ativo": false}` para colocar o quarto em manutenção.',
    responses=respostas(400, 404, 409),
)
def atualizar_quarto(quarto_id: int, dados: QuartoAtualizacao, db: SessaoDB):
    return QuartoServico(db).atualizar(quarto_id, dados)


@router.delete(
    "/{quarto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um quarto",
    description="Quartos com reservas não podem ser excluídos (409); use a desativação.",
    responses=respostas(404, 409),
)
def remover_quarto(quarto_id: int, db: SessaoDB) -> Response:
    QuartoServico(db).remover(quarto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
