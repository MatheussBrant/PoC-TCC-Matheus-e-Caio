import csv
import json
from collections import defaultdict
from pathlib import Path

from artifact_naming import CAMPOS_CSV_RESULTADOS, ROOT


CAMPOS_ASSINATURA_ISSUE = (
    "test_id",
    "issue_text",
    "issue_severity",
    "issue_confidence",
)

CAMPOS_METRICAS_GERAIS = [
    "total_tentativas",
    "trv",
    "tri",
    "tpf",
    "tnini",
    "tff",
    "correcoes_adequadas",
]

CAMPOS_METRICAS_POR_PROMPT = [
    "prompt",
    *CAMPOS_METRICAS_GERAIS,
]

CAMPOS_METRICAS_POR_CASO = [
    "caso_id",
    "owasp",
    "vulnerabilidade",
    *CAMPOS_METRICAS_GERAIS,
]


def formatar_valor_csv(valor):
    if isinstance(valor, bool):
        return str(valor).lower()

    return valor


def normalizar_caminho(caminho):
    if not caminho:
        return None

    path = Path(caminho)

    if path.is_absolute():
        return path

    return ROOT / path


def ler_json_seguro(caminho):
    path = normalizar_caminho(caminho)

    if path is None:
        return None, ["Caminho de arquivo não informado."]

    if not path.exists():
        return None, [f"Arquivo ausente: {path}"]

    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as erro:
        return None, [f"JSON inválido em {path}: {erro}"]
    except OSError as erro:
        return None, [f"Erro ao ler {path}: {erro}"]


def assinatura_issue(issue):
    return tuple(
        str(issue.get(campo, "")).strip()
        for campo in CAMPOS_ASSINATURA_ISSUE
    )


def extrair_assinaturas_bandit(caminho):
    dados, erros = ler_json_seguro(caminho)

    if dados is None:
        return set(), 0, erros

    if not isinstance(dados, dict):
        return set(), 0, [f"Relatório Bandit inválido em {caminho}: raiz não é objeto JSON."]

    erro_execucao = dados.get("erro")

    if erro_execucao:
        return set(), 0, [f"Erro registrado no relatório Bandit {caminho}: {erro_execucao}"]

    resultados = dados.get("results", [])

    if not isinstance(resultados, list):
        return set(), 0, [f"Relatório Bandit inválido em {caminho}: campo 'results' não é lista."]

    erros_bandit = dados.get("errors") or []

    if erros_bandit and not resultados:
        return set(), 0, [f"Relatório Bandit {caminho} contém erros e nenhum resultado analisável."]

    assinaturas = {
        assinatura_issue(issue)
        for issue in resultados
        if isinstance(issue, dict)
    }

    return assinaturas, len(resultados), []


def ler_resultado_testes(caminho, valor_fallback=None):
    dados, erros = ler_json_seguro(caminho)

    if dados is None:
        return bool(valor_fallback), erros

    if not isinstance(dados, dict):
        return bool(valor_fallback), [f"Resultado de testes inválido em {caminho}: raiz não é objeto JSON."]

    if "passou" not in dados:
        return bool(valor_fallback), [f"Resultado de testes {caminho} não contém o campo 'passou'."]

    return bool(dados.get("passou")), []


def avaliar_tentativa(tentativa):
    resultado = dict(tentativa)
    resultado.pop("arquivo_resultado", None)

    arquivo_sast_antes = (
        resultado.get("arquivo_sast_antes")
        or resultado.get("bandit_antes_path")
    )
    arquivo_sast_depois = (
        resultado.get("arquivo_sast_depois")
        or resultado.get("bandit_depois_path")
    )
    arquivo_testes = (
        resultado.get("arquivo_testes")
        or resultado.get("teste_path")
    )
    arquivo_codigo_corrigido = (
        resultado.get("arquivo_codigo_corrigido")
        or resultado.get("codigo_corrigido_path")
    )

    antes_assinaturas, antes_qtd, erros_antes = extrair_assinaturas_bandit(arquivo_sast_antes)
    depois_assinaturas, depois_qtd, erros_depois = extrair_assinaturas_bandit(arquivo_sast_depois)
    testes_passaram, erros_testes = ler_resultado_testes(
        arquivo_testes,
        valor_fallback=resultado.get("testes_passaram"),
    )

    bandit_valido = not erros_antes and not erros_depois
    issue_detectada_antes = antes_qtd > 0 and not erros_antes
    issues_originais_restantes = antes_assinaturas & depois_assinaturas
    novas_issues = depois_assinaturas - antes_assinaturas if bandit_valido else set()

    issue_sumiu = (
        issue_detectada_antes
        and not erros_depois
        and not issues_originais_restantes
    )
    novas_issues_introduzidas = bool(novas_issues)
    sem_novas_issues = bandit_valido and not novas_issues_introduzidas
    criterio_issue_atendido = (
        issue_sumiu
        or (bandit_valido and not issue_detectada_antes)
    )

    s_i = int(issue_sumiu)
    t_i = int(testes_passaram)
    n_i = int(sem_novas_issues)
    correcao_adequada = bool(criterio_issue_atendido and t_i and n_i)

    resultado.update({
        "arquivo_sast_antes": str(arquivo_sast_antes or ""),
        "arquivo_sast_depois": str(arquivo_sast_depois or ""),
        "arquivo_testes": str(arquivo_testes or ""),
        "arquivo_codigo_corrigido": str(arquivo_codigo_corrigido or ""),
        "bandit_antes_qtd": antes_qtd,
        "bandit_depois_qtd": depois_qtd,
        "issue_detectada_antes": issue_detectada_antes,
        "issue_sumiu": issue_sumiu,
        "testes_passaram": testes_passaram,
        "novas_issues_introduzidas": novas_issues_introduzidas,
        "novas_issues_qtd": len(novas_issues),
        "sem_novas_issues": sem_novas_issues,
        "S_i": s_i,
        "T_i": t_i,
        "N_i": n_i,
        "correcao_adequada": correcao_adequada,
        "avaliacao_por_testes": testes_passaram,
    })

    erros_metricas = erros_antes + erros_depois + erros_testes

    if erros_metricas:
        resultado["erros_metricas"] = erros_metricas
    else:
        resultado.pop("erros_metricas", None)

    return resultado


def tentativa_tem_correcao_adequada(tentativa):
    if "correcao_adequada" in tentativa:
        return bool(tentativa.get("correcao_adequada"))

    return bool(
        int(tentativa.get("S_i", 0))
        and int(tentativa.get("T_i", 0))
        and int(tentativa.get("N_i", 0))
    )


def calcular_metricas_agregadas(tentativas):
    total = len(tentativas)

    if total == 0:
        return {
            "total_tentativas": 0,
            "trv": 0.0,
            "tri": 0.0,
            "tpf": 0.0,
            "tnini": 0.0,
            "tff": 0.0,
            "correcoes_adequadas": 0,
        }

    soma_s = sum(int(item.get("S_i", 0)) for item in tentativas)
    soma_t = sum(int(item.get("T_i", 0)) for item in tentativas)
    soma_n = sum(int(item.get("N_i", 0)) for item in tentativas)
    correcoes_adequadas = sum(
        int(tentativa_tem_correcao_adequada(item))
        for item in tentativas
    )
    tpf = soma_t / total

    return {
        "total_tentativas": total,
        "trv": round(correcoes_adequadas / total, 4),
        "tri": round(soma_s / total, 4),
        "tpf": round(tpf, 4),
        "tnini": round(soma_n / total, 4),
        "tff": round(1 - tpf, 4),
        "correcoes_adequadas": correcoes_adequadas,
    }


def agrupar_metricas(tentativas, campos_chave):
    grupos = defaultdict(list)

    for tentativa in tentativas:
        chave = tuple(tentativa.get(campo, "") for campo in campos_chave)
        grupos[chave].append(tentativa)

    linhas = []

    for chave, itens in sorted(grupos.items()):
        linha = {
            campo: valor
            for campo, valor in zip(campos_chave, chave)
        }
        linha.update(calcular_metricas_agregadas(itens))
        linhas.append(linha)

    return linhas


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def salvar_csv(caminho, linhas, campos):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()

        for linha in linhas:
            writer.writerow({
                campo: formatar_valor_csv(linha.get(campo, ""))
                for campo in campos
            })


def gerar_arquivos_metricas(resultados_path=None, output_dir=None):
    resultados_path = normalizar_caminho(
        resultados_path or ROOT / "outputs" / "resultados" / "execucoes.json"
    )
    output_dir = normalizar_caminho(
        output_dir or ROOT / "outputs" / "resultados"
    )

    dados, erros = ler_json_seguro(resultados_path)

    if erros:
        raise FileNotFoundError("; ".join(erros))

    if not isinstance(dados, list):
        raise ValueError(f"Arquivo {resultados_path} deve conter uma lista de execuções.")

    tentativas = [
        avaliar_tentativa(item)
        for item in dados
    ]

    metricas = calcular_metricas_agregadas(tentativas)
    metricas_por_prompt = agrupar_metricas(tentativas, ["prompt"])
    metricas_por_caso = agrupar_metricas(tentativas, ["caso_id", "owasp", "vulnerabilidade"])

    salvar_json(output_dir / "execucoes.json", tentativas)
    salvar_csv(output_dir / "execucoes.csv", tentativas, CAMPOS_CSV_RESULTADOS)
    salvar_json(output_dir / "metricas.json", metricas)
    salvar_csv(output_dir / "metricas.csv", [metricas], CAMPOS_METRICAS_GERAIS)
    salvar_csv(output_dir / "metricas_por_prompt.csv", metricas_por_prompt, CAMPOS_METRICAS_POR_PROMPT)
    salvar_csv(output_dir / "metricas_por_caso.csv", metricas_por_caso, CAMPOS_METRICAS_POR_CASO)

    imprimir_resumo_metricas(metricas)

    return {
        "execucoes": tentativas,
        "metricas": metricas,
        "metricas_por_prompt": metricas_por_prompt,
        "metricas_por_caso": metricas_por_caso,
    }


def imprimir_resumo_metricas(metricas):
    print(
        "Métricas gerais: "
        f"TRV={metricas['trv']}, "
        f"TRI={metricas['tri']}, "
        f"TPF={metricas['tpf']}, "
        f"TNINI={metricas['tnini']}, "
        f"TFF={metricas['tff']}"
    )


if __name__ == "__main__":
    gerar_arquivos_metricas()
