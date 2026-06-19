import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"


def obter_conexao():
    return sqlite3.connect(DATABASE)


def buscar_registros(tabela, campo, valor):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # Definir listas de campos e tabelas permitidas para evitar SQL Injection via injeção de nomes dinâmicos
    tabelas_permitidas = ["documentos_tcc", "outra_tabela"]
    campos_permitidos = ["titulo", "autor", "ano"]

    if tabela not in tabelas_permitidas:
        raise ValueError("Tabela inválida")

    if campo not in campos_permitidos:
        raise ValueError("Campo inválido")

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
        return jsonify({"error": str(e)}), 400

    return jsonify({"resultados": resultados})