import sqlite3
import pytest

from vulneraveis import V02_sql_injection_complexa as app_sql


@pytest.fixture
def banco_teste(tmp_path, monkeypatch):
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

    monkeypatch.setattr(app_sql, "DATABASE", str(db_path))

    return db_path


def test_busca_legitima_retorna_apenas_documento_esperado(banco_teste):
    resultados = app_sql.buscar_registros(
        tabela="documentos_tcc",
        campo="aluno",
        valor="Matheus"
    )

    assert len(resultados) == 1
    assert resultados[0][2] == "Matheus"


def test_sql_injection_nao_retorna_todos_os_registros(banco_teste):
    payload = "' OR '1'='1"

    resultados = app_sql.buscar_registros(
        tabela="documentos_tcc",
        campo="aluno",
        valor=payload
    )

    assert resultados == []


def test_tabela_nao_permitida_deve_ser_rejeitada(banco_teste):
    with pytest.raises(ValueError):
        app_sql.buscar_registros(
            tabela="sqlite_master",
            campo="name",
            valor="documentos_tcc"
        )


def test_campo_nao_permitido_deve_ser_rejeitado(banco_teste):
    with pytest.raises(ValueError):
        app_sql.buscar_registros(
            tabela="documentos_tcc",
            campo="1=1 --",
            valor="Matheus"
        )
