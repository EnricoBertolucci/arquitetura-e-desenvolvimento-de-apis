# Hotel API

API REST para gestão de **quartos**, **hóspedes** e **reservas** de um hotel de pequeno porte, desenvolvida como trabalho final da disciplina *Arquitetura e Desenvolvimento de APIs* (Uninter).

**Problema resolvido:** centralizar o cadastro de quartos, hóspedes e reservas e **impedir reservas sobrepostas** para o mesmo quarto. A API calcula o valor da hospedagem, bloqueia reservas em quartos inativos ou acima da capacidade e preserva o histórico (hóspedes e quartos com reservas não podem ser excluídos).

- O **catálogo de quartos** é público (consulta), pensando em um site que exibe os quartos disponíveis.
- **Hóspedes e reservas** contêm dados pessoais (CPF, e-mail, histórico de hospedagem) e por isso só são acessíveis com autenticação **JWT**.

## Tecnologias

| Item | Tecnologia |
|---|---|
| Linguagem | Python 3.13 |
| Framework | FastAPI (documentação OpenAPI/Swagger automática) |
| Banco de dados | SQLite (arquivo local) |
| ORM / migrations | SQLAlchemy 2 / Alembic |
| Validação | Pydantic v2 |
| Autenticação | JWT (PyJWT) + senhas com hash bcrypt |
| Testes | pytest + TestClient do FastAPI |

## Pré-requisitos

- Python **3.12 ou superior**
- Git

## Instalação

```bash
git clone https://github.com/EnricoBertolucci/arquitetura-e-desenvolvimento-de-apis.git
cd arquitetura-e-desenvolvimento-de-apis

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

> Todos os comandos a seguir devem ser executados na raiz do projeto, com o ambiente virtual ativado.

## Configuração

Copie o arquivo de exemplo:

```bash
# Windows
copy .env.example .env
# Linux/macOS
cp .env.example .env
```

Edite o `.env`:

1. Gere uma chave forte para o JWT e cole em `JWT_SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. Defina uma senha própria em `ADMIN_PASSWORD` (será a senha do usuário administrador).

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do banco (padrão: `sqlite:///./hotel.db`) |
| `JWT_SECRET_KEY` | Chave de assinatura dos tokens (mín. 32 caracteres) — **obrigatória** |
| `JWT_ALGORITHM` | Algoritmo de assinatura (padrão: `HS256`) |
| `JWT_EXPIRE_MINUTES` | Validade do token em minutos (padrão: 60) |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Usuário administrador criado pelo seed |

O arquivo `.env` está no `.gitignore`: nenhuma credencial real é versionada.

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

🔒 = exige o header `Authorization: Bearer <token>`.
As listagens aceitam paginação com `skip` (padrão 0) e `limit` (padrão 20, máximo 100).

### Autenticação

| Método | Endpoint | Descrição | Códigos |
|---|---|---|---|
| POST | `/auth/login` | Recebe `username` e `password` (formulário) e retorna o token JWT | 200, 400, 401, 403 |
| GET 🔒 | `/auth/me` | Dados do usuário autenticado | 200, 401, 403 |

### Quartos (leitura pública, escrita protegida)

| Método | Endpoint | Descrição | Códigos |
|---|---|---|---|
| GET | `/quartos` | Lista quartos. Filtros: `tipo`, `capacidade_min`, `preco_max`, `ativo`, `disponivel_de` + `disponivel_ate` (somente quartos livres no período) | 200, 400 |
| GET | `/quartos/{id}` | Consulta um quarto | 200, 404 |
| POST 🔒 | `/quartos` | Cria um quarto (retorna o header `Location`) | 201, 400, 401, 409 |
| PATCH 🔒 | `/quartos/{id}` | Atualiza parcialmente (ex.: `{"ativo": false}`) | 200, 400, 401, 404, 409 |
| DELETE 🔒 | `/quartos/{id}` | Exclui (409 se o quarto possuir reservas) | 204, 401, 404, 409 |

### Hóspedes (todas as rotas protegidas)

| Método | Endpoint | Descrição | Códigos |
|---|---|---|---|
| GET 🔒 | `/hospedes` | Lista hóspedes. Filtros: `nome` (parcial), `cpf`, `email` | 200, 400, 401 |
| GET 🔒 | `/hospedes/{id}` | Consulta um hóspede | 200, 401, 404 |
| GET 🔒 | `/hospedes/{id}/reservas` | Reservas do hóspede (filtro `status`) | 200, 401, 404 |
| POST 🔒 | `/hospedes` | Cadastra (CPF validado pelos dígitos verificadores) | 201, 400, 401, 409 |
| PATCH 🔒 | `/hospedes/{id}` | Atualiza parcialmente | 200, 400, 401, 404, 409 |
| DELETE 🔒 | `/hospedes/{id}` | Exclui (409 se o hóspede possuir reservas) | 204, 401, 404, 409 |

### Reservas (todas as rotas protegidas)

| Método | Endpoint | Descrição | Códigos |
|---|---|---|---|
| GET 🔒 | `/reservas` | Lista reservas. Filtros: `status`, `hospede_id`, `quarto_id`, `data_de` e `data_ate` (intervalo da data de check-in) | 200, 400, 401 |
| GET 🔒 | `/reservas/{id}` | Consulta a reserva com hóspede e quarto embutidos | 200, 401, 404 |
| POST 🔒 | `/reservas` | Cria a reserva; o `valor_total` é calculado pelo servidor | 201, 400, 401, 404, 409 |
| PATCH 🔒 | `/reservas/{id}` | Altera quarto, datas, qtd. de hóspedes, status ou observações | 200, 400, 401, 404, 409 |
| DELETE 🔒 | `/reservas/{id}` | Exclui a reserva | 204, 401, 404 |

**Por que PATCH e não PUT?** PATCH aplica uma modificação parcial: o cliente envia apenas os campos que deseja alterar (ex.: `{"status": "CANCELADA"}`). PUT substitui a representação inteira do recurso e exigiria reenviar todos os campos, o que é inadequado para operações frequentes como cancelar uma reserva e aumenta o risco de sobrescrever dados por engano.

### Regras de negócio das reservas

- Não pode haver duas reservas não canceladas do mesmo quarto com períodos sobrepostos → **409**. Check-out e check-in no mesmo dia são permitidos.
- Quarto inativo não aceita reservas → **409**.
- `qtd_hospedes` acima da capacidade do quarto → **400**.
- Check-in no passado ou check-out igual/anterior ao check-in → **400**.
- `valor_total` = número de diárias × preço da diária; é recalculado quando as datas ou o quarto mudam.
- Reservas `CANCELADA` ou `CONCLUIDA` não podem mais ser alteradas → **409**.

### Formato das respostas de erro

Todas as respostas de erro são JSON com o campo `detail`. Erros de validação também trazem a lista `erros` por campo:

```json
{
  "detail": "Dados inválidos.",
  "erros": [
    { "campo": "cpf", "mensagem": "CPF inválido." },
    { "campo": "email", "mensagem": "E-mail inválido." }
  ]
}
```

| Situação | Código |
|---|---|
| Dados inválidos (tipo, formato, faixa, JSON malformado, campo desconhecido) | 400 |
| Token ausente, inválido ou expirado | 401 (com header `WWW-Authenticate: Bearer`) |
| Usuário inativo | 403 |
| Recurso ou rota inexistente | 404 |
| Método HTTP não suportado pela rota | 405 |
| Duplicidade, sobreposição de reservas, exclusão com dependentes | 409 |
| Erro inesperado (sem expor detalhes internos) | 500 |

## Autenticação

A API usa **JWT (JSON Web Token)** no padrão *Bearer*:

1. O cliente envia `username` e `password` para `POST /auth/login` (formulário `application/x-www-form-urlencoded`, padrão OAuth2).
2. A API compara a senha com o **hash bcrypt** armazenado e, se estiver correta, devolve um token assinado com `JWT_SECRET_KEY`, válido por `JWT_EXPIRE_MINUTES`.
3. Nas rotas protegidas, o cliente envia `Authorization: Bearer <token>`. A API valida assinatura e expiração e carrega o usuário a cada requisição (não há sessão no servidor).

Não há cadastro público de usuários: o administrador é criado pelo seed a partir do `.env`, assim nenhuma credencial fica no repositório.

### Como testar sem expor credenciais

Use o usuário e a senha que **você** definiu em `ADMIN_USERNAME`/`ADMIN_PASSWORD` no seu `.env`.

**Pelo Swagger** (http://localhost:8000/docs): clique em **Authorize**, informe usuário e senha e confirme. As rotas com cadeado passam a enviar o token automaticamente.

**Pelo terminal (cURL)** — os exemplos usam variáveis de ambiente para não deixar a senha no histórico de comandos:

```bash
# Linux/macOS (bash)
read -s -p "Senha: " SENHA; echo
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin" --data-urlencode "password=$SENHA" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl http://localhost:8000/reservas -H "Authorization: Bearer $TOKEN"
```

```powershell
# Windows (PowerShell)
$cred = Get-Credential -UserName admin -Message "Senha da API"
$login = Invoke-RestMethod -Method Post http://localhost:8000/auth/login `
  -Body @{ username = $cred.UserName; password = $cred.GetNetworkCredential().Password }
$headers = @{ Authorization = "Bearer $($login.access_token)" }

Invoke-RestMethod http://localhost:8000/reservas -Headers $headers
```

Sem o header, as rotas protegidas respondem `401`:

```bash
curl -i http://localhost:8000/hospedes
# HTTP/1.1 401 Unauthorized
# {"detail":"Token de acesso ausente. Faça login em /auth/login."}
```

### Exemplos de requisição

```bash
# Listar suítes com capacidade para 3 pessoas ou mais (rota pública)
curl "http://localhost:8000/quartos?tipo=SUITE&capacidade_min=3"

# Quartos livres em um período
curl "http://localhost:8000/quartos?disponivel_de=2026-12-20&disponivel_ate=2026-12-23"

# Criar uma reserva
curl -X POST http://localhost:8000/reservas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"hospede_id": 4, "quarto_id": 3, "data_checkin": "2026-12-20", "data_checkout": "2026-12-23", "qtd_hospedes": 2}'

# Cancelar a reserva (atualização parcial)
curl -X PATCH http://localhost:8000/reservas/4 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "CANCELADA"}'
```

Também há uma coleção do Postman em [`docs/postman/hotel-api.postman_collection.json`](docs/postman/hotel-api.postman_collection.json). Importe-a no Postman, execute **Auth → Login** (informe a senha na variável `senha` da coleção) e o token será salvo automaticamente para as demais requisições.

## CORS

O navegador só permite que um front-end hospedado em **outra origem** (ex.: `http://localhost:5173`) chame a API se ela autorizar essa origem. A política foi configurada de forma restritiva em `app/main.py`:

| Configuração | Valor | Justificativa |
|---|---|---|
| `allow_origins` | Lista de `CORS_ORIGINS` (`.env`) | Somente os front-ends conhecidos; **sem `*`**. Trocar de ambiente não exige alterar código |
| `allow_methods` | `GET, POST, PATCH, DELETE, OPTIONS` | Exatamente os métodos usados pela API (`PUT` não é aceito) |
| `allow_headers` | `Authorization, Content-Type` | O token JWT e o corpo JSON |
| `expose_headers` | `Location` | Permite ao front-end ler o endereço do recurso criado (respostas 201) |
| `allow_credentials` | `false` | O token trafega no header `Authorization`, não em cookies |
| `max_age` | 600 s | O navegador reaproveita o preflight por 10 minutos |

Clientes fora do navegador (cURL, Postman, outro servidor) não são afetados pelo CORS — por isso a proteção dos dados é feita pela autenticação JWT, e o CORS apenas controla quais sites podem consumir a API pelo navegador.

## Testes

Os testes automatizados usam um banco SQLite temporário (o `hotel.db` não é alterado) e não dependem do `.env`:

```bash
pytest
```

São 86 testes cobrindo: CRUD dos três recursos, filtros e paginação, regras de reserva (sobreposição, capacidade, quarto inativo, cálculo e recálculo do valor), validações (CPF, e-mail, datas, campos desconhecidos), respostas de erro (400, 404, 405, 409, 500), autenticação (login, token ausente/inválido/expirado, usuário inativo) e CORS.

## Estrutura do projeto

```
├── app/
│   ├── main.py            # cria o app, registra CORS, handlers de erro e rotas
│   ├── core/              # configurações (.env) e segurança (bcrypt, JWT)
│   ├── db/                # Base declarativa, engine e sessão do SQLAlchemy
│   ├── models/            # classes ORM ↔ tabelas
│   ├── schemas/           # modelos Pydantic de entrada e saída (validação)
│   ├── repositories/      # consultas ao banco via ORM
│   ├── services/          # regras de negócio
│   ├── routers/           # endpoints HTTP (auth, quartos, hospedes, reservas)
│   ├── dependencies.py    # sessão do banco e usuário autenticado (Depends)
│   └── exceptions.py      # exceções de domínio e handlers globais de erro
├── alembic/               # migrations
├── scripts/seed.py        # administrador e dados de exemplo
├── tests/                 # testes automatizados (pytest)
├── docs/                  # modelagem, coleção Postman e evidências
├── .env.example
└── requirements.txt
```

Fluxo de uma requisição: **cliente → CORS → router → dependências (sessão do banco, usuário do JWT) → schema Pydantic (validação) → service (regras de negócio) → repository (ORM) → SQLite → schema de saída → resposta JSON**.
