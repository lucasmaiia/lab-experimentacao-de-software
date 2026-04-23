import csv
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / "LAB01" / ".env"
load_dotenv(ENV_PATH)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError(f"GITHUB_TOKEN não encontrado. Verifique o arquivo: {ENV_PATH}")

GRAPHQL_URL = "https://api.github.com/graphql"
REPOS_CSV = Path(__file__).resolve().parent / "repositorios.csv"
OUTPUT_CSV = Path(__file__).resolve().parent / "pull_requests.csv"

MAX_PRS_PER_REPO = 500
MIN_REVIEW_COUNT = 1
MIN_ANALYSIS_HOURS = 1.0

CSV_FIELDS = [
    "repo_name",
    "pr_number",
    "state",
    "files_changed",
    "additions",
    "deletions",
    "created_at",
    "merged_at",
    "closed_at",
    "analysis_time_hours",
    "body_char_count",
    "review_count",
    "participants_count",
    "comments_count",
]

QUERY_TEMPLATE = """
query($owner: String!, $name: String!, $pageSize: Int!, $cursor: String) {{
    repository(owner: $owner, name: $name) {{
        pullRequests(
            states: {state},
            first: $pageSize,
            after: $cursor,
            orderBy: {{field: CREATED_AT, direction: DESC}}
        ) {{
            pageInfo {{ hasNextPage endCursor }}
            nodes {{
                number
                state
                createdAt
                mergedAt
                closedAt
                changedFiles
                additions
                deletions
                body
                reviews {{ totalCount }}
                participants {{ totalCount }}
                comments {{ totalCount }}
            }}
        }}
    }}
}}
"""

QUERY_MERGED = QUERY_TEMPLATE.format(state="MERGED")
QUERY_CLOSED = QUERY_TEMPLATE.format(state="CLOSED")


def graphql_request(query: str, variables: dict) -> Tuple[Optional[dict], bool]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")

    for attempt in range(1, 4):
        req = urllib.request.Request(
            GRAPHQL_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "lab03-coleta-prs",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if attempt == 3:
                raise
            wait = attempt * 5
            print(f"    Erro de rede (tentativa {attempt}/3): {exc}. Aguardando {wait}s...")
            time.sleep(wait)
            continue

        has_errors = "errors" in body
        has_data = "data" in body and body["data"] is not None

        if has_errors and not has_data:
            errors = body["errors"]
            is_resource_limit = any("RESOURCE_LIMITS" in str(e) for e in errors)
            if is_resource_limit:
                return None, True
            is_transient = any(
                any(kw in str(e).lower() for kw in ["timeout", "502", "503", "504"])
                for e in errors
            )
            if is_transient and attempt < 3:
                wait = attempt * 5
                print(f"    Erro transiente (tentativa {attempt}/3). Aguardando {wait}s...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"GraphQL errors: {errors}")

        if has_data:
            return body["data"], False

    raise RuntimeError("Falha após 3 tentativas.")


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def calc_analysis_hours(created_at: str, merged_at: Optional[str], closed_at: Optional[str]) -> Optional[float]:
    end_date = merged_at or closed_at
    if not end_date:
        return None
    delta = parse_iso(end_date) - parse_iso(created_at)
    return round(delta.total_seconds() / 3600, 4)


def load_repos() -> List[Dict]:
    if not REPOS_CSV.exists():
        raise FileNotFoundError(
            f"Arquivo {REPOS_CSV} não encontrado. Execute coleta_repos.py primeiro."
        )
    with open(REPOS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_already_collected() -> Set[str]:
    if not OUTPUT_CSV.exists():
        return set()
    repos = set()
    with open(OUTPUT_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            repos.add(row["repo_name"])
    return repos


def process_pr_node(pr: dict, repo_full_name: str) -> Optional[Dict]:
    review_count = pr.get("reviews", {}).get("totalCount", 0)
    if review_count < MIN_REVIEW_COUNT:
        return None

    hours = calc_analysis_hours(pr["createdAt"], pr.get("mergedAt"), pr.get("closedAt"))
    if hours is None or hours < MIN_ANALYSIS_HOURS:
        return None

    body_text = pr.get("body") or ""

    return {
        "repo_name": repo_full_name,
        "pr_number": pr["number"],
        "state": pr["state"],
        "files_changed": pr.get("changedFiles", 0),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "created_at": pr["createdAt"],
        "merged_at": pr.get("mergedAt") or "",
        "closed_at": pr.get("closedAt") or "",
        "analysis_time_hours": hours,
        "body_char_count": len(body_text),
        "review_count": review_count,
        "participants_count": pr.get("participants", {}).get("totalCount", 0),
        "comments_count": pr.get("comments", {}).get("totalCount", 0),
    }


def collect_prs_for_state(owner: str, name: str, query: str, limit: int) -> List[Dict]:
    collected = []
    cursor = None
    page_size = 30
    repo_full = f"{owner}/{name}"

    while len(collected) < limit:
        variables = {"owner": owner, "name": name, "pageSize": page_size, "cursor": cursor}

        try:
            data, resource_limited = graphql_request(query, variables)
        except Exception as exc:
            if page_size > 5 and "RESOURCE_LIMITS" in str(exc):
                page_size = max(5, page_size // 2)
                print(f"    Reduzindo page_size para {page_size} por limite de recursos")
                continue
            raise

        if resource_limited:
            if page_size > 5:
                page_size = max(5, page_size // 2)
                print(f"    Reduzindo page_size para {page_size} por limite de recursos")
                time.sleep(2)
                continue
            else:
                print(f"    Não foi possível reduzir mais o page_size. Encerrando coleta para {repo_full}.")
                break

        if not data or not data.get("repository"):
            break

        pr_data = data["repository"]["pullRequests"]
        nodes = pr_data.get("nodes") or []

        for pr in nodes:
            if not pr or "number" not in pr:
                continue

            row = process_pr_node(pr, repo_full)
            if row:
                collected.append(row)
                if len(collected) >= limit:
                    break

        page_info = pr_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        time.sleep(0.4)

    return collected


def collect_all_prs(owner: str, name: str) -> List[Dict]:
    merged = collect_prs_for_state(owner, name, QUERY_MERGED, MAX_PRS_PER_REPO)

    remaining = MAX_PRS_PER_REPO - len(merged)
    closed = []
    if remaining > 0:
        closed = collect_prs_for_state(owner, name, QUERY_CLOSED, remaining)

    return merged + closed


def append_rows_to_csv(rows: List[Dict]) -> None:
    file_exists = OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    repos = load_repos()
    already_done = load_already_collected()
    pending = [r for r in repos if r["name_with_owner"] not in already_done]

    if not pending:
        print("Todos os repositórios já foram coletados.")
        return 0

    total = len(repos)
    done_count = len(already_done)
    total_prs = 0
    start = time.time()

    print(f"Total de repositórios: {total}")
    print(f"Já coletados: {done_count}")
    print(f"Pendentes: {len(pending)}")
    print(f"Limite de PRs por repo: {MAX_PRS_PER_REPO}")
    print(f"Filtros: reviews ≥ {MIN_REVIEW_COUNT}, análise ≥ {MIN_ANALYSIS_HOURS}h")
    print(f"Saída: {OUTPUT_CSV}\n")

    for i, repo in enumerate(pending, start=1):
        name_with_owner = repo["name_with_owner"]
        owner, name = name_with_owner.split("/", 1)

        elapsed = time.time() - start
        print(f"[{done_count + i}/{total}] {name_with_owner} — {elapsed:.0f}s")

        try:
            prs = collect_all_prs(owner, name)
        except Exception as exc:
            print(f"  ERRO ao coletar {name_with_owner}: {exc}")
            print(f"  Pulando repositório. Os anteriores foram salvos.")
            continue

        if prs:
            append_rows_to_csv(prs)

        total_prs += len(prs)
        print(f"  → {len(prs)} PRs coletados (acumulado: {total_prs})")
        time.sleep(0.5)

    elapsed = time.time() - start
    print(f"\nConcluído em {elapsed:.1f}s")
    print(f"Total de PRs coletados nesta execução: {total_prs}")
    print(f"Arquivo: {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
