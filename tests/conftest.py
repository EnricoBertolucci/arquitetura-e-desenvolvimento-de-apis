"""Configuração compartilhada dos testes.

Os testes usam um banco SQLite temporário, recriado a cada teste, e variáveis
de ambiente próprias; o banco de desenvolvimento (hotel.db) nunca é tocado.
As variáveis precisam ser definidas antes de importar a aplicação.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

_PASTA_TEMPORARIA = Path(tempfile.mkdtemp(prefix="hotel-api-testes-"))

os.environ["DATABASE_URL"] = f"sqlite:///{(_PASTA_TEMPORARIA / 'teste.db').as_posix()}"
os.environ["JWT_SECRET_KEY"] = "chave-usada-somente-nos-testes-automatizados-0123456789"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "15"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401  (registra os modelos nos metadados)
from app.core.security import gerar_hash_senha  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Usuario  # noqa: E402

USUARIO_TESTE = "recepcao"
SENHA_TESTE = "senha-de-teste-123"
# O bcrypt é lento de propósito; o hash é calculado uma vez para toda a sessão.
_HASH_SENHA_TESTE = gerar_hash_senha(SENHA_TESTE)


def pytest_sessionfinish(session, exitstatus) -> None:
    engine.dispose()
    shutil.rmtree(_PASTA_TEMPORARIA, ignore_errors=True)


@pytest.fixture(autouse=True)
def banco_limpo() -> Iterator[None]:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(Usuario(username=USUARIO_TESTE, senha_hash=_HASH_SENHA_TESTE))
        db.add(Usuario(username="desativado", senha_hash=_HASH_SENHA_TESTE, ativo=False))
        db.commit()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def token(client: TestClient) -> str:
    resposta = client.post("/auth/login", data={"username": USUARIO_TESTE, "password": SENHA_TESTE})
    assert resposta.status_code == 200
    return resposta.json()["access_token"]


@pytest.fixture
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def dias(n: int) -> str:
    """Data relativa a hoje, no formato ISO usado pela API."""
    return (date.today() + timedelta(days=n)).isoformat()


# CPFs válidos (dígitos verificadores corretos) e fictícios.
CPFS_VALIDOS = ["52998224725", "11144477735", "39053344705", "15350946056"]


@pytest.fixture
def criar_quarto(client: TestClient, auth: dict[str, str]):
    contador = iter(range(100, 1000))

    def _criar(**campos) -> dict:
        dados = {"numero": str(next(contador)), "tipo": "CASAL", "capacidade": 2, "preco_diaria": 200, "andar": 1}
        dados.update(campos)
        resposta = client.post("/quartos", json=dados, headers=auth)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar


@pytest.fixture
def criar_hospede(client: TestClient, auth: dict[str, str]):
    cpfs = iter(CPFS_VALIDOS)

    def _criar(**campos) -> dict:
        cpf = next(cpfs)
        dados = {"nome": "Hóspede Teste", "cpf": cpf, "email": f"hospede{cpf}@example.com"}
        dados.update(campos)
        resposta = client.post("/hospedes", json=dados, headers=auth)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar


@pytest.fixture
def criar_reserva(client: TestClient, auth: dict[str, str]):
    def _criar(hospede_id: int, quarto_id: int, checkin: int, checkout: int, qtd: int = 1) -> dict:
        dados = {
            "hospede_id": hospede_id,
            "quarto_id": quarto_id,
            "data_checkin": dias(checkin),
            "data_checkout": dias(checkout),
            "qtd_hospedes": qtd,
        }
        resposta = client.post("/reservas", json=dados, headers=auth)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar
