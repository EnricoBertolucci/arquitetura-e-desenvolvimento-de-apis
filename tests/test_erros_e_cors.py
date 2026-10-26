from fastapi.testclient import TestClient

from app.main import app
from app.services.quarto import QuartoServico


def test_status_da_api(client):
    resposta = client.get("/")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_documentacao_openapi_disponivel_sem_respostas_422(client):
    assert client.get("/docs").status_code == 200
    esquema = client.get("/openapi.json").json()

    codigos = {codigo for rota in esquema["paths"].values() for op in rota.values() for codigo in op["responses"]}
    assert "422" not in codigos
    assert "400" in codigos


def test_json_malformado_retorna_400(client, auth):
    resposta = client.post(
        "/quartos", content="{numero: 101", headers=auth | {"Content-Type": "application/json"}
    )

    assert resposta.status_code == 400
    assert resposta.json()["erros"] == [{"campo": "corpo", "mensagem": "JSON malformado."}]


def test_parametro_de_rota_com_tipo_errado_retorna_400(client):
    resposta = client.get("/quartos/abc")

    assert resposta.status_code == 400
    assert resposta.json()["erros"][0]["campo"] == "quarto_id"


def test_rota_inexistente_retorna_404_em_json(client):
    resposta = client.get("/rota-que-nao-existe")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Rota não encontrada."}


def test_metodo_nao_permitido_retorna_405(client):
    resposta = client.put("/quartos/1", json={})

    assert resposta.status_code == 405


def test_erro_inesperado_retorna_500_sem_detalhes_internos(monkeypatch):
    def falhar(*_args, **_kwargs):
        raise RuntimeError("falha interna com detalhe sensível")

    monkeypatch.setattr(QuartoServico, "listar", falhar)
    cliente = TestClient(app, raise_server_exceptions=False)

    resposta = cliente.get("/quartos")

    assert resposta.status_code == 500
    assert resposta.json() == {"detail": "Erro interno do servidor."}


# --- CORS ------------------------------------------------------------------
# Nos testes, CORS_ORIGINS = "http://localhost:5173" (ver conftest.py).


def test_cors_preflight_de_origem_permitida(client):
    resposta = client.options(
        "/quartos",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert resposta.status_code == 200
    assert resposta.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "PATCH" in resposta.headers["Access-Control-Allow-Methods"]
    assert "PUT" not in resposta.headers["Access-Control-Allow-Methods"]
    assert "access-control-allow-credentials" not in resposta.headers


def test_cors_bloqueia_origem_nao_listada(client):
    resposta = client.options(
        "/quartos",
        headers={"Origin": "http://site-malicioso.example", "Access-Control-Request-Method": "GET"},
    )

    assert resposta.status_code == 400
    assert "access-control-allow-origin" not in resposta.headers


def test_cors_rejeita_metodo_nao_listado(client):
    resposta = client.options(
        "/quartos",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "PUT"},
    )

    assert resposta.status_code == 400


def test_cors_em_requisicao_simples(client):
    resposta = client.get("/quartos", headers={"Origin": "http://localhost:5173"})

    assert resposta.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert resposta.headers["Access-Control-Expose-Headers"] == "Location"
