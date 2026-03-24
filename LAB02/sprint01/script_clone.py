import argparse
import csv
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_CSV_FILE = "repositorios_java_top1000.csv"
DEFAULT_CLONE_DIR = "repos_clonados"
DEFAULT_STATUS_FILE = "clone_status.csv"


def parse_arguments() -> argparse.Namespace:
    """Le os argumentos da linha de comando."""
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Le o CSV da coleta e clona os repositorios localmente."
    )
    parser.add_argument(
        "--csv-file",
        default=str(script_dir / DEFAULT_CSV_FILE),
        help="Caminho para o CSV gerado pelo script de coleta.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(script_dir / DEFAULT_CLONE_DIR),
        help="Diretorio onde os repositorios serao clonados.",
    )
    parser.add_argument(
        "--status-file",
        default=str(script_dir / DEFAULT_STATUS_FILE),
        help="Arquivo CSV de status salvo incrementalmente durante a clonagem.",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=None,
        help="Limita a quantidade de repositorios clonados. Se omitido, usa todo o CSV.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="Quantidade de clones em paralelo. Padrao: 4.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Profundidade do clone. Padrao: 1 para acelerar a busca.",
    )
    parser.add_argument(
        "--full-history",
        action="store_true",
        help="Desativa clone raso e baixa o historico completo do repositorio.",
    )
    return parser.parse_args()


def ensure_git_available() -> None:
    """Confirma se o Git esta disponivel no PATH."""
    if shutil.which("git") is None:
        raise EnvironmentError(
            "Git nao encontrado no PATH. Instale o Git e tente novamente."
        )


def validate_csv_path(csv_path: Path) -> None:
    """Valida se o arquivo CSV informado existe."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Arquivo CSV nao encontrado em: {csv_path}")


def validate_arguments(args: argparse.Namespace) -> None:
    """Valida argumentos numericos para evitar configuracoes invalidas."""
    if args.max_repos is not None and args.max_repos <= 0:
        raise ValueError("O valor de --max-repos deve ser maior que zero.")

    if args.jobs <= 0:
        raise ValueError("O valor de --jobs deve ser maior que zero.")

    if args.depth <= 0:
        raise ValueError("O valor de --depth deve ser maior que zero.")


def read_repositories(csv_path: Path) -> List[Dict[str, str]]:
    """Carrega do CSV os repositorios a serem clonados."""
    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []

        required_columns = {"clone_url", "full_name"}
        missing_columns = required_columns.difference(fieldnames)
        if missing_columns:
            raise ValueError(
                "O CSV nao contem as colunas obrigatorias: "
                + ", ".join(sorted(missing_columns))
            )

        repositories = list(reader)

    if not repositories:
        raise ValueError("O CSV informado esta vazio.")

    return repositories


def destination_path(output_dir: Path, repository: Dict[str, str]) -> Path:
    """Define a pasta local do repositorio a partir de owner/repo."""
    full_name = (repository.get("full_name") or "").strip()
    if "/" in full_name:
        owner, repo_name = full_name.split("/", 1)
        return output_dir / owner / repo_name

    fallback_name = full_name or (repository.get("name") or "repositorio_sem_nome")
    safe_name = fallback_name.replace("/", "_").replace("\\", "_")
    return output_dir / safe_name


def iter_repositories(
    repositories: List[Dict[str, str]], max_repos: int | None
) -> Iterable[Dict[str, str]]:
    """Aplica um limite opcional de quantidade de repositorios."""
    if max_repos is None:
        return repositories
    return repositories[:max_repos]


def load_completed_destinations(status_file: Path) -> set[str]:
    """Le o arquivo de status para retomar apenas os clones pendentes."""
    if not status_file.is_file():
        return set()

    completed = set()
    with status_file.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("status") == "clonado":
                completed.add((row.get("target_dir") or "").strip())
    return completed


def initialize_status_file(status_file: Path) -> None:
    """Cria o arquivo de status com cabecalho caso ele ainda nao exista."""
    if status_file.exists():
        return

    status_file.parent.mkdir(parents=True, exist_ok=True)
    with status_file.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "full_name",
                "clone_url",
                "target_dir",
                "status",
                "message",
            ],
        )
        writer.writeheader()


def append_status(
    status_file: Path,
    full_name: str,
    clone_url: str,
    target_dir: Path,
    status: str,
    message: str,
) -> None:
    """Salva o resultado de cada repositorio imediatamente apos o processamento."""
    with status_file.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "full_name",
                "clone_url",
                "target_dir",
                "status",
                "message",
            ],
        )
        writer.writerow(
            {
                "full_name": full_name,
                "clone_url": clone_url,
                "target_dir": str(target_dir),
                "status": status,
                "message": message,
            }
        )


def build_clone_command(
    clone_url: str, target_dir: Path, depth: int, full_history: bool
) -> List[str]:
    """Monta o comando git clone com opcoes de aceleracao."""
    command = ["git", "clone", "--single-branch"]

    if not full_history:
        command.extend(["--depth", str(depth)])

    command.extend([clone_url, str(target_dir)])
    return command


def clone_repository(
    full_name: str,
    clone_url: str,
    target_dir: Path,
    depth: int,
    full_history: bool,
) -> Dict[str, str]:
    """Executa o git clone para um repositorio individual."""
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    command = build_clone_command(clone_url, target_dir, depth, full_history)

    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = (completed.stdout or "").strip()
    if completed.returncode != 0:
        if target_dir.exists() and not any(target_dir.iterdir()):
            target_dir.rmdir()
        raise RuntimeError(
            f"Falha ao clonar {full_name}. Codigo {completed.returncode}. {output}"
        )

    return {
        "full_name": full_name,
        "clone_url": clone_url,
        "target_dir": str(target_dir),
        "status": "clonado",
        "message": output or "Clone concluido com sucesso.",
    }


def main() -> int:
    """Le o CSV da coleta e clona os repositorios para a pasta de saida."""
    args = parse_arguments()
    validate_arguments(args)

    csv_path = Path(args.csv_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    status_file = Path(args.status_file).expanduser().resolve()

    ensure_git_available()
    validate_csv_path(csv_path)

    repositories = read_repositories(csv_path)
    selected_repositories = list(iter_repositories(repositories, args.max_repos))
    output_dir.mkdir(parents=True, exist_ok=True)
    initialize_status_file(status_file)

    completed_destinations = load_completed_destinations(status_file)

    print(f"Iniciando clonagem de ate {len(selected_repositories)} repositorios...")
    print(f"CSV de origem: {csv_path}")
    print(f"Pasta de destino: {output_dir}")
    print(f"Arquivo de status incremental: {status_file}")
    print(
        "Modo de clone: historico completo"
        if args.full_history
        else f"clone raso com depth={args.depth}"
    )
    print(f"Clones em paralelo: {args.jobs}")

    pending_tasks = []
    skipped_count = 0

    for repository in selected_repositories:
        clone_url = (repository.get("clone_url") or "").strip()
        full_name = (repository.get("full_name") or "").strip() or clone_url

        if not clone_url:
            target_dir = destination_path(output_dir, repository)
            append_status(
                status_file,
                full_name,
                clone_url,
                target_dir,
                "erro",
                "Repositorio sem clone_url.",
            )
            skipped_count += 1
            continue

        target_dir = destination_path(output_dir, repository)
        target_dir_str = str(target_dir)

        if target_dir.exists():
            append_status(
                status_file,
                full_name,
                clone_url,
                target_dir,
                "ignorado",
                "Repositorio ja existe localmente.",
            )
            skipped_count += 1
            continue

        if target_dir_str in completed_destinations:
            skipped_count += 1
            continue

        pending_tasks.append(
            {
                "full_name": full_name,
                "clone_url": clone_url,
                "target_dir": target_dir,
            }
        )

    print(f"Repositorios na fila de clone: {len(pending_tasks)}")
    print(f"Repositorios ja existentes ou invalidos: {skipped_count}")

    cloned_count = 0
    error_count = 0

    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        future_map = {
            executor.submit(
                clone_repository,
                task["full_name"],
                task["clone_url"],
                task["target_dir"],
                args.depth,
                args.full_history,
            ): task
            for task in pending_tasks
        }

        for index, future in enumerate(as_completed(future_map), start=1):
            task = future_map[future]
            full_name = task["full_name"]
            clone_url = task["clone_url"]
            target_dir = task["target_dir"]

            print(f"[{index}/{len(pending_tasks)}] Finalizando {full_name}...")

            try:
                result = future.result()
                append_status(
                    status_file,
                    result["full_name"],
                    result["clone_url"],
                    Path(result["target_dir"]),
                    result["status"],
                    result["message"],
                )
                cloned_count += 1
                print(f"Clone concluido: {target_dir}")
            except Exception as exc:
                append_status(
                    status_file,
                    full_name,
                    clone_url,
                    target_dir,
                    "erro",
                    str(exc),
                )
                error_count += 1
                print(f"Erro ao clonar {full_name}: {exc}")

    print("Processo de clonagem finalizado.")
    print(f"Repositorios clonados com sucesso: {cloned_count}")
    print(f"Repositorios com erro: {error_count}")
    print(f"Repositorios ignorados: {skipped_count}")
    print(f"Local dos repositorios: {output_dir}")
    print(f"Arquivo de status: {status_file}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
