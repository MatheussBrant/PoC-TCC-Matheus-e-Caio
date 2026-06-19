from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUCAO_PADRAO = "E01"


CASOS = {
    "V01": {
        "nome": "sql_injection",
        "owasp": "A05",
        "vuln": "SQLI",
        "arquivo": "V01_sql_injection.py",
        "teste": "test_V01_sql_injection.py",
        "contexto": "V01_sql_injection_contexto.md",
    },
    "V02": {
        "nome": "sql_injection_complexa",
        "owasp": "A05",
        "vuln": "SQLI",
        "arquivo": "V02_sql_injection_complexa.py",
        "teste": "test_V02_sql_injection_complexa.py",
        "contexto": "V02_sql_injection_complexa_contexto.md",
    },
    "V03": {
        "nome": "idor_bola",
        "owasp": "A01",
        "vuln": "IDOR",
        "arquivo": "V03_idor_bola.py",
        "teste": "test_V03_idor_bola.py",
        "contexto": "V03_idor_bola_contexto.md",
    },
}


PROMPTS = {
    "P1_simples": "P1",
    "P2_raciocinio_guiado": "P2",
    "P3_sast": "P3",
    "P4_contexto_sast": "P4",
}


CAMPOS_CSV_RESULTADOS = [
    "caso_id",
    "owasp",
    "vulnerabilidade",
    "prompt",
    "execucao",
    "issue_detectada_antes",
    "issue_sumiu",
    "testes_passaram",
    "novas_issues_introduzidas",
    "sem_novas_issues",
    "S_i",
    "T_i",
    "N_i",
    "correcao_adequada",
    "avaliacao_por_testes",
]


def gerar_nome_artefato(
    caso_id,
    owasp,
    vulnerabilidade,
    prompt_id,
    execucao,
    artefato,
    extensao,
):
    extensao = extensao.lstrip(".")

    return (
        f"{caso_id}_{owasp}_{vulnerabilidade}_{prompt_id}_"
        f"{execucao}_{artefato}.{extensao}"
    )


def obter_prompt_curto(prompt_id):
    return PROMPTS[prompt_id]


def obter_caminho_codigo_vulneravel(caso_id):
    return ROOT / "vulneraveis" / CASOS[caso_id]["arquivo"]


def obter_caminho_teste(caso_id):
    return ROOT / "testes" / CASOS[caso_id]["teste"]


def obter_caminho_contexto(caso_id):
    return ROOT / "contextos" / CASOS[caso_id]["contexto"]


def gerar_nome_artefato_caso(caso_id, prompt_id, execucao, artefato, extensao):
    caso = CASOS[caso_id]

    return gerar_nome_artefato(
        caso_id=caso_id,
        owasp=caso["owasp"],
        vulnerabilidade=caso["vuln"],
        prompt_id=prompt_id,
        execucao=execucao,
        artefato=artefato,
        extensao=extensao,
    )


def gerar_caminho_output(caso_id, prompt_id, execucao, artefato, extensao, pasta):
    nome_arquivo = gerar_nome_artefato_caso(
        caso_id=caso_id,
        prompt_id=prompt_id,
        execucao=execucao,
        artefato=artefato,
        extensao=extensao,
    )

    return ROOT / "outputs" / pasta / nome_arquivo
