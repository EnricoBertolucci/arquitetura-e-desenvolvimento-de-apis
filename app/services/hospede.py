from sqlalchemy.orm import Session

from app.exceptions import Conflito, RecursoNaoEncontrado
from app.models import Hospede
from app.repositories.hospede import HospedeRepositorio
from app.schemas.comum import somente_digitos
from app.schemas.hospede import HospedeAtualizacao, HospedeCriacao


class HospedeServico:
    def __init__(self, db: Session) -> None:
        self.repo = HospedeRepositorio(db)

    def listar(
        self,
        *,
        nome: str | None = None,
        cpf: str | None = None,
        email: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Hospede]:
        # Os filtros aceitam CPF com máscara e e-mail em qualquer caixa,
        # como na gravação.
        return self.repo.buscar(
            nome=nome.strip() if nome else None,
            cpf=somente_digitos(cpf) if cpf else None,
            email=email.strip().lower() if email else None,
            skip=skip,
            limit=limit,
        )

    def obter(self, hospede_id: int) -> Hospede:
        hospede = self.repo.obter(hospede_id)
        if hospede is None:
            raise RecursoNaoEncontrado(f"Hóspede {hospede_id} não encontrado.")
        return hospede

    def _verificar_unicidade(self, cpf: str | None, email: str | None, excluir_id: int | None = None) -> None:
        if cpf and self.repo.cpf_em_uso(cpf, excluir_id=excluir_id):
            raise Conflito("Já existe um hóspede cadastrado com este CPF.")
        if email and self.repo.email_em_uso(email, excluir_id=excluir_id):
            raise Conflito("Já existe um hóspede cadastrado com este e-mail.")

    def criar(self, dados: HospedeCriacao) -> Hospede:
        self._verificar_unicidade(dados.cpf, dados.email)
        return self.repo.adicionar(Hospede(**dados.model_dump()))

    def atualizar(self, hospede_id: int, dados: HospedeAtualizacao) -> Hospede:
        hospede = self.obter(hospede_id)
        alteracoes = dados.model_dump(exclude_unset=True)
        self._verificar_unicidade(alteracoes.get("cpf"), alteracoes.get("email"), excluir_id=hospede_id)
        return self.repo.atualizar(hospede, alteracoes)

    def remover(self, hospede_id: int) -> None:
        hospede = self.obter(hospede_id)
        if self.repo.possui_reservas(hospede_id):
            raise Conflito(
                f"O hóspede {hospede_id} possui reservas e não pode ser excluído "
                "(o histórico de hospedagens é preservado)."
            )
        self.repo.remover(hospede)
