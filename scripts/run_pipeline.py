import json
import re

from artifact_naming import (
    CASOS,
    EXECUCAO_PADRAO,
    ROOT,
    gerar_caminho_output,
    obter_caminho_codigo_vulneravel,
    obter_caminho_contexto,
    obter_prompt_curto,
)
from openai_client import chamar_openai
from prompt_builder import (
    montar_prompt_simples,
    montar_prompt_raciocinio_guiado,
    montar_prompt_rag,
    montar_prompt_rag_raciocinio_guiado,
)
from bandit_client import (
    executar_bandit,
    contar_issues_bandit,
    simplificar_primeira_issue_bandit,
)
from calculate_metrics import avaliar_tentativa, gerar_arquivos_metricas
from run_tests import executar_testes_codigo, salvar_resultado_teste


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


def salvar_codigo_corrigido(
    caso_id: str,
    prompt_id: str,
    execucao: str,
    resposta_texto: str,
):
    """
    Extrai o código corrigido da resposta da LLM e salva apenas o arquivo Python.
    """

    resposta_json, _ = extrair_json(resposta_texto)

    codigo_corrigido = limpar_codigo(resposta_json.get("codigo_corrigido", ""))

    codigo_path = gerar_caminho_output(
        caso_id=caso_id,
        prompt_id=prompt_id,
        execucao=execucao,
        artefato="codigo",
        extensao="py",
        pasta="codigos_corrigidos",
    )

    codigo_path.parent.mkdir(parents=True, exist_ok=True)

    codigo_path.write_text(
        codigo_corrigido,
        encoding="utf-8"
    )

    return codigo_path


def main():
    resultados = []
    execucao = EXECUCAO_PADRAO

    for caso_id, caso in CASOS.items():
        print(f"\n=== Analisando caso {caso_id} - {caso['nome']} ===")

        arquivo_codigo = obter_caminho_codigo_vulneravel(caso_id)
        arquivo_contexto = obter_caminho_contexto(caso_id)

        contexto = arquivo_contexto.read_text(encoding="utf-8")
        codigo_vulneravel = arquivo_codigo.read_text(encoding="utf-8")

        bandit_antes_path = gerar_caminho_output(
            caso_id=caso_id,
            prompt_id="BASE",
            execucao=execucao,
            artefato="sast_antes",
            extensao="json",
            pasta="bandit_antes",
        )

        print("Rodando Bandit antes da correção...")

        resultado_bandit_antes = executar_bandit(
            source_file=arquivo_codigo,
            output_path=bandit_antes_path
        )

        issue_sast = simplificar_primeira_issue_bandit(
            resultado_bandit=resultado_bandit_antes,
            arquivo=caso["arquivo"]
        )

        qtd_antes = contar_issues_bandit(resultado_bandit_antes)

        teste_vulneravel_resultado = executar_testes_codigo(
            caso_id=caso_id,
            codigo_corrigido=arquivo_codigo
        )

        testes_detectaram_falha = not teste_vulneravel_resultado["passou"]

        prompts = {
            "P1_simples": montar_prompt_simples(codigo_vulneravel),
            "P2_raciocinio_guiado": montar_prompt_raciocinio_guiado(codigo_vulneravel),
            "P3_rag": montar_prompt_rag(codigo_vulneravel, issue_sast, contexto),
            "P4_rag_raciocinio_guiado": montar_prompt_rag_raciocinio_guiado(
                codigo_vulneravel,
                issue_sast,
                contexto,
            ),
        }

        for prompt_original, prompt in prompts.items():
            prompt_id = obter_prompt_curto(prompt_original)

            print(f"\nExecutando {caso_id} - {prompt_id} ({prompt_original})")

            resposta_texto = chamar_openai(prompt)

            codigo_corrigido_path = salvar_codigo_corrigido(
                caso_id=caso_id,
                prompt_id=prompt_id,
                execucao=execucao,
                resposta_texto=resposta_texto
            )

            bandit_depois_path = gerar_caminho_output(
                caso_id=caso_id,
                prompt_id=prompt_id,
                execucao=execucao,
                artefato="sast_depois",
                extensao="json",
                pasta="bandit_depois",
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
                caso_id=caso_id,
                codigo_corrigido=codigo_corrigido_path
            )

            teste_path = gerar_caminho_output(
                caso_id=caso_id,
                prompt_id=prompt_id,
                execucao=execucao,
                artefato="testes",
                extensao="json",
                pasta="testes",
            )

            salvar_resultado_teste(
                resultado=teste_resultado,
                output_path=teste_path
            )

            resultado = {
                "caso_id": caso_id,
                "nome_caso": caso["nome"],
                "owasp": caso["owasp"],
                "vulnerabilidade": caso["vuln"],
                "prompt": prompt_id,
                "prompt_original": prompt_original,
                "execucao": execucao,
                "bandit_antes_qtd": qtd_antes,
                "bandit_depois_qtd": qtd_depois,
                "testes_detectaram_falha": testes_detectaram_falha,
                "arquivo_codigo_corrigido": str(codigo_corrigido_path),
                "arquivo_sast_antes": str(bandit_antes_path),
                "arquivo_sast_depois": str(bandit_depois_path),
                "arquivo_testes": str(teste_path),
            }

            resultado = avaliar_tentativa(resultado)

            resultados.append(resultado)

            print(f"Correção adequada? {resultado['correcao_adequada']}")

    resultados_path = ROOT / "outputs" / "resultados" / "execucoes.json"
    resultados_path.parent.mkdir(parents=True, exist_ok=True)

    resultados_path.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    gerar_arquivos_metricas(resultados_path=resultados_path)

    print(f"\nResultados salvos em: {resultados_path}")
    print(f"Resumo CSV salvo em: {ROOT / 'outputs' / 'resultados' / 'execucoes.csv'}")


if __name__ == "__main__":
    main()
