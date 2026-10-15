# Modelagem da Hotel API

Documento de projeto: entidades, regras de negócio, endpoints, arquitetura e padrão de erros.

---

## 1. Visão geral (T1.1)

**Problema:** um hotel de pequeno porte precisa centralizar o cadastro de quartos, hóspedes e reservas, evitando reservas duplicadas para o mesmo quarto no mesmo período.

**Público/cenário:** recepção e administração do hotel (usuários autenticados) e um eventual site/app que exibe o catálogo de quartos (público).

| Recurso | Descrição | Operações |
|---|---|---|
| Quarto | Unidades disponíveis para hospedagem (número, tipo, capacidade, diária) | Listar/filtrar, consultar, criar, atualizar, excluir, **consultar disponibilidade por período** |
| Hóspede | Pessoas que se hospedam (dados pessoais) | Listar/filtrar, consultar, criar, atualizar, excluir, listar reservas do hóspede |
| Reserva | Vínculo hóspede ↔ quarto num período, com valor calculado | Listar/filtrar, consultar, criar, atualizar (datas/status), excluir |
| Usuário | Funcionário que acessa a API (apenas autenticação) | Login, consultar o próprio perfil |

### Diagrama de relacionamentos

```
usuarios (isolada — só autenticação)

hospedes 1 ────< N reservas N >──── 1 quartos
```

---

## 2. Modelo de dados (T1.2)

Convenções: tabelas no plural e snake_case; PK inteira autoincremento `id`; datas de auditoria em UTC.

### 2.1 `quartos`

| Campo | Tipo (SQLAlchemy) | Restrições / validação |
|---|---|---|
| id | Integer PK | autoincremento |
| numero | String(10) | obrigatório, **único**, 1–10 caracteres (ex.: "101", "12B") |
| tipo | Enum `TipoQuarto` | `SOLTEIRO`, `CASAL`, `DUPLO`, `SUITE` |
| capacidade | Integer | obrigatório, 1–10 |
| preco_diaria | Numeric(10,2) | obrigatório, > 0 |
| andar | Integer | obrigatório, ≥ 0 |
| descricao | String(500) | opcional |
| ativo | Boolean | padrão `true` (falso = em manutenção, não aceita reservas) |
| criado_em / atualizado_em | DateTime | preenchidos pelo servidor |

### 2.2 `hospedes`

| Campo | Tipo | Restrições / validação |
|---|---|---|
| id | Integer PK | |
| nome | String(120) | obrigatório, 3–120 caracteres |
| cpf | String(11) | obrigatório, **único**, só dígitos, **validação dos dígitos verificadores**; aceita entrada com máscara (`123.456.789-09`) e normaliza |
| email | String(254) | obrigatório, **único**, formato de e-mail válido |
| telefone | String(11) | opcional, 10–11 dígitos (normalizado) |
| data_nascimento | Date | opcional, deve estar no passado |
| criado_em / atualizado_em | DateTime | servidor |

### 2.3 `reservas`

| Campo | Tipo | Restrições / validação |
|---|---|---|
| id | Integer PK | |
| hospede_id | Integer FK → hospedes.id | obrigatório, hóspede deve existir |
| quarto_id | Integer FK → quartos.id | obrigatório, quarto deve existir e estar ativo |
| data_checkin | Date | obrigatório; na criação, não pode ser no passado |
| data_checkout | Date | obrigatório, **> data_checkin** |
| qtd_hospedes | Integer | obrigatório, 1 ≤ qtd ≤ capacidade do quarto |
| status | Enum `StatusReserva` | `CONFIRMADA` (padrão), `CANCELADA`, `CONCLUIDA` |
| valor_total | Numeric(10,2) | **calculado pelo servidor**: nº de diárias × preço da diária (somente leitura) |
| observacoes | String(500) | opcional |
| criado_em / atualizado_em | DateTime | servidor |

**Regras de negócio da reserva**

1. **Sem sobreposição:** não pode existir outra reserva não cancelada do mesmo quarto em que `checkin_novo < checkout_existente` **e** `checkout_novo > checkin_existente` → **409 Conflict**. (Checkout e check-in no mesmo dia são permitidos.)
2. Quarto inativo não aceita novas reservas → **409**.
3. `qtd_hospedes` acima da capacidade → erro de validação.
4. Reserva `CANCELADA` ou `CONCLUIDA` é final: não pode mais ser alterada → **409**.
5. `valor_total` é recalculado sempre que datas ou quarto mudarem.

### 2.4 `usuarios`

| Campo | Tipo | Restrições |
|---|---|---|
| id | Integer PK | |
| username | String(50) | obrigatório, único, 3–50 (letras, números, `_` e `.`) |
| senha_hash | String(255) | **hash bcrypt** — a senha nunca é armazenada em texto |
| ativo | Boolean | padrão `true` |
| criado_em | DateTime | servidor |

Não há cadastro público de usuários: o administrador inicial é criado por **script de seed** a partir de `ADMIN_USERNAME`/`ADMIN_PASSWORD` do `.env` (assim nenhuma credencial fica no repositório).

### 2.5 Exclusões e integridade

| Ação | Comportamento | Justificativa |
|---|---|---|
| DELETE hóspede **com** reservas | **409** com mensagem | preserva histórico financeiro/fiscal |
| DELETE quarto **com** reservas | **409** (sugere desativar via `PATCH ativo=false`) | idem |
| DELETE reserva | remoção física → 204 | cancelamento "lógico" é feito por `PATCH status=CANCELADA` |

---

## 3. Endpoints (T1.3)

Prefixo: nenhum (ex.: `http://localhost:8000/quartos`). Documentação: `/docs` (Swagger) e `/redoc`.
Paginação em todas as listagens: `skip` (padrão 0) e `limit` (padrão 20, máx. 100).
🔒 = exige `Authorization: Bearer <token>`. Quartos: leitura pública (catálogo). Hóspedes e reservas: **todas** as rotas protegidas (dados pessoais — LGPD).

### 3.1 Autenticação

| Método | Endpoint | Finalidade | Entrada | Respostas |
|---|---|---|---|---|
| POST | `/auth/login` | Obter token JWT | form `username`, `password` (padrão OAuth2 — habilita o botão *Authorize* do Swagger) | 200 `{access_token, token_type}` / 401 credenciais inválidas / 400 campos ausentes |
| GET 🔒 | `/auth/me` | Dados do usuário logado | token | 200 / 401 |

### 3.2 Quartos

| Método | Endpoint | Finalidade | Entrada | Respostas |
|---|---|---|---|---|
| GET | `/quartos` | Listar com filtros | query: `tipo`, `capacidade_min`, `preco_max`, `ativo`, `disponivel_de` + `disponivel_ate` (só quartos livres no período), `skip`, `limit` | 200 / 400 período inválido |
| GET | `/quartos/{id}` | Consultar quarto | id | 200 / 404 |
| POST 🔒 | `/quartos` | Criar | JSON | 201 + header `Location` / 400 / 401 / 409 número duplicado |
| PATCH 🔒 | `/quartos/{id}` | Atualizar parcialmente | id + JSON parcial | 200 / 400 / 401 / 404 / 409 número duplicado |
| DELETE 🔒 | `/quartos/{id}` | Excluir | id | 204 / 401 / 404 / 409 possui reservas |

### 3.3 Hóspedes

| Método | Endpoint | Finalidade | Entrada | Respostas |
|---|---|---|---|---|
| GET 🔒 | `/hospedes` | Listar com filtros | query: `nome` (contém, sem diferenciar maiúsculas), `cpf`, `email`, `skip`, `limit` | 200 / 401 |
| GET 🔒 | `/hospedes/{id}` | Consultar | id | 200 / 401 / 404 |
| GET 🔒 | `/hospedes/{id}/reservas` | Reservas do hóspede | id + `status` opcional | 200 / 401 / 404 |
| POST 🔒 | `/hospedes` | Criar | JSON | 201 / 400 / 401 / 409 CPF ou e-mail duplicado |
| PATCH 🔒 | `/hospedes/{id}` | Atualizar parcialmente | id + JSON parcial | 200 / 400 / 401 / 404 / 409 |
| DELETE 🔒 | `/hospedes/{id}` | Excluir | id | 204 / 401 / 404 / 409 possui reservas |

### 3.4 Reservas

| Método | Endpoint | Finalidade | Entrada | Respostas |
|---|---|---|---|---|
| GET 🔒 | `/reservas` | Listar com filtros | query: `status`, `hospede_id`, `quarto_id`, `data_de`, `data_ate`, `skip`, `limit` | 200 / 401 |
| GET 🔒 | `/reservas/{id}` | Consultar (com hóspede e quarto embutidos) | id | 200 / 401 / 404 |
| POST 🔒 | `/reservas` | Criar | JSON `hospede_id`, `quarto_id`, datas, `qtd_hospedes`, `observacoes` | 201 / 400 / 401 / 404 hóspede ou quarto inexistente / 409 sobreposição ou quarto inativo |
| PATCH 🔒 | `/reservas/{id}` | Alterar datas, quarto, qtd, status, observações | id + JSON parcial | 200 / 400 / 401 / 404 / 409 |
| DELETE 🔒 | `/reservas/{id}` | Excluir | id | 204 / 401 / 404 |

### 3.5 Justificativa do PATCH (para o relatório)

PATCH aplica **modificação parcial**: o cliente envia apenas os campos que deseja alterar (ex.: `{"status": "CANCELADA"}`). PUT, pela semântica HTTP (RFC 9110), **substitui a representação inteira** do recurso, exigindo reenviar todos os campos — o que é inadequado para operações frequentes como cancelar uma reserva ou mudar a diária de um quarto, e aumenta o risco de sobrescrever dados por engano.

---

## 4. Arquitetura e estrutura de pastas (T1.4)

Fluxo de uma requisição:

```
Cliente → CORS middleware → Router (FastAPI) → Dependências (sessão do banco, usuário autenticado via JWT)
        → Schema Pydantic (validação da entrada) → Service (regras de negócio)
        → Repository (consultas via SQLAlchemy ORM) → SQLite
        → Schema Pydantic (serialização da saída) → Resposta JSON + código HTTP
```

```
hotel-api/                 ← raiz do repositório
├── app/
│   ├── main.py                # cria o app, registra routers, CORS e handlers de erro
│   ├── core/
│   │   ├── config.py          # configurações lidas do .env (pydantic-settings)
│   │   └── security.py        # hash de senha (bcrypt) e geração/validação de JWT (PyJWT)
│   ├── db/
│   │   ├── base.py            # Base declarativa do SQLAlchemy
│   │   └── session.py         # engine e SessionLocal
│   ├── models/                # classes ORM ↔ tabelas (usuario, quarto, hospede, reserva)
│   ├── schemas/               # modelos Pydantic de entrada/saída
│   ├── repositories/          # acesso a dados (consultas ORM)
│   ├── services/              # regras de negócio (sobreposição, cálculo de valor, exclusões)
│   ├── routers/               # endpoints: auth, quartos, hospedes, reservas
│   ├── dependencies.py        # get_db, get_current_user
│   └── exceptions.py          # exceções de domínio + handlers globais
├── alembic/                   # migrations (estrutura reproduzível do banco)
├── alembic.ini
├── scripts/seed.py            # cria admin (do .env) e dados de exemplo
├── tests/                     # pytest + TestClient (banco de teste isolado)
├── docs/                      # modelagem, evidências (prints) para o relatório
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Bibliotecas planejadas: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic-settings`, `email-validator`, `pyjwt`, `bcrypt`, `python-multipart`, `pytest`, `httpx`.
Obs.: as aulas usaram `python-jose` e `passlib`; proponho **PyJWT** e **bcrypt** direto porque `passlib` não é mais mantido e apresenta incompatibilidade com versões atuais do `bcrypt` — isso vira argumento técnico no relatório (Crit. 2).

Variáveis de ambiente (`.env.example`): `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `CORS_ORIGINS`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.

### CORS (antecipando T6.4)

- `allow_origins`: lista lida de `CORS_ORIGINS` (ex.: `http://localhost:3000,http://localhost:5173`) — **sem `*`**.
- `allow_methods`: `GET, POST, PATCH, DELETE, OPTIONS` (exatamente os usados pela API).
- `allow_headers`: `Authorization, Content-Type`.
- `allow_credentials`: `false` — o token trafega no header `Authorization`, não em cookies.

---

## 5. Padrão de erros (T1.5)

Todas as respostas de erro em JSON com o mesmo formato:

```json
{ "detail": "Quarto 101 já possui reserva entre 2026-11-01 e 2026-11-05." }
```

Erros de validação (com lista por campo):

```json
{
  "detail": "Dados inválidos.",
  "erros": [ { "campo": "data_checkout", "mensagem": "Deve ser posterior à data de check-in." } ]
}
```

| Situação | Código |
|---|---|
| Sucesso em consulta/atualização | 200 |
| Criação | 201 (+ `Location`) |
| Exclusão | 204 (sem corpo) |
| Dados inválidos (tipo, formato, faixa, regra de campo, JSON malformado) | **400** (o 422 padrão do FastAPI é convertido por handler global) |
| Sem token / token inválido ou expirado | 401 (+ `WWW-Authenticate: Bearer`) |
| Usuário inativo | 403 |
| Recurso inexistente | 404 |
| Conflito (duplicidade, sobreposição, exclusão com dependentes, reserva finalizada) | 409 |
| Erro inesperado | 500 com mensagem genérica (sem stack trace) |

---

## 6. Decisões tomadas na Fase 1

| # | Decisão | Escolha | Justificativa |
|---|---|---|---|
| 1 | Código para dados inválidos | **400 Bad Request** | Alinha com a tabela modelo do professor; o 422 nativo do FastAPI é convertido para 400 com o formato `{detail, erros[]}` |
| 2 | Leitura de hóspedes e reservas | **Protegida (JWT)** | CPF, e-mail e histórico de hospedagem são dados pessoais (LGPD); quartos seguem públicos por serem catálogo |
