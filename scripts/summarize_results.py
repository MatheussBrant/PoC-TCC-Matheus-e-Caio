import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CAMPOS_CSV_RESULTADOS = [
    "caso_id",
    "vulnerabilidade",
    "prompt",
    "issue_sumiu",
    "testes_passaram",
    "correcao_adequada",
]


def formatar_valor_csv(valor):
    if isinstance(valor, bool):
        return str(valor).lower()

    return valor


def gerar_resumo():
    """
    Gera um CSV resumido a partir do arquivo outputs/resultados/execucoes.json.
    """

    resultados_path = ROOT / "outputs" / "resultados" / "execucoes.json"
    csv_path = ROOT / "outputs" / "resultados" / "execucoes.csv"

    if not resultados_path.exists():
        raise FileNotFoundError(
            "Arquivo outputs/resultados/execucoes.json não encontrado. "
            "Execute primeiro: python scripts/run_pipeline.py"
        )

    dados = json.loads(resultados_path.read_text(encoding="utf-8"))

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=CAMPOS_CSV_RESULTADOS)
        writer.writeheader()

        for item in dados:
            writer.writerow({
                campo: formatar_valor_csv(item.get(campo, ""))
                for campo in CAMPOS_CSV_RESULTADOS
            })

    print(f"Resumo CSV salvo em: {csv_path}")


if __name__ == "__main__":
    gerar_resumo()
