import json
import re
import tempfile
from pathlib import Path

from openai_client import chamar_openai
from prompt_builder import (
    montar_prompt_simples,
    montar_prompt_raciocinio_guiado,
    montar_prompt_sast,
    montar_prompt_contexto_sast,
)
from sonar_client import (
    preparar_workspace,
    executar_sonar,
    aguardar_processamento,
    salvar_analise_sast,
    simplificar_primeira_issue,
    contar_issues,
    contar_hotspots,
)
from run_tests import executar_testes_codigo, salvar_resultado_teste


ROOT = Path(__file__).resolve().parents[1]


CASOS = [
    {
        "id": "V01",
        "nome": "sql_injection",
        "arquivo_codigo": ROOT / "vulneraveis" / "V01_sql_injection.py",
        "arquivo_contexto": ROOT / "contextos" / "V01_sql_injection_contexto.md",
        "module_name": "V01_sql_injection.py",
    },
    {
        "id": "V02",
        "nome": "idor_bola",
        "arquivo_codigo": ROOT / "vulneraveis" / "V02_idor_bola.py",
        "arquivo_contexto": ROOT / "contextos" / "V02_idor_bola_contexto.md",
        "module_name": "V02_idor_bola.py",
    },
]


def extrair_json(texto: str) -> tuple[dict, bool]:
    """
    Tenta extrair JSON válido da resposta da LLM.
    """

    texto = texto.strip()

    try:
        return json.loads(texto), True
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", texto, re.DOTALL)

    if not match:
        return {
            "erro_parse_json": True,
            "resposta_bruta": texto,
            "codigo_corrigido": ""
        }, False

    try:
        return json.loads(match.group(0)), True
    except json.JSONDecodeError:
        return {
            "erro_parse_json": True,
            "resposta_bruta": texto,
            "codigo_corrigido": ""
        }, False


def limpar_codigo(codigo: str) -> str:
    """
    Remove cercas markdown se o modelo devolver código entre ```python ... ```.
    """

    codigo = codigo.strip()

    if codigo.startswith("```"):
        codigo = re.sub(r"^```python", "", codigo, flags=re.IGNORECASE).strip()
        codigo = re.sub(r"^```", "", codigo).strip()
        codigo = re.sub(r"```$", "", codigo).strip()

    return codigo


def salvar_resposta_e_codigo(caso: dict, prompt_id: str, resposta_texto: str) -> tuple[Path, Path, bool]:
    """
    Salva a resposta JSON da LLM e o código corrigido extraído dela.
    """

    pasta_respostas = ROOT / "outputs" / "respostas_llm"
    pasta_codigos = ROOT / "outputs" / "codigos_corrigidos"

    pasta_respostas.mkdir(parents=True, exist_ok=True)
    pasta_codigos.mkdir(parents=True, exist_ok=True)

    nome_base = f"{caso['id']}_{caso['nome']}_{prompt_id}"

    resposta_json, json_valido = extrair_json(resposta_texto)

    resposta_path = pasta_respostas / f"{nome_base}.json"

    resposta_path.write_text(
        json.dumps(resposta_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    codigo_corrigido = limpar_codigo(resposta_json.get("codigo_corrigido", ""))

    codigo_path = pasta_codigos / f"{nome_base}.py"

    codigo_path.write_text(
        codigo_corrigido,
        encoding="utf-8"
    )

    return resposta_path, codigo_path, json_valido


def analisar_com_sonar(project_key: str, source_file: Path, module_name: str, output_path: Path) -> dict:
    """
    Cria workspace temporário, executa Sonar e salva a análise SAST.
    """

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)

        preparar_workspace(
            source_file=source_file,
            module_name=module_name,
            workspace=workspace
        )

        executar_sonar(
            project_key=project_key,
            source_dir=workspace
        )

        aguardar_processamento(project_key)

        return salvar_analise_sast(
            project_key=project_key,
            output_path=output_path
        )


def main():
    resultados = []

    for caso in CASOS:
        print(f"\n=== Analisando caso {caso['id']} - {caso['nome']} ===")

        contexto = caso["arquivo_contexto"].read_text(encoding="utf-8")
        codigo_vulneravel = caso["arquivo_codigo"].read_text(encoding="utf-8")

        project_key_antes = f"POC_{caso['id']}_{caso['nome']}_ANTES"

        sonar_antes_path = (
            ROOT
            / "outputs"
            / "sonar_antes"
            / f"{caso['id']}_{caso['nome']}.json"
        )

        print("Rodando Sonar antes da correção...")

        analise_antes = analisar_com_sonar(
            project_key=project_key_antes,
            source_file=caso["arquivo_codigo"],
            module_name=caso["module_name"],
            output_path=sonar_antes_path
        )

        issue_sast = simplificar_primeira_issue(
            issues=analise_antes["vulnerabilidades"],
            arquivo=caso["module_name"]
        )

        qtd_antes = contar_issues(analise_antes["vulnerabilidades"])
        qtd_hotspots_antes = contar_hotspots(analise_antes["hotspots"])
        sast_detectou_vulnerabilidade = qtd_antes > 0
        sast_detectou_hotspot = qtd_hotspots_antes > 0

        teste_vulneravel_resultado = executar_testes_codigo(
            caso_id=caso["id"],
            codigo_corrigido=caso["arquivo_codigo"]
        )

        testes_detectaram_falha = not teste_vulneravel_resultado["passou"]

        prompts = {
            "P1_simples": montar_prompt_simples(codigo_vulneravel),
            "P2_raciocinio_guiado": montar_prompt_raciocinio_guiado(codigo_vulneravel),
            "P3_sast": montar_prompt_sast(codigo_vulneravel, issue_sast),
            "P4_contexto_sast": montar_prompt_contexto_sast(codigo_vulneravel, issue_sast, contexto),
        }

        for prompt_id, prompt in prompts.items():
            print(f"\nExecutando {caso['id']} - {prompt_id}")

            resposta_texto = chamar_openai(prompt)

            resposta_path, codigo_corrigido_path, json_valido = salvar_resposta_e_codigo(
                caso=caso,
                prompt_id=prompt_id,
                resposta_texto=resposta_texto
            )

            project_key_depois = f"POC_{caso['id']}_{caso['nome']}_{prompt_id}_DEPOIS"

            sonar_depois_path = (
                ROOT
                / "outputs"
                / "sonar_depois"
                / f"{caso['id']}_{caso['nome']}_{prompt_id}.json"
            )

            print("Rodando Sonar depois da correção...")

            try:
                analise_depois = analisar_com_sonar(
                    project_key=project_key_depois,
                    source_file=codigo_corrigido_path,
                    module_name=caso["module_name"],
                    output_path=sonar_depois_path
                )

                qtd_depois = contar_issues(analise_depois["vulnerabilidades"])
                qtd_hotspots_depois = contar_hotspots(analise_depois["hotspots"])

            except Exception as erro:
                analise_depois = {
                    "erro": str(erro),
                    "issues_todas": {"issues": []},
                    "vulnerabilidades": {"issues": []},
                    "hotspots": {"hotspots": []}
                }

                sonar_depois_path.parent.mkdir(parents=True, exist_ok=True)

                sonar_depois_path.write_text(
                    json.dumps(analise_depois, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

                qtd_depois = -1
                qtd_hotspots_depois = -1

            print("Executando testes automatizados...")

            teste_resultado = executar_testes_codigo(
                caso_id=caso["id"],
                codigo_corrigido=codigo_corrigido_path
            )

            teste_path = (
                ROOT
                / "outputs"
                / "testes"
                / f"{caso['id']}_{caso['nome']}_{prompt_id}_testes.json"
            )

            salvar_resultado_teste(
                resultado=teste_resultado,
                output_path=teste_path
            )

            issue_sumiu = qtd_antes > 0 and qtd_depois == 0
            testes_passaram = teste_resultado["passou"]
            correcao_adequada = issue_sumiu and testes_passaram

            resultados.append({
                "caso_id": caso["id"],
                "vulnerabilidade": caso["nome"],
                "prompt": prompt_id,
                "sonar_antes_qtd": qtd_antes,
                "sonar_depois_qtd": qtd_depois,
                "sonar_hotspots_antes_qtd": qtd_hotspots_antes,
                "sonar_hotspots_depois_qtd": qtd_hotspots_depois,
                "sast_detectou_vulnerabilidade": sast_detectou_vulnerabilidade,
                "sast_detectou_hotspot": sast_detectou_hotspot,
                "testes_detectaram_falha": testes_detectaram_falha,
                "issue_sumiu": issue_sumiu,
                "testes_passaram": testes_passaram,
                "correcao_adequada": correcao_adequada,
                "resposta_json_valida": json_valido,
                "resposta_path": str(resposta_path),
                "codigo_corrigido_path": str(codigo_corrigido_path),
                "sonar_antes_path": str(sonar_antes_path),
                "sonar_depois_path": str(sonar_depois_path),
                "teste_path": str(teste_path),
            })

            print(f"Correção adequada? {correcao_adequada}")

    resultados_path = ROOT / "outputs" / "resultados" / "execucoes.json"

    resultados_path.parent.mkdir(parents=True, exist_ok=True)

    resultados_path.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\nResultados salvos em: {resultados_path}")


if __name__ == "__main__":
    main()
