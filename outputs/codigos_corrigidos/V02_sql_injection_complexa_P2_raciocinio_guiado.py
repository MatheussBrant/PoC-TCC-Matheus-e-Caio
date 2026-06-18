import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = "academico.db"

TABELAS_PERMITIDAS = {
    "documentos_tcc": {"id", "titulo", "autor", "ano", "resumo"}
}


def obter_conexao():
    return sqlite3.connect(DATABASE)


def validar_tabela_e_campo(tabela, campo):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida")

    if campo not in TABELAS_PERMITIDAS[tabela]:
        raise ValueError("Campo não permitido")

    return tabela, campo


def buscar_registros(tabela, campo, valor):
    tabela, campo = validar_tabela_e_campo(tabela, campo)

    conexao = obter_conexao()
    try:
        cursor = conexao.cursor()
        query = f"SELECT * FROM {tabela} WHERE {campo} = ?"
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