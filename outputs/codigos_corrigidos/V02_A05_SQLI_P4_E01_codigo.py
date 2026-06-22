import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"


CONSULTAS_PERMITIDAS = {
    ("documentos_tcc", "aluno"): "SELECT * FROM documentos_tcc WHERE aluno = ?",
    ("documentos_tcc", "titulo"): "SELECT * FROM documentos_tcc WHERE titulo = ?",
}


def obter_conexao():
    return sqlite3.connect(DATABASE)


def buscar_registros(tabela, campo, valor):
    if (tabela, campo) not in CONSULTAS_PERMITIDAS:
        raise ValueError(f"Parâmetros inválidos: tabela '{tabela}' ou campo '{campo}' não permitidos.")

    query = CONSULTAS_PERMITIDAS[(tabela, campo)]

    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute(query, (valor,))
    resultados = cursor.fetchall()

    conexao.close()
    return resultados


@app.route("/documentos/buscar-complexo")
def buscar_documentos_complexo():
    campo = request.args.get("campo", "titulo")
    valor = request.args.get("valor", "")
    tabela = request.args.get("tabela", "documentos_tcc")

    try:
        resultados = buscar_registros(tabela, campo, valor)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    return jsonify({"resultados": resultados})