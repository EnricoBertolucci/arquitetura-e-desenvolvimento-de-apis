# Hotel API

API REST para gestão de **quartos**, **hóspedes** e **reservas** de um hotel, desenvolvida como trabalho final da disciplina *Arquitetura e Desenvolvimento de APIs* (Uninter).

> 🚧 Em desenvolvimento — seções marcadas com _(em breve)_ serão completadas ao longo do projeto.

## Tecnologias

| Item | Tecnologia |
|---|---|
| Linguagem | Python 3.13 |
| Framework | FastAPI |
| Banco de dados | SQLite |
| ORM / migrations | SQLAlchemy 2 / Alembic |
| Validação | Pydantic v2 |
| Autenticação | JWT (PyJWT) + senhas com hash bcrypt |
| Testes | pytest + TestClient |

## Pré-requisitos

- Python **3.12 ou superior**
- Git

## Instalação

```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Configuração

Copie o arquivo de exemplo e ajuste os valores:

```bash
# Windows
copy .env.example .env
# Linux/macOS
cp .env.example .env
```

Gere uma chave forte para o JWT e cole em `JWT_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do banco (padrão: `sqlite:///./hotel.db`) |
| `JWT_SECRET_KEY` | Chave de assinatura dos tokens (mín. 32 caracteres) |
| `JWT_ALGORITHM` | Algoritmo de assinatura (padrão: `HS256`) |
| `JWT_EXPIRE_MINUTES` | Validade do token em minutos |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Usuário administrador criado pelo seed |

Banco de dados e usuário inicial: _(em breve)_

## Execução

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Documentação Swagger: http://localhost:8000/docs
- Documentação ReDoc: http://localhost:8000/redoc

## Endpoints

_(em breve)_

## Autenticação

_(em breve)_

## Testes

_(em breve)_
