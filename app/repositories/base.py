from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base

Modelo = TypeVar("Modelo", bound=Base)


class RepositorioBase(Generic[Modelo]):
    """Operações comuns a todos os recursos (buscar, inserir, atualizar, remover)."""

    modelo: type[Modelo]

    def __init__(self, db: Session) -> None:
        self.db = db

    def obter(self, id_: int) -> Modelo | None:
        return self.db.get(self.modelo, id_)

    def existe(self, *condicoes: Any, excluir_id: int | None = None) -> bool:
        consulta = select(self.modelo.id).where(*condicoes)
        if excluir_id is not None:
            consulta = consulta.where(self.modelo.id != excluir_id)
        return self.db.scalar(consulta.limit(1)) is not None

    def listar(self, consulta: Select, skip: int, limit: int) -> list[Modelo]:
        return list(self.db.scalars(consulta.order_by(self.modelo.id).offset(skip).limit(limit)))

    def adicionar(self, objeto: Modelo) -> Modelo:
        self.db.add(objeto)
        self.db.commit()
        self.db.refresh(objeto)
        return objeto

    def atualizar(self, objeto: Modelo, dados: dict[str, Any]) -> Modelo:
        for campo, valor in dados.items():
            setattr(objeto, campo, valor)
        self.db.commit()
        self.db.refresh(objeto)
        return objeto

    def remover(self, objeto: Modelo) -> None:
        self.db.delete(objeto)
        self.db.commit()
