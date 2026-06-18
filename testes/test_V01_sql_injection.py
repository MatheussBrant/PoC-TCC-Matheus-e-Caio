import importlib.util
from pathlib import Path

import sqlite3


def carregar_modulo():
    caminho = Path(__file__).resolve().parent / "V01_sql_injection.py"

    spec = importlib.util.spec_from_file_location(
        "V01_sql_injection",
        caminho
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo


def preparar_banco_teste(tmp_path, monkeypatch, modulo):
    db_path = tmp_path / "academico_teste.db"

    conexao = sqlite3.connect(db_path)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE documentos_tcc (
            id INTEGER PRIMARY KEY,
            titulo TEXT,
            aluno TEXT
        )
    """)

    cursor.execute("""
        INSERT INTO documentos_tcc (titulo, aluno)
        VALUES ('TCC - versão final', 'Matheus')
    """)

    cursor.execute("""
        INSERT INTO documentos_tcc (titulo, aluno)
        VALUES ('Declaração de estágio', 'Caio')
    """)

    conexao.commit()
    conexao.close()

    monkeypatch.setattr(modulo, "DATABASE", str(db_path))

    return db_path


def test_busca_legitima_retorna_apenas_documento_esperado(tmp_path, monkeypatch):
    modulo = carregar_modulo()
    preparar_banco_teste(tmp_path, monkeypatch, modulo)

    resultados = modulo.buscar_documentos_por_aluno("Matheus")

    assert len(resultados) == 1
    assert resultados[0][2] == "Matheus"


def test_sql_injection_nao_retorna_todos_os_registros(tmp_path, monkeypatch):
    modulo = carregar_modulo()
    preparar_banco_teste(tmp_path, monkeypatch, modulo)

    payload = "' OR '1'='1"

    resultados = modulo.buscar_documentos_por_aluno(payload)

    assert resultados == []


def test_senha_de_outro_aluno_nao_retorna_documento_errado(tmp_path, monkeypatch):
    modulo = carregar_modulo()
    preparar_banco_teste(tmp_path, monkeypatch, modulo)

    resultados = modulo.buscar_documentos_por_aluno("Caio")

    assert len(resultados) == 1
    assert resultados[0][2] == "Caio"
    assert resultados[0][2] != "Matheus"


def test_codigo_corrigido_nao_deve_montar_sql_com_f_string():
    modulo = carregar_modulo()

    caminho = Path(modulo.__file__)
    conteudo = caminho.read_text(encoding="utf-8")

    assert "f\"SELECT" not in conteudo
    assert "f'SELECT" not in conteudo
    assert ".format(" not in conteudo
    assert "% aluno" not in conteudo
    assert "WHERE aluno = ?" in conteudo
