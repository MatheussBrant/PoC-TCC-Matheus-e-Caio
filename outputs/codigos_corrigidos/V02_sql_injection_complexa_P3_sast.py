import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATABASE = 'academico.db'

CONSULTAS_BUSCA = {
    'documentos_tcc': {
        'titulo': 'SELECT * FROM documentos_tcc WHERE titulo = ?',
        'autor': 'SELECT * FROM documentos_tcc WHERE autor = ?',
        'curso': 'SELECT * FROM documentos_tcc WHERE curso = ?',
        'ano': 'SELECT * FROM documentos_tcc WHERE ano = ?'
    }
}


def obter_conexao():
    return sqlite3.connect(DATABASE)


def obter_query_permitida(tabela, campo):
    try:
        return CONSULTAS_BUSCA[tabela][campo]
    except KeyError as exc:
        raise ValueError('Tabela ou campo não permitido para busca') from exc


def buscar_registros(tabela, campo, valor):
    query = obter_query_permitida(tabela, campo)

    conexao = obter_conexao()
    try:
        cursor = conexao.cursor()
        cursor.execute(query, (valor,))
        return cursor.fetchall()
    finally:
        conexao.close()


@app.route('/documentos/buscar-complexo')
def buscar_documentos_complexo():
    campo = request.args.get('campo', 'titulo')
    valor = request.args.get('valor', '')
    tabela = request.args.get('tabela', 'documentos_tcc')

    try:
        resultados = buscar_registros(tabela, campo, valor)
    except ValueError as exc:
        return jsonify({'erro': str(exc)}), 400

    return jsonify({'resultados': resultados})