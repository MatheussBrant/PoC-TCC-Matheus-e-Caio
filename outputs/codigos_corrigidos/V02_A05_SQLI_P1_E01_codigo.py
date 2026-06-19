import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"

# Lista de tabelas e campos permitidos para evitar injeção via nomes
TABELAS_VALIDAS = {"documentos_tcc", "usuarios", "outra_tabela"}
CAMPOS_VALIDOS = {"titulo", "autor", "id", "data"}

def obter_conexao():
    return sqlite3.connect(DATABASE)

def buscar_registros(tabela, campo, valor):
    if tabela not in TABELAS_VALIDAS:
        raise ValueError("Tabela inválida")
    if campo not in CAMPOS_VALIDOS:
        raise ValueError("Campo inválido")

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
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    return jsonify({"resultados": resultados})