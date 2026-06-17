import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CASOS = {
    "V01": {
        "module_name": "V01_sql_injection.py",
        "test_file": ROOT / "testes" / "test_V01_sql_injection.py",
    },
    "V02": {
        "module_name": "V02_idor_bola.py",
        "test_file": ROOT / "testes" / "test_V02_idor_bola.py",
    },
}


def executar_testes_codigo(caso_id: str, codigo_corrigido: Path) -> dict:
    """
    Executa os testes do caso correspondente sobre um código corrigido.
    """

    caso = CASOS[caso_id]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        pacote_vulneraveis = tmp_path / "vulneraveis"
        pacote_testes = tmp_path / "testes"

        pacote_vulneraveis.mkdir()
        pacote_testes.mkdir()

        (pacote_vulneraveis / "__init__.py").write_text("", encoding="utf-8")

        modulo_destino = pacote_vulneraveis / caso["module_name"]
        teste_destino = pacote_testes / caso["test_file"].name

        shutil.copy(codigo_corrigido, modulo_destino)
        shutil.copy(caso["test_file"], teste_destino)

        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", str(teste_destino), "-q"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        return {
            "passou": resultado.returncode == 0,
            "returncode": resultado.returncode,
            "stdout": resultado.stdout,
            "stderr": resultado.stderr
        }


def salvar_resultado_teste(resultado: dict, output_path: Path) -> None:
    """
    Salva o resultado de uma execução de teste.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
