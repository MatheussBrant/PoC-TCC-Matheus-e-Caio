import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"


def obter_conexao():
    return sqlite3.connect(DATABASE)


def montar_filtro(campo, valor):
    return f"{campo} = '{valor}'"


def buscar_registros(tabela, campo, valor):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    filtro = montar_filtro(campo, valor)
    query = f"SELECT * FROM {tabela} WHERE {filtro}"

    cursor.execute(query)
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
