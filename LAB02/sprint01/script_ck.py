import argparse
import csv
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


EXPECTED_OUTPUT_FILES = [
    "class.csv",
    "field.csv",
    "method.csv",
    "variable.csv",
]

SUMMARY_FILE_NAME = "ck_metrics_summary.csv"


def parse_arguments() -> argparse.Namespace:
    """Le os argumentos da linha de comando."""
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Executa a ferramenta CK em um repositorio Java local."
    )
    parser.add_argument(
        "repository",
        help="Caminho para o repositorio Java que sera analisado.",
    )
    parser.add_argument(
        "--ck-jar",
        default=str(script_dir / "ck-0.7.0-jar-with-dependencies.jar"),
        help="Caminho para o arquivo ck.jar.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(script_dir / "ck_output"),
        help="Diretorio onde os arquivos CSV gerados serao armazenados.",
    )
    return parser.parse_args()


def validate_paths(repository_path: Path, ck_jar_path: Path) -> None:
    """Valida se os caminhos obrigatorios existem."""
    if not ck_jar_path.is_file():
        raise FileNotFoundError(f"Arquivo CK nao encontrado em: {ck_jar_path}")

    if ck_jar_path.suffix.lower() != ".jar":
        raise ValueError(f"O arquivo informado para CK nao e um .jar: {ck_jar_path}")

    if not repository_path.exists():
        raise FileNotFoundError(
            f"Diretorio do repositorio nao encontrado em: {repository_path}"
        )

    if not repository_path.is_dir():
        raise NotADirectoryError(
            f"O caminho do repositorio nao e um diretorio: {repository_path}"
        )


def ensure_java_available() -> None:
    """Confirma se o Java esta disponivel no ambiente antes da execucao."""
    if shutil.which("java") is None:
        raise EnvironmentError(
            "Java nao encontrado no PATH. Instale o Java e tente novamente."
        )


def prepare_output_directory(output_dir: Path) -> None:
    """Cria a pasta de saida e remove CSVs antigos para evitar confusao."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for csv_file in output_dir.glob("*.csv"):
        csv_file.unlink()


def build_ck_command(ck_jar_path: Path, repository_path: Path) -> List[str]:
    """Monta o comando padrao para execucao do CK."""
    return [
        "java",
        "-jar",
        str(ck_jar_path),
        str(repository_path),
        "true",
        "0",
        "false",
    ]


def stream_process_output(process: subprocess.Popen) -> None:
    """Exibe em tempo real os logs produzidos pela ferramenta CK."""
    assert process.stdout is not None

    for line in process.stdout:
        print(line.rstrip())


def execute_ck(command: List[str], output_dir: Path) -> None:
    """Executa o CK via subprocess e envia os logs para o terminal."""
    print("Iniciando execucao da ferramenta CK...")
    print(f"Diretorio de saida: {output_dir}")
    print(f"Comando: {' '.join(command)}")

    process = subprocess.Popen(
        command,
        cwd=output_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    stream_process_output(process)
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(f"A execucao do CK falhou com codigo de saida {return_code}.")


def existing_output_files(output_dir: Path) -> List[Path]:
    """Retorna os arquivos CSV encontrados na pasta de saida."""
    return sorted(output_dir.glob("*.csv"))


def validate_generated_files(output_dir: Path) -> Iterable[Path]:
    """Garante que o CK gerou pelo menos o class.csv e lista os CSVs encontrados."""
    generated_files = existing_output_files(output_dir)
    if not generated_files:
        raise FileNotFoundError(
            f"Nenhum arquivo CSV foi gerado pelo CK em: {output_dir}"
        )

    class_csv = output_dir / "class.csv"
    if not class_csv.is_file():
        found_names = ", ".join(file.name for file in generated_files)
        raise FileNotFoundError(
            "O arquivo class.csv nao foi gerado. "
            f"Arquivos encontrados: {found_names}"
        )

    return generated_files


def find_metric_column(fieldnames: List[str], metric_name: str) -> str:
    """Localiza uma coluna do CSV ignorando diferencas de maiusculas/minusculas."""
    for fieldname in fieldnames:
        if fieldname.lower() == metric_name.lower():
            return fieldname

    raise ValueError(f"Coluna '{metric_name}' nao encontrada em class.csv.")


def read_metric_values(class_csv_path: Path, metric_name: str) -> List[float]:
    """Extrai os valores numericos de uma metrica no class.csv."""
    with class_csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        metric_column = find_metric_column(fieldnames, metric_name)

        values = []
        for row in reader:
            raw_value = (row.get(metric_column) or "").strip()
            if not raw_value:
                continue

            try:
                values.append(float(raw_value))
            except ValueError:
                continue

    if not values:
        raise ValueError(f"Nenhum valor numerico encontrado para a metrica {metric_name}.")

    return values


def summarize_metric(values: List[float]) -> dict:
    """Calcula estatisticas basicas para uma metrica da CK."""
    summary = {
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }

    if len(values) > 1:
        summary["stdev"] = round(statistics.stdev(values), 4)
    else:
        summary["stdev"] = 0.0

    return summary


def write_summary_csv(repository_path: Path, class_csv_path: Path, output_dir: Path) -> Path:
    """Gera um resumo por repositorio com CBO, DIT, LCOM e LOC a partir do class.csv."""
    cbo_values = read_metric_values(class_csv_path, "cbo")
    dit_values = read_metric_values(class_csv_path, "dit")
    lcom_values = read_metric_values(class_csv_path, "lcom")
    loc_values = read_metric_values(class_csv_path, "loc")

    cbo_summary = summarize_metric(cbo_values)
    dit_summary = summarize_metric(dit_values)
    lcom_summary = summarize_metric(lcom_values)
    loc_summary = summarize_metric(loc_values)

    summary_path = output_dir / SUMMARY_FILE_NAME
    with summary_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "repository_name",
                "class_count",
                "loc_total",
                "loc_mean",
                "loc_median",
                "loc_stdev",
                "cbo_mean",
                "cbo_median",
                "cbo_stdev",
                "cbo_min",
                "cbo_max",
                "dit_mean",
                "dit_median",
                "dit_stdev",
                "dit_min",
                "dit_max",
                "lcom_mean",
                "lcom_median",
                "lcom_stdev",
                "lcom_min",
                "lcom_max",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "repository_name": repository_path.name,
                "class_count": len(cbo_values),
                "loc_total": int(sum(loc_values)),
                "loc_mean": loc_summary["mean"],
                "loc_median": loc_summary["median"],
                "loc_stdev": loc_summary["stdev"],
                "cbo_mean": cbo_summary["mean"],
                "cbo_median": cbo_summary["median"],
                "cbo_stdev": cbo_summary["stdev"],
                "cbo_min": cbo_summary["min"],
                "cbo_max": cbo_summary["max"],
                "dit_mean": dit_summary["mean"],
                "dit_median": dit_summary["median"],
                "dit_stdev": dit_summary["stdev"],
                "dit_min": dit_summary["min"],
                "dit_max": dit_summary["max"],
                "lcom_mean": lcom_summary["mean"],
                "lcom_median": lcom_summary["median"],
                "lcom_stdev": lcom_summary["stdev"],
                "lcom_min": lcom_summary["min"],
                "lcom_max": lcom_summary["max"],
            }
        )

    return summary_path


def main() -> int:
    """Orquestra a validacao, execucao do CK e verificacao dos resultados."""
    args = parse_arguments()

    repository_path = Path(args.repository).expanduser().resolve()
    ck_jar_path = Path(args.ck_jar).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    validate_paths(repository_path, ck_jar_path)
    ensure_java_available()
    prepare_output_directory(output_dir)

    command = build_ck_command(ck_jar_path, repository_path)
    execute_ck(command, output_dir)
    generated_files = validate_generated_files(output_dir)

    class_csv_path = output_dir / "class.csv"
    summary_path = write_summary_csv(repository_path, class_csv_path, output_dir)

    print("Execucao concluida com sucesso.")
    print("Arquivos CSV gerados:")
    for file_path in generated_files:
        print(f"- {file_path}")
    print(f"Resumo das metricas CK: {summary_path}")

    missing_optional = [
        file_name
        for file_name in EXPECTED_OUTPUT_FILES
        if not (output_dir / file_name).exists()
    ]
    if missing_optional:
        print(
            "Aviso: alguns CSVs esperados nao foram encontrados: "
            + ", ".join(missing_optional)
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
