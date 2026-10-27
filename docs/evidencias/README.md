# Evidências de funcionamento

Capturas de tela da API em execução, obtidas pelo Swagger UI (`/docs`), pelo terminal e pelo editor, a partir de um banco recém-criado (`alembic upgrade head` + `python -m scripts.seed`).

| Arquivo | O que demonstra |
|---|---|
| `01-estrutura-pastas.png` | Organização do projeto em camadas |
| `02-modelo-orm.png` | Classe ORM `Reserva` mapeada para a tabela `reservas` |
| `03-erro-validacao.png` | `POST /hospedes` com dados inválidos → 400 com erros por campo |
| `04a-rota-protegida-sem-token.png` | `GET /hospedes` sem token → 401 |
| `04b-rota-protegida-com-token.png` | `GET /hospedes` autenticado → 200 |
| `05-cors.png` | Configuração de CORS e resposta ao preflight |
| `06-get-lista.png` | `GET /quartos` → 200 |
| `07-get-filtro.png` | `GET /quartos?tipo=SUITE&capacidade_min=3` → 200 |
| `08-post.png` | `POST /reservas` → 201 com valor total calculado |
| `09-patch.png` | `PATCH /reservas/4` → 200 com valor recalculado |
| `10-delete.png` | `DELETE /reservas/4` → 204 |
| `11-testes-pytest.png` | Execução da suíte de testes automatizados |
