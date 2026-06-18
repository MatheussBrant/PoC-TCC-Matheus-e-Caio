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
    query = CONSULTAS_PERMITIDAS.get((tabela, campo))

    if query is None:
        raise ValueError("Tabela ou campo não permitido")

    conexao = obter_conexao()

    try:
        cursor = conexao.cursor()
        cursor.execute(query, (valor,))
        resultados = cursor.fetchall()
        return resultados
    finally:
        conexao.close()


@app.route("/documentos/buscar-complexo")
def buscar_documentos_complexo():
    campo = request.args.get("campo", "titulo")
    valor = request.args.get("valor", "")
    tabela = request.args.get("tabela", "documentos_tcc")

    try:
        resultados = buscar_registros(tabela, campo, valor)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"resultados": resultados})