import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"


def obter_conexao():
    return sqlite3.connect(DATABASE)


def buscar_documentos_por_aluno(aluno):
    with obter_conexao() as conexao:
        cursor = conexao.cursor()

        query = "SELECT * FROM documentos_tcc WHERE aluno = ?"
        cursor.execute(query, (aluno,))

        resultados = cursor.fetchall()

    return resultados


@app.route("/documentos/buscar")
def buscar_documentos():
    aluno = request.args.get("aluno", "")

    resultados = buscar_documentos_por_aluno(aluno)

    return jsonify({"resultados": resultados})