import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


SONAR_HOST_URL = os.getenv("SONAR_HOST_URL", "http://localhost:9000").rstrip("/")
SONAR_TOKEN = os.getenv("SONAR_TOKEN", "")
SONAR_SCANNER_CMD = os.getenv("SONAR_SCANNER_CMD", "sonar-scanner")


def _auth():
    """
    Retorna a autenticação usada nas chamadas HTTP para a API do SonarQube.
    """

    if not SONAR_TOKEN:
        raise RuntimeError("SONAR_TOKEN não configurado no arquivo .env")

    return (SONAR_TOKEN, "")


def preparar_workspace(source_file: Path, module_name: str, workspace: Path) -> None:
    """
    Cria uma pasta temporária de análise e copia o arquivo que será analisado pelo Sonar.
    """

    workspace.mkdir(parents=True, exist_ok=True)

    destino = workspace / module_name

    shutil.copy(source_file, destino)


def executar_sonar(project_key: str, source_dir: Path) -> None:
    """
    Executa o sonar-scanner dentro da pasta source_dir.
    """

    if not SONAR_TOKEN:
        raise RuntimeError("SONAR_TOKEN não configurado no arquivo .env")

    comando = [
        SONAR_SCANNER_CMD,
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.projectName={project_key}",
        "-Dsonar.sources=.",
        f"-Dsonar.host.url={SONAR_HOST_URL}",
        f"-Dsonar.token={SONAR_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
    ]

    resultado = subprocess.run(
        comando,
        cwd=source_dir,
        capture_output=True,
        text=True
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            "Erro ao executar sonar-scanner.\n"
            f"Comando: {' '.join(comando)}\n\n"
            f"STDOUT:\n{resultado.stdout}\n\n"
            f"STDERR:\n{resultado.stderr}"
        )


def aguardar_processamento(
    project_key: str,
    tentativas: int = 20,
    intervalo: int = 3
) -> None:
    """
    Aguarda o SonarQube processar a análise.

    Nesta PoC, a estratégia é simples:
    tenta consultar a API de issues algumas vezes até o projeto estar disponível.
    """

    for _ in range(tentativas):
        try:
            url = f"{SONAR_HOST_URL}/api/issues/search"

            params = {
                "componentKeys": project_key,
                "ps": 1
            }

            resposta = requests.get(
                url,
                params=params,
                auth=_auth(),
                timeout=15
            )

            if resposta.status_code == 200:
                return

        except requests.RequestException:
            pass

        time.sleep(intervalo)


def buscar_issues(project_key: str, tipos: str | None = None) -> dict:
    """
    Busca issues no SonarQube.
    """

    url = f"{SONAR_HOST_URL}/api/issues/search"

    params = {
        "componentKeys": project_key,
        "ps": 500
    }

    if tipos:
        params["types"] = tipos

    resposta = requests.get(
        url,
        params=params,
        auth=_auth(),
        timeout=30
    )

    resposta.raise_for_status()

    return resposta.json()


def buscar_vulnerabilidades(project_key: str) -> dict:
    """
    Busca somente issues classificadas como VULNERABILITY no SonarQube.
    """

    return buscar_issues(project_key, tipos="VULNERABILITY")


def buscar_hotspots(project_key: str) -> dict:
    """
    Busca Security Hotspots no SonarQube.

    Hotspots usam uma API diferente de issues. Se o token não tiver permissão,
    o erro é retornado no JSON para que a execução continue rastreável.
    """

    url = f"{SONAR_HOST_URL}/api/hotspots/search"

    params = {
        "projectKey": project_key,
        "ps": 500
    }

    resposta = requests.get(
        url,
        params=params,
        auth=_auth(),
        timeout=30
    )

    if resposta.status_code == 403:
        return {
            "erro": "Permissão insuficiente para consultar Security Hotspots.",
            "status_code": resposta.status_code,
            "hotspots": []
        }

    resposta.raise_for_status()

    return resposta.json()


def salvar_issues(project_key: str, output_path: Path) -> dict:
    """
    Busca as vulnerabilidades no SonarQube e salva o resultado em um arquivo JSON.
    """

    issues = buscar_vulnerabilidades(project_key)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(issues, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return issues


def salvar_analise_sast(project_key: str, output_path: Path) -> dict:
    """
    Salva um retrato da análise SAST com issues, vulnerabilidades e hotspots.
    """

    analise = {
        "project_key": project_key,
        "issues_todas": buscar_issues(project_key),
        "vulnerabilidades": buscar_vulnerabilidades(project_key),
        "hotspots": buscar_hotspots(project_key)
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(analise, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return analise


def simplificar_primeira_issue(issues: dict, arquivo: str) -> dict:
    """
    Converte a primeira issue retornada pelo SonarQube em um formato simples
    para ser usado nos prompts enviados à LLM.
    """

    lista = issues.get("issues", [])

    if not lista:
        return {
            "tipo": "Não identificado",
            "severidade": "",
            "arquivo": arquivo,
            "linha": "",
            "mensagem": "Nenhuma vulnerabilidade retornada pelo SonarQube.",
            "regra": ""
        }

    issue = lista[0]

    return {
        "tipo": issue.get("type", "VULNERABILITY"),
        "severidade": issue.get("severity", ""),
        "arquivo": arquivo,
        "linha": issue.get("line", ""),
        "mensagem": issue.get("message", ""),
        "regra": issue.get("rule", "")
    }


def contar_issues(issues: dict) -> int:
    """
    Conta quantas issues foram encontradas pelo SonarQube.
    """

    return len(issues.get("issues", []))


def contar_hotspots(hotspots: dict) -> int:
    """
    Conta quantos Security Hotspots foram encontrados pelo SonarQube.
    """

    return len(hotspots.get("hotspots", []))
