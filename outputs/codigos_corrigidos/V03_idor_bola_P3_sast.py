from flask import Flask, request, jsonify

app = Flask(__name__)

DOCUMENTOS = {
    "d1": {
        "titulo": "TCC - versão final",
        "arquivo": "tcc_final_g1.pdf",
        "tipo": "tcc",
        "visibilidade": "restrita"
    },
    "d2": {
        "titulo": "Declaração de estágio",
        "arquivo": "declaracao_estagio_g2.pdf",
        "tipo": "estagio",
        "visibilidade": "restrita"
    },
    "d3": {
        "titulo": "Ata de banca",
        "arquivo": "ata_banca_g1.pdf",
        "tipo": "banca",
        "visibilidade": "restrita"
    }
}

VINCULOS = {
    "u1": ["d1", "d3"],
    "u2": ["d1", "d3"],
    "u3": ["d2"],
}

USUARIOS = {
    "u1": {"id": "u1", "nome": "Matheus", "perfil": "aluno"},
    "u2": {"id": "u2", "nome": "Caio", "perfil": "aluno"},
    "u3": {"id": "u3", "nome": "Outro aluno", "perfil": "aluno"},
    "u4": {"id": "u4", "nome": "Professor", "perfil": "professor"},
    "u5": {"id": "u5", "nome": "Coordenador", "perfil": "coordenador"},
}

PERFIS_COM_ACESSO_TOTAL = {"professor", "coordenador"}


def obter_usuario_logado():
    usuario_id = request.headers.get("X-User-Id")
    return USUARIOS.get(usuario_id)


def buscar_documento(documento_id):
    return DOCUMENTOS.get(documento_id)


def usuario_tem_acesso_ao_documento(usuario, documento_id, documento):
    if usuario is None or documento is None:
        return False

    if documento.get("visibilidade") == "publica":
        return True

    if usuario.get("perfil") in PERFIS_COM_ACESSO_TOTAL:
        return True

    documentos_vinculados = VINCULOS.get(usuario.get("id"), [])
    return documento_id in documentos_vinculados


@app.route("/documentos/<documento_id>")
def visualizar_documento(documento_id):
    usuario = obter_usuario_logado()

    if usuario is None:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    documento = buscar_documento(documento_id)

    if documento is None or not usuario_tem_acesso_ao_documento(usuario, documento_id, documento):
        return jsonify({"erro": "Documento não encontrado"}), 404

    return jsonify(documento)