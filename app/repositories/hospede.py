from sqlalchemy import select

from app.models import Hospede, Reserva
from app.repositories.base import RepositorioBase


class HospedeRepositorio(RepositorioBase[Hospede]):
    modelo = Hospede

    def buscar(
        self, *, nome: str | None, cpf: str | None, email: str | None, skip: int, limit: int
    ) -> list[Hospede]:
        consulta = select(Hospede)
        if nome:
            # Busca parcial sem diferenciar maiúsculas de minúsculas.
            consulta = consulta.where(Hospede.nome.icontains(nome, autoescape=True))
        if cpf:
            consulta = consulta.where(Hospede.cpf == cpf)
        if email:
            consulta = consulta.where(Hospede.email == email)
        return self.listar(consulta, skip, limit)

    def cpf_em_uso(self, cpf: str, excluir_id: int | None = None) -> bool:
        return self.existe(Hospede.cpf == cpf, excluir_id=excluir_id)

    def email_em_uso(self, email: str, excluir_id: int | None = None) -> bool:
        return self.existe(Hospede.email == email, excluir_id=excluir_id)

    def possui_reservas(self, hospede_id: int) -> bool:
        return self.db.scalar(select(Reserva.id).where(Reserva.hospede_id == hospede_id).limit(1)) is not None
