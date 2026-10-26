from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import Conflito, DadosInvalidos, RecursoNaoEncontrado
from app.models import Quarto, TipoQuarto
from app.repositories.quarto import QuartoRepositorio
from app.schemas.quarto import QuartoAtualizacao, QuartoCriacao


class QuartoServico:
    def __init__(self, db: Session) -> None:
        self.repo = QuartoRepositorio(db)

    def listar(
        self,
        *,
        tipo: TipoQuarto | None = None,
        capacidade_min: int | None = None,
        preco_max: Decimal | None = None,
        ativo: bool | None = None,
        disponivel_de: date | None = None,
        disponivel_ate: date | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Quarto]:
        if (disponivel_de is None) != (disponivel_ate is None):
            campo = "disponivel_ate" if disponivel_ate is None else "disponivel_de"
            raise DadosInvalidos(campo, "Informe disponivel_de e disponivel_ate juntos.")
        if disponivel_de and disponivel_ate and disponivel_ate <= disponivel_de:
            raise DadosInvalidos("disponivel_ate", "Deve ser posterior a disponivel_de.")

        return self.repo.buscar(
            tipo=tipo,
            capacidade_min=capacidade_min,
            preco_max=preco_max,
            ativo=ativo,
            livre_de=disponivel_de,
            livre_ate=disponivel_ate,
            skip=skip,
            limit=limit,
        )

    def obter(self, quarto_id: int) -> Quarto:
        quarto = self.repo.obter(quarto_id)
        if quarto is None:
            raise RecursoNaoEncontrado(f"Quarto {quarto_id} não encontrado.")
        return quarto

    def criar(self, dados: QuartoCriacao) -> Quarto:
        if self.repo.numero_em_uso(dados.numero):
            raise Conflito(f"Já existe um quarto com o número {dados.numero}.")
        return self.repo.adicionar(Quarto(**dados.model_dump()))

    def atualizar(self, quarto_id: int, dados: QuartoAtualizacao) -> Quarto:
        quarto = self.obter(quarto_id)
        alteracoes = dados.model_dump(exclude_unset=True)

        numero = alteracoes.get("numero")
        if numero and self.repo.numero_em_uso(numero, excluir_id=quarto_id):
            raise Conflito(f"Já existe um quarto com o número {numero}.")

        # A diária de reservas já feitas não muda: o valor_total foi fixado na reserva.
        return self.repo.atualizar(quarto, alteracoes)

    def remover(self, quarto_id: int) -> None:
        quarto = self.obter(quarto_id)
        if self.repo.possui_reservas(quarto_id):
            raise Conflito(
                f"O quarto {quarto.numero} possui reservas e não pode ser excluído. "
                "Para retirá-lo de uso, desative-o com PATCH {\"ativo\": false}."
            )
        self.repo.remover(quarto)
