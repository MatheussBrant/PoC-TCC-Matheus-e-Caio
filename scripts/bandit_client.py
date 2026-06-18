import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


BANDIT_CMD = os.getenv("BANDIT_CMD", "bandit")


def executar_bandit(source_file: Path, output_path: Path) -> dict:
    """
    Executa o Bandit em um arquivo Python e salva o resultado em JSON.

    Observação:
    O Bandit retorna código 1 quando encontra issues.
    Portanto, returncode 1 não deve ser tratado como erro fatal.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    comando = [
        BANDIT_CMD,
        "-r",
        str(source_file),
        "-f",
        "json",
        "-o",
        str(output_path),
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    if resultado.returncode not in (0, 1):
        raise RuntimeError(
            "Erro ao executar Bandit.\n"
            f"Comando: {' '.join(comando)}\n\n"
            f"STDOUT:\n{resultado.stdout}\n\n"
            f"STDERR:\n{resultado.stderr}"
        )

    if not output_path.exists():
        return {
            "errors": [
                {
                    "message": "Arquivo de saída do Bandit não foi gerado.",
                    "stdout": resultado.stdout,
                    "stderr": resultado.stderr,
                }
            ],
            "results": []
        }

    try:
        return json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "errors": [
                {
                    "message": "Não foi possível ler o JSON gerado pelo Bandit.",
                    "stdout": resultado.stdout,
                    "stderr": resultado.stderr,
                }
            ],
            "results": []
        }


def contar_issues_bandit(resultado_bandit: dict) -> int:
    """
    Conta quantas issues o Bandit encontrou.
    """

    return len(resultado_bandit.get("results", []))


def simplificar_primeira_issue_bandit(resultado_bandit: dict, arquivo: str) -> dict:
    """
    Converte a primeira issue do Bandit em formato simples para usar nos prompts.
    """

    issues = resultado_bandit.get("results", [])

    if not issues:
        return {
            "tipo": "Não identificado",
            "severidade": "",
            "arquivo": arquivo,
            "linha": "",
            "mensagem": "Nenhuma vulnerabilidade retornada pelo Bandit.",
            "regra": ""
        }

    issue = issues[0]

    return {
        "tipo": issue.get("test_id", ""),
        "severidade": issue.get("issue_severity", ""),
        "arquivo": arquivo,
        "linha": issue.get("line_number", ""),
        "mensagem": issue.get("issue_text", ""),
        "regra": issue.get("test_name", "")
    }
