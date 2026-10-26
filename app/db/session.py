"""Conexão com o banco de dados: engine e fábrica de sessões."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_eh_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # O SQLite, por padrão, só permite uso da conexão pela thread que a criou;
    # o FastAPI atende requisições em threads diferentes.
    connect_args={"check_same_thread": False} if _eh_sqlite else {},
)

if _eh_sqlite:

    @event.listens_for(Engine, "connect")
    def _habilitar_chaves_estrangeiras(conexao_dbapi, _registro) -> None:
        # O SQLite não valida chaves estrangeiras a menos que isso seja
        # ativado em cada conexão.
        cursor = conexao_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Abre uma sessão por requisição e garante o fechamento ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
