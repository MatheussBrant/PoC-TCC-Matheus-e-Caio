import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"

TABELAS_PERMITIDAS = {
    "documentos_tcc": {"id", "titulo", "autor", "orientador", "ano"},
    "documentos_artigos": {"id", "titulo", "autor", "periodico", "ano"}
}


def obter_conexao():
    return sqlite3.connect(DATABASE)


def validar_identificadores(tabela, campo):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida")

    if campo not in TABELAS_PERMITIDAS[tabela]:
        raise ValueError("Campo não permitido")


def buscar_registros(tabela, campo, valor):
    validar_identificadores(tabela, campo)

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

    try:
        resultados = buscar_registros(tabela, campo, valor)
        return jsonify({"resultados": resultados})
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400