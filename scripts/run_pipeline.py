import csv
import json
import re
from pathlib import Path

from openai_client import chamar_openai
from prompt_builder import (
    montar_prompt_simples,
    montar_prompt_raciocinio_guiado,
    montar_prompt_sast,
    montar_prompt_contexto_sast,
)
from bandit_client import (
    executar_bandit,
    contar_issues_bandit,
    simplificar_primeira_issue_bandit,
)
from run_tests import executar_testes_codigo, salvar_resultado_teste


ROOT = Path(__file__).resolve().parents[1]


CAMPOS_CSV_RESULTADOS = [
    "caso_id",
    "vulnerabilidade",
    "prompt",
    "issue_sumiu",
    "testes_passaram",
    "correcao_adequada",
]


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
        "nome": "sql_injection_complexa",
        "arquivo_codigo": ROOT / "vulneraveis" / "V02_sql_injection_complexa.py",
        "arquivo_contexto": ROOT / "contextos" / "V02_sql_injection_complexa_contexto.md",
        "module_name": "V02_sql_injection_complexa.py",
    },
    {
        "id": "V03",
        "nome": "idor_bola",
        "arquivo_codigo": ROOT / "vulneraveis" / "V03_idor_bola.py",
        "arquivo_contexto": ROOT / "contextos" / "V03_idor_bola_contexto.md",
        "module_name": "V03_idor_bola.py",
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
            "codigo_corrigido": ""
        }, False

    try:
        return json.loads(match.group(0)), True
    except json.JSONDecodeError:
        return {
            "erro_parse_json": True,
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


def salvar_codigo_corrigido(caso: dict, prompt_id: str, resposta_texto: str) -> Path:
    """
    Extrai o código corrigido da resposta da LLM e salva apenas o arquivo Python.
    """

    pasta_codigos = ROOT / "outputs" / "codigos_corrigidos"

    pasta_codigos.mkdir(parents=True, exist_ok=True)

    nome_base = f"{caso['id']}_{caso['nome']}_{prompt_id}"

    resposta_json, _ = extrair_json(resposta_texto)

    codigo_corrigido = limpar_codigo(resposta_json.get("codigo_corrigido", ""))

    codigo_path = pasta_codigos / f"{nome_base}.py"

    codigo_path.write_text(
        codigo_corrigido,
        encoding="utf-8"
    )

    return codigo_path


def salvar_csv_resultados(resultados: list[dict], output_path: Path) -> None:
    """
    Salva uma tabela resumida das execuções com as principais métricas booleanas.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=CAMPOS_CSV_RESULTADOS)
        writer.writeheader()

        for resultado in resultados:
            writer.writerow({
                campo: formatar_valor_csv(resultado.get(campo, ""))
                for campo in CAMPOS_CSV_RESULTADOS
            })


def formatar_valor_csv(valor):
    if isinstance(valor, bool):
        return str(valor).lower()

    return valor


def main():
    resultados = []

    for caso in CASOS:
        print(f"\n=== Analisando caso {caso['id']} - {caso['nome']} ===")

        contexto = caso["arquivo_contexto"].read_text(encoding="utf-8")
        codigo_vulneravel = caso["arquivo_codigo"].read_text(encoding="utf-8")

        bandit_antes_path = (
            ROOT
            / "outputs"
            / "bandit_antes"
            / f"{caso['id']}_{caso['nome']}.json"
        )

        print("Rodando Bandit antes da correção...")

        resultado_bandit_antes = executar_bandit(
            source_file=caso["arquivo_codigo"],
            output_path=bandit_antes_path
        )

        issue_sast = simplificar_primeira_issue_bandit(
            resultado_bandit=resultado_bandit_antes,
            arquivo=caso["module_name"]
        )

        qtd_antes = contar_issues_bandit(resultado_bandit_antes)

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

            codigo_corrigido_path = salvar_codigo_corrigido(
                caso=caso,
                prompt_id=prompt_id,
                resposta_texto=resposta_texto
            )

            bandit_depois_path = (
                ROOT
                / "outputs"
                / "bandit_depois"
                / f"{caso['id']}_{caso['nome']}_{prompt_id}.json"
            )

            print("Rodando Bandit depois da correção...")

            try:
                resultado_bandit_depois = executar_bandit(
                    source_file=codigo_corrigido_path,
                    output_path=bandit_depois_path
                )

                qtd_depois = contar_issues_bandit(resultado_bandit_depois)

            except Exception as erro:
                resultado_bandit_depois = {
                    "erro": str(erro),
                    "results": []
                }

                bandit_depois_path.parent.mkdir(parents=True, exist_ok=True)

                bandit_depois_path.write_text(
                    json.dumps(resultado_bandit_depois, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

                qtd_depois = -1

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
                "bandit_antes_qtd": qtd_antes,
                "bandit_depois_qtd": qtd_depois,
                "testes_detectaram_falha": testes_detectaram_falha,
                "issue_sumiu": issue_sumiu,
                "testes_passaram": testes_passaram,
                "correcao_adequada": correcao_adequada,
                "codigo_corrigido_path": str(codigo_corrigido_path),
                "bandit_antes_path": str(bandit_antes_path),
                "bandit_depois_path": str(bandit_depois_path),
                "teste_path": str(teste_path),
            })

            print(f"Correção adequada? {correcao_adequada}")

    resultados_path = ROOT / "outputs" / "resultados" / "execucoes.json"
    resultados_csv_path = ROOT / "outputs" / "resultados" / "execucoes.csv"

    resultados_path.parent.mkdir(parents=True, exist_ok=True)

    resultados_path.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    salvar_csv_resultados(resultados, resultados_csv_path)

    print(f"\nResultados salvos em: {resultados_path}")
    print(f"Resumo CSV salvo em: {resultados_csv_path}")


if __name__ == "__main__":
    main()
