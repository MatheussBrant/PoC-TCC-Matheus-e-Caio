import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def gerar_resumo():
    """
    Gera um CSV final a partir do arquivo outputs/resultados/execucoes.json.
    """

    resultados_path = ROOT / "outputs" / "resultados" / "execucoes.json"
    csv_path = ROOT / "outputs" / "resultados" / "resultado_final.csv"

    if not resultados_path.exists():
        raise FileNotFoundError(
            "Arquivo outputs/resultados/execucoes.json não encontrado. "
            "Execute primeiro: python scripts/run_pipeline.py"
        )

    dados = json.loads(resultados_path.read_text(encoding="utf-8"))

    campos = [
        "caso_id",
        "vulnerabilidade",
        "prompt",
        "sonar_antes_qtd",
        "sonar_depois_qtd",
        "sonar_hotspots_antes_qtd",
        "sonar_hotspots_depois_qtd",
        "sast_detectou_vulnerabilidade",
        "sast_detectou_hotspot",
        "testes_detectaram_falha",
        "issue_sumiu",
        "testes_passaram",
        "correcao_adequada",
        "resposta_json_valida",
        "codigo_corrigido_path"
    ]

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=campos)
        writer.writeheader()

        for item in dados:
            writer.writerow({campo: item.get(campo, "") for campo in campos})

    print(f"Resumo CSV salvo em: {csv_path}")


if __name__ == "__main__":
    gerar_resumo()
