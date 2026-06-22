import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

DATABASE = "academico.db"

TABELAS_VALIDAS = {"documentos_tcc", "outra_tabela_permitida"}  # Lista de tabelas permitidas
CAMPOS_VALIDOS = {"titulo", "autor", "ano"}  # Campos permitidos para filtro

def obter_conexao():
    return sqlite3.connect(DATABASE)


def buscar_registros(tabela, campo, valor):
    if tabela not in TABELAS_VALIDAS or campo not in CAMPOS_VALIDOS:
        abort(400, description="Parâmetro inválido para tabela ou campo")

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