import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prompt_builder import montar_prompt_rag, montar_prompt_rag_raciocinio_guiado


ISSUE_SAST = {
    "tipo": "B608",
    "severidade": "MEDIUM",
    "arquivo": "app.py",
    "linha": 10,
    "mensagem": "Possible SQL injection vector.",
    "regra": "hardcoded_sql_expressions",
}


def test_prompt_p3_rag_inclui_contexto_e_sast():
    prompt = montar_prompt_rag(
        codigo="def exemplo(): pass",
        issue_sast=ISSUE_SAST,
        contexto="A consulta deve usar parametros.",
    )

    assert "Contexto recuperado por RAG" in prompt
    assert "A consulta deve usar parametros." in prompt
    assert "Achado SAST" in prompt
    assert "B608" in prompt
    assert "Possible SQL injection vector." in prompt
    assert "seguindo estas etapas" not in prompt


def test_prompt_p4_rag_raciocinio_guiado_inclui_contexto_sast_e_etapas():
    prompt = montar_prompt_rag_raciocinio_guiado(
        codigo="def exemplo(): pass",
        issue_sast=ISSUE_SAST,
        contexto="A consulta deve usar parametros.",
    )

    assert "Contexto recuperado por RAG" in prompt
    assert "A consulta deve usar parametros." in prompt
    assert "Achado SAST" in prompt
    assert "B608" in prompt
    assert "seguindo estas etapas" in prompt
    assert "1. Identifique a vulnerabilidade" in prompt
    assert '"causa": ""' in prompt
    assert '"impacto": ""' in prompt
