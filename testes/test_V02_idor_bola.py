from vulneraveis import V02_idor_bola as app_idor


def test_usuario_vinculado_pode_acessar_documento():
    client = app_idor.app.test_client()

    resposta = client.get(
        "/documentos/d1",
        headers={"X-User-Id": "u1"}
    )

    assert resposta.status_code == 200
    assert resposta.get_json()["arquivo"] == "tcc_final_g1.pdf"


def test_usuario_nao_vinculado_nao_pode_acessar_documento():
    client = app_idor.app.test_client()

    resposta = client.get(
        "/documentos/d1",
        headers={"X-User-Id": "u3"}
    )

    assert resposta.status_code == 403


def test_professor_nao_tem_acesso_automatico_a_todos_documentos():
    client = app_idor.app.test_client()

    resposta = client.get(
        "/documentos/d1",
        headers={"X-User-Id": "u4"}
    )

    assert resposta.status_code == 403


def test_coordenador_pode_acessar_qualquer_documento():
    client = app_idor.app.test_client()

    resposta = client.get(
        "/documentos/d2",
        headers={"X-User-Id": "u5"}
    )

    assert resposta.status_code == 200
    assert resposta.get_json()["arquivo"] == "declaracao_estagio_g2.pdf"


def test_usuario_nao_autenticado_recebe_401():
    client = app_idor.app.test_client()

    resposta = client.get("/documentos/d1")

    assert resposta.status_code == 401


def test_documento_inexistente_retorna_404_para_usuario_autenticado():
    client = app_idor.app.test_client()

    resposta = client.get(
        "/documentos/inexistente",
        headers={"X-User-Id": "u1"}
    )

    assert resposta.status_code == 404
