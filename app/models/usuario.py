from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CriadoEmMixin


class Usuario(CriadoEmMixin, Base):
    """Funcionário do hotel com acesso à API. Usado apenas na autenticação."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # Somente o hash bcrypt é armazenado; a senha em texto nunca chega ao banco.
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)
