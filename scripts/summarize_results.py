from pathlib import Path

from calculate_metrics import gerar_arquivos_metricas

ROOT = Path(__file__).resolve().parents[1]


def gerar_resumo():
    """
    Gera CSVs e métricas a partir do arquivo outputs/resultados/execucoes.json.
    """

    resultados_path = ROOT / "outputs" / "resultados" / "execucoes.json"

    if not resultados_path.exists():
        raise FileNotFoundError(
            "Arquivo outputs/resultados/execucoes.json não encontrado. "
            "Execute primeiro: python scripts/run_pipeline.py"
        )

    gerar_arquivos_metricas(resultados_path=resultados_path)

    print(f"Resumo e métricas salvos em: {ROOT / 'outputs' / 'resultados'}")


if __name__ == "__main__":
    gerar_resumo()
