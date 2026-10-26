from tests.conftest import dias


def test_cria_quarto_retorna_201_com_location(client, auth):
    dados = {"numero": "12b", "tipo": "SUITE", "capacidade": 4, "preco_diaria": 450.5, "andar": 1}

    resposta = client.post("/quartos", json=dados, headers=auth)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert resposta.headers["Location"] == f"/quartos/{corpo['id']}"
    assert corpo["numero"] == "12B"
    assert corpo["preco_diaria"] == 450.5
    assert corpo["ativo"] is True


def test_cria_quarto_com_numero_duplicado_retorna_409(client, auth, criar_quarto):
    criar_quarto(numero="101")

    resposta = client.post(
        "/quartos",
        json={"numero": "101", "tipo": "CASAL", "capacidade": 2, "preco_diaria": 100, "andar": 1},
        headers=auth,
    )

    assert resposta.status_code == 409


def test_cria_quarto_com_dados_invalidos_retorna_400_com_erros_por_campo(client, auth):
    dados = {"numero": "", "tipo": "PRESIDENCIAL", "capacidade": 0, "preco_diaria": -10, "valor_extra": 1}

    resposta = client.post("/quartos", json=dados, headers=auth)

    assert resposta.status_code == 400
    corpo = resposta.json()
    assert corpo["detail"] == "Dados inválidos."
    campos = {erro["campo"] for erro in corpo["erros"]}
    assert campos == {"numero", "tipo", "capacidade", "preco_diaria", "andar", "valor_extra"}


def test_lista_quartos(client, criar_quarto):
    criar_quarto()
    criar_quarto()

    resposta = client.get("/quartos")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_lista_quartos_com_filtros(client, criar_quarto):
    criar_quarto(tipo="SOLTEIRO", capacidade=1, preco_diaria=150)
    suite = criar_quarto(tipo="SUITE", capacidade=4, preco_diaria=500)
    criar_quarto(tipo="SUITE", capacidade=4, preco_diaria=800)

    resposta = client.get("/quartos", params={"tipo": "SUITE", "capacidade_min": 3, "preco_max": 600})

    assert resposta.status_code == 200
    assert [q["id"] for q in resposta.json()] == [suite["id"]]


def test_lista_quartos_disponiveis_no_periodo(client, criar_quarto, criar_hospede, criar_reserva):
    ocupado = criar_quarto()
    livre = criar_quarto()
    criar_quarto(ativo=False)
    hospede = criar_hospede()
    criar_reserva(hospede["id"], ocupado["id"], checkin=10, checkout=15)

    resposta = client.get("/quartos", params={"disponivel_de": dias(12), "disponivel_ate": dias(14)})

    assert [q["id"] for q in resposta.json()] == [livre["id"]]


def test_filtro_de_disponibilidade_exige_periodo_valido(client):
    assert client.get("/quartos", params={"disponivel_de": dias(5)}).status_code == 400
    assert client.get("/quartos", params={"disponivel_de": dias(5), "disponivel_ate": dias(5)}).status_code == 400


def test_paginacao_limita_resultados(client, criar_quarto):
    for _ in range(3):
        criar_quarto()

    resposta = client.get("/quartos", params={"skip": 1, "limit": 1})

    assert len(resposta.json()) == 1
    assert client.get("/quartos", params={"limit": 500}).status_code == 400


def test_consulta_quarto_por_id(client, criar_quarto):
    quarto = criar_quarto()

    resposta = client.get(f"/quartos/{quarto['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["numero"] == quarto["numero"]


def test_consulta_quarto_inexistente_retorna_404(client):
    resposta = client.get("/quartos/999")

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Quarto 999 não encontrado."}


def test_atualiza_quarto_parcialmente(client, auth, criar_quarto):
    quarto = criar_quarto(preco_diaria=200)

    resposta = client.patch(f"/quartos/{quarto['id']}", json={"preco_diaria": 230, "ativo": False}, headers=auth)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["preco_diaria"] == 230
    assert corpo["ativo"] is False
    assert corpo["numero"] == quarto["numero"]  # campos não enviados permanecem


def test_atualiza_quarto_com_campo_obrigatorio_nulo_retorna_400(client, auth, criar_quarto):
    quarto = criar_quarto()

    resposta = client.patch(f"/quartos/{quarto['id']}", json={"numero": None}, headers=auth)

    assert resposta.status_code == 400
    assert resposta.json()["erros"] == [{"campo": "numero", "mensagem": "Não pode ser nulo."}]


def test_atualiza_quarto_sem_campos_retorna_400(client, auth, criar_quarto):
    quarto = criar_quarto()

    assert client.patch(f"/quartos/{quarto['id']}", json={}, headers=auth).status_code == 400


def test_atualiza_quarto_para_numero_existente_retorna_409(client, auth, criar_quarto):
    criar_quarto(numero="201")
    quarto = criar_quarto(numero="202")

    resposta = client.patch(f"/quartos/{quarto['id']}", json={"numero": "201"}, headers=auth)

    assert resposta.status_code == 409


def test_atualiza_quarto_inexistente_retorna_404(client, auth):
    assert client.patch("/quartos/999", json={"andar": 2}, headers=auth).status_code == 404


def test_exclui_quarto(client, auth, criar_quarto):
    quarto = criar_quarto()

    resposta = client.delete(f"/quartos/{quarto['id']}", headers=auth)

    assert resposta.status_code == 204
    assert resposta.content == b""
    assert client.get(f"/quartos/{quarto['id']}").status_code == 404


def test_exclui_quarto_inexistente_retorna_404(client, auth):
    assert client.delete("/quartos/999", headers=auth).status_code == 404


def test_exclui_quarto_com_reservas_retorna_409(client, auth, criar_quarto, criar_hospede, criar_reserva):
    quarto = criar_quarto()
    criar_reserva(criar_hospede()["id"], quarto["id"], checkin=1, checkout=2)

    resposta = client.delete(f"/quartos/{quarto['id']}", headers=auth)

    assert resposta.status_code == 409
    assert "desative" in resposta.json()["detail"]
