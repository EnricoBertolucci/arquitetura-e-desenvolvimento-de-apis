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

## Banco de dados

O banco SQLite (`hotel.db`) é criado pelas **migrations do Alembic**, que reproduzem toda a estrutura (tabelas, chaves estrangeiras, constraints e índices):

```bash
alembic upgrade head
```

Em seguida, crie o usuário administrador (credenciais de `ADMIN_USERNAME`/`ADMIN_PASSWORD` do `.env`) e os dados de exemplo:

```bash
python -m scripts.seed                 # administrador + 6 quartos, 4 hóspedes e 3 reservas
python -m scripts.seed --sem-exemplos  # somente o administrador
```

O seed pode ser executado mais de uma vez sem duplicar registros. Para recriar o banco do zero, apague o arquivo `hotel.db` e repita os dois comandos.

| Tabela | Descrição | Relacionamentos |
|---|---|---|
| `quartos` | Número, tipo, capacidade, diária, andar, ativo | 1:N com `reservas` |
| `hospedes` | Nome, CPF, e-mail, telefone, data de nascimento | 1:N com `reservas` |
| `reservas` | Período, qtd. de hóspedes, status, valor total | N:1 com `hospedes` e `quartos` |
| `usuarios` | Usuários da API (senha armazenada com hash bcrypt) | — |

Detalhes da modelagem em [`docs/MODELAGEM.md`](docs/MODELAGEM.md).

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
