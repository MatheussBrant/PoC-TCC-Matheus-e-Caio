import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"


def obter_conexao():
    return sqlite3.connect(DATABASE)


def buscar_registros(tabela, campo, valor):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # Validação simples dos nomes da tabela e do campo para evitar SQL Injection
    allowed_tables = ["documentos_tcc", "outra_tabela"]
    allowed_columns = ["titulo", "autor", "ano"]

    if tabela not in allowed_tables:
        raise ValueError("Tabela não permitida")
    if campo not in allowed_columns:
        raise ValueError("Campo não permitido")

    # Query parametrizada para evitar injeção
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