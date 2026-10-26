import pytest

from tests.conftest import dias


@pytest.fixture
def cenario(criar_quarto, criar_hospede):
    """Um hóspede e um quarto de casal com diária de R$ 250,00."""
    return {"hospede": criar_hospede(), "quarto": criar_quarto(capacidade=2, preco_diaria=250)}


def _dados(cenario, checkin=10, checkout=13, qtd=2, **extra):
    return {
        "hospede_id": cenario["hospede"]["id"],
        "quarto_id": cenario["quarto"]["id"],
        "data_checkin": dias(checkin),
        "data_checkout": dias(checkout),
        "qtd_hospedes": qtd,
        **extra,
    }


def test_cria_reserva_calculando_valor_total(client, auth, cenario):
    resposta = client.post("/reservas", json=_dados(cenario, observacoes="Berço no quarto."), headers=auth)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert resposta.headers["Location"] == f"/reservas/{corpo['id']}"
    assert corpo["status"] == "CONFIRMADA"
    assert corpo["valor_total"] == 750.0  # 3 diárias x R$ 250,00
    assert corpo["hospede"]["id"] == cenario["hospede"]["id"]
    assert corpo["quarto"]["numero"] == cenario["quarto"]["numero"]


def test_cliente_nao_pode_definir_valor_total(client, auth, cenario):
    resposta = client.post("/reservas", json=_dados(cenario, valor_total=1), headers=auth)

    assert resposta.status_code == 400
    assert resposta.json()["erros"][0]["campo"] == "valor_total"


def test_reserva_sobreposta_no_mesmo_quarto_retorna_409(client, auth, cenario):
    client.post("/reservas", json=_dados(cenario, checkin=10, checkout=13), headers=auth)

    resposta = client.post("/reservas", json=_dados(cenario, checkin=12, checkout=15), headers=auth)

    assert resposta.status_code == 409
    assert "já possui reserva" in resposta.json()["detail"]


def test_checkin_no_dia_do_checkout_anterior_e_permitido(client, auth, cenario):
    client.post("/reservas", json=_dados(cenario, checkin=10, checkout=13), headers=auth)

    resposta = client.post("/reservas", json=_dados(cenario, checkin=13, checkout=14), headers=auth)

    assert resposta.status_code == 201


def test_reserva_cancelada_libera_o_periodo(client, auth, cenario):
    primeira = client.post("/reservas", json=_dados(cenario), headers=auth).json()
    client.patch(f"/reservas/{primeira['id']}", json={"status": "CANCELADA"}, headers=auth)

    resposta = client.post("/reservas", json=_dados(cenario), headers=auth)

    assert resposta.status_code == 201


def test_quarto_inativo_nao_aceita_reserva(client, auth, criar_quarto, cenario):
    inativo = criar_quarto(ativo=False)

    resposta = client.post("/reservas", json=_dados(cenario) | {"quarto_id": inativo["id"]}, headers=auth)

    assert resposta.status_code == 409


def test_qtd_hospedes_acima_da_capacidade_retorna_400(client, auth, cenario):
    resposta = client.post("/reservas", json=_dados(cenario, qtd=3), headers=auth)

    assert resposta.status_code == 400
    assert resposta.json()["erros"][0]["campo"] == "qtd_hospedes"


@pytest.mark.parametrize(
    "checkin, checkout, campo",
    [(-1, 2, "data_checkin"), (5, 5, "data_checkout"), (5, 3, "data_checkout")],
    ids=["checkin-no-passado", "checkout-igual", "checkout-anterior"],
)
def test_periodo_invalido_retorna_400(client, auth, cenario, checkin, checkout, campo):
    resposta = client.post("/reservas", json=_dados(cenario, checkin=checkin, checkout=checkout), headers=auth)

    assert resposta.status_code == 400
    assert resposta.json()["erros"][0]["campo"] == campo


@pytest.mark.parametrize("campo", ["hospede_id", "quarto_id"])
def test_hospede_ou_quarto_inexistente_retorna_404(client, auth, cenario, campo):
    resposta = client.post("/reservas", json=_dados(cenario) | {campo: 999}, headers=auth)

    assert resposta.status_code == 404


def test_lista_e_filtra_reservas(client, auth, cenario, criar_quarto):
    outro_quarto = criar_quarto()
    a = client.post("/reservas", json=_dados(cenario, checkin=1, checkout=2), headers=auth).json()
    b = client.post("/reservas", json=_dados(cenario, checkin=20, checkout=22), headers=auth).json()
    c = client.post(
        "/reservas", json=_dados(cenario, checkin=1, checkout=2) | {"quarto_id": outro_quarto["id"]}, headers=auth
    ).json()
    client.patch(f"/reservas/{c['id']}", json={"status": "CANCELADA"}, headers=auth)

    todas = client.get("/reservas", headers=auth).json()
    canceladas = client.get("/reservas", params={"status": "CANCELADA"}, headers=auth).json()
    por_quarto = client.get("/reservas", params={"quarto_id": cenario["quarto"]["id"]}, headers=auth).json()
    por_periodo = client.get("/reservas", params={"data_de": dias(15), "data_ate": dias(30)}, headers=auth).json()

    assert len(todas) == 3
    assert [r["id"] for r in canceladas] == [c["id"]]
    assert [r["id"] for r in por_quarto] == [a["id"], b["id"]]
    assert [r["id"] for r in por_periodo] == [b["id"]]


def test_filtro_de_periodo_invertido_retorna_400(client, auth):
    resposta = client.get("/reservas", params={"data_de": dias(10), "data_ate": dias(1)}, headers=auth)

    assert resposta.status_code == 400


def test_consulta_reserva_com_hospede_e_quarto(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario), headers=auth).json()

    resposta = client.get(f"/reservas/{criada['id']}", headers=auth)

    assert resposta.status_code == 200
    assert resposta.json()["hospede"]["nome"] == cenario["hospede"]["nome"]
    assert client.get("/reservas/999", headers=auth).status_code == 404


def test_alterar_datas_recalcula_valor(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario, checkin=10, checkout=13), headers=auth).json()

    resposta = client.patch(f"/reservas/{criada['id']}", json={"data_checkout": dias(15)}, headers=auth)

    assert resposta.status_code == 200
    assert resposta.json()["valor_total"] == 1250.0  # 5 diárias


def test_trocar_de_quarto_recalcula_valor_e_valida_capacidade(client, auth, cenario, criar_quarto):
    criada = client.post("/reservas", json=_dados(cenario, qtd=2), headers=auth).json()
    individual = criar_quarto(capacidade=1, preco_diaria=100)
    suite = criar_quarto(capacidade=4, preco_diaria=400)

    pequeno = client.patch(f"/reservas/{criada['id']}", json={"quarto_id": individual["id"]}, headers=auth)
    troca = client.patch(f"/reservas/{criada['id']}", json={"quarto_id": suite["id"]}, headers=auth)

    assert pequeno.status_code == 400
    assert troca.status_code == 200
    assert troca.json()["valor_total"] == 1200.0  # 3 diárias x R$ 400,00


def test_alteracao_nao_pode_gerar_sobreposicao(client, auth, cenario):
    client.post("/reservas", json=_dados(cenario, checkin=10, checkout=13), headers=auth)
    outra = client.post("/reservas", json=_dados(cenario, checkin=20, checkout=22), headers=auth).json()

    resposta = client.patch(f"/reservas/{outra['id']}", json={"data_checkin": dias(12)}, headers=auth)

    assert resposta.status_code == 409


def test_alteracao_com_checkout_antes_do_checkin_retorna_400(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario, checkin=10, checkout=13), headers=auth).json()

    resposta = client.patch(f"/reservas/{criada['id']}", json={"data_checkout": dias(9)}, headers=auth)

    assert resposta.status_code == 400


def test_reserva_cancelada_nao_pode_ser_alterada(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario), headers=auth).json()

    cancelada = client.patch(f"/reservas/{criada['id']}", json={"status": "CANCELADA"}, headers=auth)
    resposta = client.patch(f"/reservas/{criada['id']}", json={"observacoes": "teste"}, headers=auth)

    assert cancelada.status_code == 200
    assert cancelada.json()["status"] == "CANCELADA"
    assert resposta.status_code == 409


def test_status_invalido_retorna_400(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario), headers=auth).json()

    resposta = client.patch(f"/reservas/{criada['id']}", json={"status": "PENDENTE"}, headers=auth)

    assert resposta.status_code == 400


def test_hospede_da_reserva_nao_pode_ser_trocado(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario), headers=auth).json()

    resposta = client.patch(f"/reservas/{criada['id']}", json={"hospede_id": 2}, headers=auth)

    assert resposta.status_code == 400


def test_exclui_reserva(client, auth, cenario):
    criada = client.post("/reservas", json=_dados(cenario), headers=auth).json()

    assert client.delete(f"/reservas/{criada['id']}", headers=auth).status_code == 204
    assert client.get(f"/reservas/{criada['id']}", headers=auth).status_code == 404
    assert client.delete(f"/reservas/{criada['id']}", headers=auth).status_code == 404
