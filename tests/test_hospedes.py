from app.schemas.comum import cpf_valido


def test_validacao_de_cpf():
    assert cpf_valido("52998224725")
    assert not cpf_valido("52998224724")  # dígito verificador errado
    assert not cpf_valido("11111111111")  # sequência repetida
    assert not cpf_valido("123")


def test_cria_hospede_normalizando_cpf_email_e_telefone(client, auth):
    dados = {
        "nome": "  Maria Oliveira ",
        "cpf": "529.982.247-25",
        "email": "Maria.Oliveira@Example.com",
        "telefone": "(41) 99999-0000",
        "data_nascimento": "1992-05-10",
    }

    resposta = client.post("/hospedes", json=dados, headers=auth)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert resposta.headers["Location"] == f"/hospedes/{corpo['id']}"
    assert corpo["nome"] == "Maria Oliveira"
    assert corpo["cpf"] == "52998224725"
    assert corpo["email"] == "maria.oliveira@example.com"
    assert corpo["telefone"] == "41999990000"


def test_cria_hospede_com_dados_invalidos_retorna_400(client, auth):
    dados = {
        "nome": "Al",
        "cpf": "111.111.111-11",
        "email": "email-invalido",
        "telefone": "1234",
        "data_nascimento": "2999-01-01",
    }

    resposta = client.post("/hospedes", json=dados, headers=auth)

    assert resposta.status_code == 400
    erros = {erro["campo"]: erro["mensagem"] for erro in resposta.json()["erros"]}
    assert erros["cpf"] == "CPF inválido."
    assert erros["email"] == "E-mail inválido."
    assert set(erros) == {"nome", "cpf", "email", "telefone", "data_nascimento"}


def test_cria_hospede_sem_campos_obrigatorios_retorna_400(client, auth):
    resposta = client.post("/hospedes", json={}, headers=auth)

    assert resposta.status_code == 400
    assert {e["campo"] for e in resposta.json()["erros"]} == {"nome", "cpf", "email"}
    assert all(e["mensagem"] == "Campo obrigatório." for e in resposta.json()["erros"])


def test_cpf_ou_email_duplicado_retorna_409(client, auth, criar_hospede):
    existente = criar_hospede()

    mesmo_cpf = client.post(
        "/hospedes", json={"nome": "Outra Pessoa", "cpf": existente["cpf"], "email": "novo@example.com"}, headers=auth
    )
    mesmo_email = client.post(
        "/hospedes",
        json={"nome": "Outra Pessoa", "cpf": "11144477735", "email": existente["email"].upper()},
        headers=auth,
    )

    assert mesmo_cpf.status_code == 409
    assert mesmo_email.status_code == 409


def test_lista_hospedes_com_filtros(client, auth, criar_hospede):
    ana = criar_hospede(nome="Ana Paula Souza")
    criar_hospede(nome="Bruno Lima")

    por_nome = client.get("/hospedes", params={"nome": "PAULA"}, headers=auth)
    cpf_com_mascara = f"{ana['cpf'][:3]}.{ana['cpf'][3:6]}.{ana['cpf'][6:9]}-{ana['cpf'][9:]}"
    por_cpf = client.get("/hospedes", params={"cpf": cpf_com_mascara}, headers=auth)

    assert [h["id"] for h in por_nome.json()] == [ana["id"]]
    assert [h["id"] for h in por_cpf.json()] == [ana["id"]]
    assert len(client.get("/hospedes", headers=auth).json()) == 2


def test_consulta_hospede(client, auth, criar_hospede):
    hospede = criar_hospede()

    assert client.get(f"/hospedes/{hospede['id']}", headers=auth).json() == hospede
    assert client.get("/hospedes/999", headers=auth).status_code == 404


def test_atualiza_hospede_parcialmente(client, auth, criar_hospede):
    hospede = criar_hospede(telefone="41999990000")

    resposta = client.patch(
        f"/hospedes/{hospede['id']}", json={"nome": "Nome Corrigido", "telefone": None}, headers=auth
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Nome Corrigido"
    assert resposta.json()["telefone"] is None  # campo opcional pode ser limpo
    assert resposta.json()["cpf"] == hospede["cpf"]


def test_atualiza_hospede_com_email_de_outro_retorna_409(client, auth, criar_hospede):
    primeiro = criar_hospede()
    segundo = criar_hospede()

    resposta = client.patch(f"/hospedes/{segundo['id']}", json={"email": primeiro["email"]}, headers=auth)

    assert resposta.status_code == 409


def test_exclui_hospede(client, auth, criar_hospede):
    hospede = criar_hospede()

    assert client.delete(f"/hospedes/{hospede['id']}", headers=auth).status_code == 204
    assert client.get(f"/hospedes/{hospede['id']}", headers=auth).status_code == 404
    assert client.delete(f"/hospedes/{hospede['id']}", headers=auth).status_code == 404


def test_exclui_hospede_com_reservas_retorna_409(client, auth, criar_quarto, criar_hospede, criar_reserva):
    hospede = criar_hospede()
    criar_reserva(hospede["id"], criar_quarto()["id"], checkin=1, checkout=3)

    assert client.delete(f"/hospedes/{hospede['id']}", headers=auth).status_code == 409


def test_lista_reservas_do_hospede(client, auth, criar_quarto, criar_hospede, criar_reserva):
    hospede = criar_hospede()
    outro = criar_hospede()
    quarto = criar_quarto()
    reserva = criar_reserva(hospede["id"], quarto["id"], checkin=1, checkout=3)
    criar_reserva(outro["id"], quarto["id"], checkin=5, checkout=6)

    resposta = client.get(f"/hospedes/{hospede['id']}/reservas", headers=auth)

    assert resposta.status_code == 200
    assert [r["id"] for r in resposta.json()] == [reserva["id"]]
    assert client.get("/hospedes/999/reservas", headers=auth).status_code == 404
