from datetime import timedelta

import pytest

from app.core.security import criar_token_acesso
from tests.conftest import SENHA_TESTE, USUARIO_TESTE


def test_login_retorna_token_jwt(client):
    resposta = client.post("/auth/login", data={"username": USUARIO_TESTE, "password": SENHA_TESTE})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["expires_in"] == 15 * 60
    assert corpo["access_token"].count(".") == 2  # header.payload.assinatura


@pytest.mark.parametrize("username, senha", [(USUARIO_TESTE, "senha-errada"), ("inexistente", SENHA_TESTE)])
def test_login_com_credenciais_invalidas_retorna_401(client, username, senha):
    resposta = client.post("/auth/login", data={"username": username, "password": senha})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Usuário ou senha incorretos."}
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


def test_login_de_usuario_inativo_retorna_403(client):
    resposta = client.post("/auth/login", data={"username": "desativado", "password": SENHA_TESTE})

    assert resposta.status_code == 403


def test_login_sem_campos_retorna_400(client):
    resposta = client.post("/auth/login", data={})

    assert resposta.status_code == 400
    campos = {erro["campo"] for erro in resposta.json()["erros"]}
    assert {"username", "password"} <= campos


def test_me_retorna_usuario_autenticado(client, auth):
    resposta = client.get("/auth/me", headers=auth)

    assert resposta.status_code == 200
    assert resposta.json()["username"] == USUARIO_TESTE
    assert "senha_hash" not in resposta.json()


def test_me_sem_token_retorna_401(client):
    resposta = client.get("/auth/me")

    assert resposta.status_code == 401
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token, mensagem",
    [
        ("token-qualquer", "Token de acesso inválido."),
        (criar_token_acesso(USUARIO_TESTE, expira_em=timedelta(seconds=-1)), "Token de acesso expirado. Faça login novamente."),
        (criar_token_acesso("usuario-apagado"), "Token de acesso inválido."),
    ],
    ids=["malformado", "expirado", "usuario-inexistente"],
)
def test_token_invalido_retorna_401(client, token, mensagem):
    resposta = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == mensagem


def test_token_assinado_com_outra_chave_retorna_401(client):
    import jwt

    falso = jwt.encode({"sub": USUARIO_TESTE, "exp": 9999999999}, "outra-chave-secreta-com-mais-de-32-bytes", "HS256")
    resposta = client.get("/auth/me", headers={"Authorization": f"Bearer {falso}"})

    assert resposta.status_code == 401


def test_token_de_usuario_inativo_retorna_403(client):
    token = criar_token_acesso("desativado")
    resposta = client.get("/hospedes", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "Usuário inativo."}


@pytest.mark.parametrize(
    "metodo, rota",
    [
        ("post", "/quartos"),
        ("patch", "/quartos/1"),
        ("delete", "/quartos/1"),
        ("get", "/hospedes"),
        ("get", "/hospedes/1"),
        ("post", "/hospedes"),
        ("get", "/reservas"),
        ("post", "/reservas"),
        ("delete", "/reservas/1"),
    ],
)
def test_rotas_protegidas_exigem_token(client, metodo, rota):
    resposta = client.request(metodo, rota, json={})

    assert resposta.status_code == 401


def test_leitura_de_quartos_e_publica(client):
    assert client.get("/quartos").status_code == 200
