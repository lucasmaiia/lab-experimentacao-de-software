#!/usr/bin/env python3
"""
Executa a ferramenta CK em lote nos repositorios Java.
Pipeline por repo: git clone --depth 1 -> CK -> extrai metricas -> apaga clone.
Usa diretorio temporario para cada repo, economizando disco.
Retomavel: pula repos ja processados no CSV de saida.
"""

import argparse
import csv
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List


SUMMARY_FIELDNAMES = [
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
]

_write_lock = threading.Lock()
_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def parse_arguments() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Pipeline CK em lote: clone -> analise -> cleanup."
    )
    parser.add_argument(
        "--repos-csv",
        default=str(script_dir.parent / "sprint01" / "repositorios_java_top1000.csv"),
        help="CSV com os repositorios (colunas: name, clone_url).",
    )
    parser.add_argument(
        "--ck-jar",
        default=str(script_dir / "ck-0.7.0-jar-with-dependencies.jar"),
        help="Caminho para o JAR do CK.",
    )
    parser.add_argument(
        "--summary-file",
        default=str(script_dir / "ck_batch_summary.csv"),
        help="CSV consolidado de saida com as metricas.",
    )
    parser.add_argument(
        "--jobs", "-j",
        type=int,
        default=4,
        help="Repos processados em paralelo (default: 4).",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=None,
        help="Limita quantos repos processar (para testes).",
    )
    parser.add_argument(
        "--clone-timeout",
        type=int,
        default=180,
        help="Timeout em segundos para git clone (default: 180).",
    )
    parser.add_argument(
        "--ck-timeout",
        type=int,
        default=600,
        help="Timeout em segundos para execucao do CK (default: 600).",
    )
    return parser.parse_args()


def load_repos(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_completed(summary_path: Path) -> set:
    if not summary_path.is_file():
        return set()

    completed = set()
    try:
        with summary_path.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row.get("repository_name", "").strip()
                if name:
                    completed.add(name)
    except Exception:
        return set()
    return completed


def initialize_summary(summary_path: Path) -> None:
    if summary_path.exists():
        return
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=SUMMARY_FIELDNAMES).writeheader()


def append_row(summary_path: Path, row: Dict) -> None:
    with _write_lock:
        with summary_path.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=SUMMARY_FIELDNAMES).writerow(row)


def shallow_clone(clone_url: str, dest: Path, timeout: int) -> None:
    subprocess.run(
        [
            "git", "clone",
            "--depth", "1",
            "--single-branch",
            "--no-tags",
            "--quiet",
            clone_url,
            str(dest),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )


def run_ck(ck_jar: Path, repo_dir: Path, output_dir: Path, timeout: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "java", "-jar", str(ck_jar),
            str(repo_dir),
            "true",
            "0",
            "false",
        ],
        cwd=str(output_dir),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )


def extract_metrics(class_csv: Path) -> Dict[str, List[float]]:
    result = {"cbo": [], "dit": [], "lcom": [], "loc": []}

    with class_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        col_map = {}
        for metric in result:
            for fn in fieldnames:
                if fn.lower() == metric:
                    col_map[metric] = fn
                    break

        for row in reader:
            for metric, col in col_map.items():
                raw = (row.get(col) or "").strip()
                if raw:
                    try:
                        result[metric].append(float(raw))
                    except ValueError:
                        pass

    return result


def calc_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0, "median": 0, "stdev": 0, "min": 0, "max": 0}
    s = {
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }
    s["stdev"] = round(statistics.stdev(values), 4) if len(values) > 1 else 0.0
    return s


def process_repo(
    repo_name: str,
    clone_url: str,
    ck_jar: Path,
    clone_timeout: int,
    ck_timeout: int,
) -> Dict:
    with tempfile.TemporaryDirectory(prefix="ck_") as tmp_dir:
        tmp = Path(tmp_dir)
        repo_dir = tmp / "repo"
        ck_output = tmp / "output"

        shallow_clone(clone_url, repo_dir, clone_timeout)
        run_ck(ck_jar, repo_dir, ck_output, ck_timeout)

        class_csv = ck_output / "class.csv"
        if not class_csv.is_file():
            raise FileNotFoundError("CK nao gerou class.csv")

        raw = extract_metrics(class_csv)

        if not raw["cbo"]:
            raise ValueError("Nenhuma classe Java valida encontrada")

        cbo = calc_stats(raw["cbo"])
        dit = calc_stats(raw["dit"])
        lcom = calc_stats(raw["lcom"])
        loc = calc_stats(raw["loc"])

        return {
            "repository_name": repo_name,
            "class_count": len(raw["cbo"]),
            "loc_total": int(sum(raw["loc"])) if raw["loc"] else 0,
            "loc_mean": loc["mean"],
            "loc_median": loc["median"],
            "loc_stdev": loc["stdev"],
            "cbo_mean": cbo["mean"],
            "cbo_median": cbo["median"],
            "cbo_stdev": cbo["stdev"],
            "cbo_min": cbo["min"],
            "cbo_max": cbo["max"],
            "dit_mean": dit["mean"],
            "dit_median": dit["median"],
            "dit_stdev": dit["stdev"],
            "dit_min": dit["min"],
            "dit_max": dit["max"],
            "lcom_mean": lcom["mean"],
            "lcom_median": lcom["median"],
            "lcom_stdev": lcom["stdev"],
            "lcom_min": lcom["min"],
            "lcom_max": lcom["max"],
        }


def format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


def main() -> int:
    args = parse_arguments()

    repos_csv = Path(args.repos_csv).resolve()
    ck_jar = Path(args.ck_jar).resolve()
    summary_path = Path(args.summary_file).resolve()

    if not repos_csv.is_file():
        print(f"Erro: CSV nao encontrado: {repos_csv}", file=sys.stderr)
        return 1

    if not ck_jar.is_file():
        print(f"Erro: JAR do CK nao encontrado: {ck_jar}", file=sys.stderr)
        return 1

    if shutil.which("java") is None:
        print("Erro: Java nao encontrado no PATH.", file=sys.stderr)
        return 1

    repos = load_repos(repos_csv)
    if args.max_repos:
        repos = repos[: args.max_repos]

    initialize_summary(summary_path)
    completed = load_completed(summary_path)

    pending = [r for r in repos if r["name"] not in completed]

    total = len(repos)
    done_count = len(completed)
    to_process = len(pending)

    log("=" * 60)
    log("CK Batch Pipeline")
    log("=" * 60)
    log(f"Repos no CSV:       {total}")
    log(f"Ja processados:     {done_count}")
    log(f"Pendentes:          {to_process}")
    log(f"Workers paralelos:  {args.jobs}")
    log(f"Clone timeout:      {args.clone_timeout}s")
    log(f"CK timeout:         {args.ck_timeout}s")
    log(f"Saida:              {summary_path}")
    log("=" * 60)

    if to_process == 0:
        log("Nenhum repo pendente.")
        return 0

    success = 0
    errors = 0
    error_names = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {}
        for repo in pending:
            future = executor.submit(
                process_repo,
                repo["name"],
                repo["clone_url"],
                ck_jar,
                args.clone_timeout,
                args.ck_timeout,
            )
            futures[future] = repo["name"]

        for i, future in enumerate(as_completed(futures), start=1):
            repo_name = futures[future]
            progress = done_count + i
            elapsed = time.time() - start_time
            avg_per_repo = elapsed / i
            remaining = avg_per_repo * (to_process - i)

            try:
                result = future.result()
                append_row(summary_path, result)
                success += 1
                log(
                    f"[{progress}/{total}] OK  {repo_name} "
                    f"({result['class_count']} classes, "
                    f"LOC={result['loc_total']}) "
                    f"ETA: {format_duration(remaining)}"
                )
            except Exception as exc:
                errors += 1
                error_names.append(repo_name)
                short_err = str(exc).split("\n")[0][:80]
                log(f"[{progress}/{total}] ERR {repo_name}: {short_err}")

    elapsed = time.time() - start_time

    log("")
    log("=" * 60)
    log("RESULTADO FINAL")
    log("=" * 60)
    log(f"Tempo total:   {format_duration(elapsed)}")
    log(f"Sucesso:       {success}")
    log(f"Erros:         {errors}")
    log(f"CSV gerado:    {summary_path}")

    if error_names:
        log(f"\nRepos com erro ({len(error_names)}):")
        for name in error_names:
            log(f"  - {name}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrompido. Progresso salvo no CSV.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"Erro fatal: {exc}", file=sys.stderr)
        sys.exit(1)
