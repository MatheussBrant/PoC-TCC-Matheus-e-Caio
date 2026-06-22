import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

DATABASE = "academico.db"

VALID_TABLES = {'documentos_tcc', 'outra_tabela_valida'}
VALID_CAMPOS = {'titulo', 'autor', 'ano'}


def obter_conexao():
    return sqlite3.connect(DATABASE)


def buscar_registros(tabela, campo, valor):
    if tabela not in VALID_TABLES:
        abort(400, description="Tabela inválida.")
    if campo not in VALID_CAMPOS:
        abort(400, description="Campo inválido.")

    conexao = obter_conexao()
    cursor = conexao.cursor()

    query = f"SELECT * FROM {tabela} WHERE {campo} = ?"
    cursor.execute(query, (valor,))
    resultados = cursor.fetchall()

    conexao.close()
    return resultados


@app.route("/documentos/buscar-complexo")
def buscar_documentos_complexo():
    campo = request.args.get("campo", "titulo")
    valor = request.args.get("valor", "")
    tabela = request.args.get("tabela", "documentos_tcc")

    resultados = buscar_registros(tabela, campo, valor)

    return jsonify({"resultados": resultados})