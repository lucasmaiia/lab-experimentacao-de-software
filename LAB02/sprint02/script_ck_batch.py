import argparse
import csv
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


DEFAULT_REPOS_DIR = "repos_clonados"
DEFAULT_OUTPUT_ROOT = "ck_batch_output"
DEFAULT_STATUS_FILE = "ck_batch_status.csv"
DEFAULT_SUMMARY_FILE = "ck_batch_summary.csv"
PER_REPOSITORY_SUMMARY_FILE = "ck_metrics_summary.csv"


def parse_arguments() -> argparse.Namespace:
    """Le os argumentos da linha de comando."""
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Executa a CK em lote para todos os repositorios clonados."
    )
    parser.add_argument(
        "--repos-dir",
        default=str(script_dir / DEFAULT_REPOS_DIR),
        help="Diretorio que contem os repositorios clonados.",
    )
    parser.add_argument(
        "--ck-jar",
        default=str(script_dir / "ck-0.7.0-jar-with-dependencies.jar"),
        help="Caminho para o arquivo ck.jar.",
    )
    parser.add_argument(
        "--output-root",
        default=str(script_dir / DEFAULT_OUTPUT_ROOT),
        help="Diretorio raiz onde os resultados da CK serao salvos.",
    )
    parser.add_argument(
        "--status-file",
        default=str(script_dir / DEFAULT_STATUS_FILE),
        help="Arquivo CSV de status incremental da execucao em lote.",
    )
    parser.add_argument(
        "--summary-file",
        default=str(script_dir / DEFAULT_SUMMARY_FILE),
        help="Arquivo CSV consolidado com o resumo das metricas da CK.",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=None,
        help="Limita a quantidade de repositorios processados.",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Processa novamente repositorios que ja constam como concluidos no status.",
    )
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Valida argumentos numericos do script."""
    if args.max_repos is not None and args.max_repos <= 0:
        raise ValueError("O valor de --max-repos deve ser maior que zero.")


def validate_paths(repos_dir: Path, ck_jar_path: Path, script_ck_path: Path) -> None:
    """Valida se os caminhos necessarios existem."""
    if not repos_dir.is_dir():
        raise FileNotFoundError(
            f"Diretorio de repositorios clonados nao encontrado em: {repos_dir}"
        )

    if not ck_jar_path.is_file():
        raise FileNotFoundError(f"Arquivo CK nao encontrado em: {ck_jar_path}")

    if not script_ck_path.is_file():
        raise FileNotFoundError(f"Script individual CK nao encontrado em: {script_ck_path}")


def discover_repositories(repos_dir: Path) -> List[Path]:
    """Localiza repositorios git clonados procurando a pasta .git."""
    repositories = sorted(git_dir.parent for git_dir in repos_dir.rglob(".git"))
    if not repositories:
        raise ValueError(f"Nenhum repositorio git encontrado em: {repos_dir}")
    return repositories


def initialize_csv(csv_path: Path, fieldnames: List[str]) -> None:
    """Cria um CSV com cabecalho caso ele ainda nao exista."""
    if csv_path.exists():
        return

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()


def append_csv_row(csv_path: Path, fieldnames: List[str], row: Dict[str, str]) -> None:
    """Adiciona uma linha ao CSV incremental."""
    with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(row)


def load_completed_repositories(status_file: Path) -> set[str]:
    """Le o CSV de status para retomar apenas repositorios pendentes."""
    if not status_file.is_file():
        return set()

    completed = set()
    with status_file.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("status") == "concluido":
                completed.add((row.get("repository_path") or "").strip())
    return completed


def repository_output_dir(output_root: Path, repos_dir: Path, repository_path: Path) -> Path:
    """Monta o diretorio de saida da CK para um repositorio especifico."""
    relative_parts = repository_path.relative_to(repos_dir).parts
    normalized_name = "__".join(relative_parts)
    return output_root / normalized_name


def stream_process_output(process: subprocess.Popen) -> None:
    """Exibe em tempo real os logs do script CK individual."""
    assert process.stdout is not None
    for line in process.stdout:
        print(line.rstrip())


def run_ck_for_repository(
    python_executable: str,
    script_ck_path: Path,
    repository_path: Path,
    ck_jar_path: Path,
    output_dir: Path,
) -> None:
    """Executa o script_ck.py individual para um repositório."""
    command = [
        python_executable,
        str(script_ck_path),
        str(repository_path),
        "--ck-jar",
        str(ck_jar_path),
        "--output-dir",
        str(output_dir),
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    stream_process_output(process)
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(
            f"Falha ao executar a CK para {repository_path}. Codigo de saida: {return_code}"
        )


def read_summary_row(summary_path: Path) -> Dict[str, str]:
    """Carrega a unica linha do resumo gerado pelo script CK individual."""
    if not summary_path.is_file():
        raise FileNotFoundError(f"Resumo CK nao encontrado em: {summary_path}")

    with summary_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    if not rows:
        raise ValueError(f"O resumo CK esta vazio em: {summary_path}")

    return rows[0]


def main() -> int:
    """Executa a CK em lote sobre todos os repositorios clonados."""
    args = parse_arguments()
    validate_arguments(args)

    script_dir = Path(__file__).resolve().parent
    repos_dir = Path(args.repos_dir).expanduser().resolve()
    ck_jar_path = Path(args.ck_jar).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    status_file = Path(args.status_file).expanduser().resolve()
    summary_file = Path(args.summary_file).expanduser().resolve()
    script_ck_path = script_dir / "script_ck.py"

    validate_paths(repos_dir, ck_jar_path, script_ck_path)
    repositories = discover_repositories(repos_dir)

    if args.max_repos is not None:
        repositories = repositories[: args.max_repos]

    status_fieldnames = [
        "repository_name",
        "repository_path",
        "output_dir",
        "status",
        "message",
    ]
    summary_fieldnames = [
        "repository_name",
        "repository_path",
        "output_dir",
        "class_count",
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
    ]

    initialize_csv(status_file, status_fieldnames)
    initialize_csv(summary_file, summary_fieldnames)
    completed_repositories = set() if args.rerun else load_completed_repositories(status_file)

    print(f"Repositorio(s) encontrados para processamento: {len(repositories)}")
    print(f"Diretorio dos clones: {repos_dir}")
    print(f"Diretorio de saida da CK em lote: {output_root}")
    print(f"Arquivo de status: {status_file}")
    print(f"Arquivo de resumo consolidado: {summary_file}")

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for index, repository_path in enumerate(repositories, start=1):
        repository_key = str(repository_path)
        repository_name = str(repository_path.relative_to(repos_dir))
        output_dir = repository_output_dir(output_root, repos_dir, repository_path)

        if repository_key in completed_repositories:
            skipped_count += 1
            print(f"[{index}/{len(repositories)}] Pulando {repository_name} (ja concluido).")
            continue

        print(f"[{index}/{len(repositories)}] Executando CK em {repository_name}...")

        try:
            run_ck_for_repository(
                sys.executable,
                script_ck_path,
                repository_path,
                ck_jar_path,
                output_dir,
            )

            summary_row = read_summary_row(output_dir / PER_REPOSITORY_SUMMARY_FILE)
            consolidated_row = {
                "repository_name": summary_row["repository_name"],
                "repository_path": repository_key,
                "output_dir": str(output_dir),
                "class_count": summary_row["class_count"],
                "cbo_mean": summary_row["cbo_mean"],
                "cbo_median": summary_row["cbo_median"],
                "cbo_stdev": summary_row["cbo_stdev"],
                "cbo_min": summary_row["cbo_min"],
                "cbo_max": summary_row["cbo_max"],
                "dit_mean": summary_row["dit_mean"],
                "dit_median": summary_row["dit_median"],
                "dit_stdev": summary_row["dit_stdev"],
                "dit_min": summary_row["dit_min"],
                "dit_max": summary_row["dit_max"],
                "lcom_mean": summary_row["lcom_mean"],
                "lcom_median": summary_row["lcom_median"],
                "lcom_stdev": summary_row["lcom_stdev"],
                "lcom_min": summary_row["lcom_min"],
                "lcom_max": summary_row["lcom_max"],
            }
            append_csv_row(summary_file, summary_fieldnames, consolidated_row)
            append_csv_row(
                status_file,
                status_fieldnames,
                {
                    "repository_name": repository_name,
                    "repository_path": repository_key,
                    "output_dir": str(output_dir),
                    "status": "concluido",
                    "message": "CK executada com sucesso.",
                },
            )
            processed_count += 1
        except Exception as exc:
            append_csv_row(
                status_file,
                status_fieldnames,
                {
                    "repository_name": repository_name,
                    "repository_path": repository_key,
                    "output_dir": str(output_dir),
                    "status": "erro",
                    "message": str(exc),
                },
            )
            error_count += 1
            print(f"Erro em {repository_name}: {exc}")

    print("Execucao em lote finalizada.")
    print(f"Repositorios processados com sucesso: {processed_count}")
    print(f"Repositorios pulados: {skipped_count}")
    print(f"Repositorios com erro: {error_count}")
    print(f"Resumo consolidado: {summary_file}")
    print(f"Status incremental: {status_file}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
