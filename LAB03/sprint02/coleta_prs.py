"""
Coleta de Pull Requests - Sprint 02 (versão otimizada)

Melhorias em relação à sprint01:
  - page_size 30 -> 100  (3x menos chamadas à API por repositório)
  - override=True no load_dotenv (prevalece sobre variável de ambiente do sistema)
  - Mensagens de erro mais claras (HTTP 401, 502, etc.)
  - urllib.request sem keep-alive (evita 502 por conexão reutilizada)
"""

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
load_dotenv(ENV_PATH, override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError(f"GITHUB_TOKEN não encontrado. Verifique o arquivo: {ENV_PATH}")

GRAPHQL_URL = "https://api.github.com/graphql"
REPOS_CSV = Path(__file__).resolve().parents[1] / "sprint01" / "repositorios.csv"
OUTPUT_CSV = Path(__file__).resolve().parent / "pull_requests.csv"

MAX_PRS_PER_REPO = 500
MIN_REVIEW_COUNT = 1
MIN_ANALYSIS_HOURS = 1.0
PAGE_SIZE = 100  # sprint01 usava 30 - 3x menos roundtrips

CSV_FIELDS = [
    "repo_name", "pr_number", "state",
    "files_changed", "additions", "deletions",
    "created_at", "merged_at", "closed_at",
    "analysis_time_hours", "body_char_count",
    "review_count", "participants_count", "comments_count",
]

_QUERY = """
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
                number state createdAt mergedAt closedAt
                changedFiles additions deletions body
                reviews      {{ totalCount }}
                participants {{ totalCount }}
                comments     {{ totalCount }}
            }}
        }}
    }}
}}
"""
QUERY_MERGED = _QUERY.format(state="MERGED")
QUERY_CLOSED = _QUERY.format(state="CLOSED")


def _graphql_request(query: str, variables: dict) -> Tuple[Optional[dict], bool]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "lab03-s02-coleta-prs",
        },
    )

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            msg = f"HTTP {exc.code}"
            if exc.code == 401:
                raise RuntimeError("Token invalido ou expirado (401). Atualize o GITHUB_TOKEN no .env.")
            if attempt == 3:
                raise RuntimeError(msg)
            print(f"    {msg} (tentativa {attempt}/3). Aguardando {attempt * 5}s...")
            time.sleep(attempt * 5)
            continue
        except Exception as exc:
            if attempt == 3:
                raise
            print(f"    Erro de rede (tentativa {attempt}/3): {exc}. Aguardando {attempt * 5}s...")
            time.sleep(attempt * 5)
            continue

        has_errors = "errors" in body
        has_data = "data" in body and body["data"] is not None

        if has_errors and not has_data:
            errors = body["errors"]
            if any("RESOURCE_LIMITS" in str(e) for e in errors):
                return None, True
            is_transient = any(
                any(kw in str(e).lower() for kw in ["timeout", "502", "503", "504"])
                for e in errors
            )
            if is_transient and attempt < 3:
                time.sleep(attempt * 5)
                continue
            raise RuntimeError(f"GraphQL errors: {errors}")

        if has_data:
            return body["data"], False

    raise RuntimeError("Falha apos 3 tentativas.")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _analysis_hours(created_at: str, merged_at: Optional[str], closed_at: Optional[str]) -> Optional[float]:
    end = merged_at or closed_at
    if not end:
        return None
    delta = _parse_iso(end) - _parse_iso(created_at)
    return round(delta.total_seconds() / 3600, 4)


def _process_node(pr: dict, repo_full: str) -> Optional[Dict]:
    review_count = pr.get("reviews", {}).get("totalCount", 0)
    if review_count < MIN_REVIEW_COUNT:
        return None
    hours = _analysis_hours(pr["createdAt"], pr.get("mergedAt"), pr.get("closedAt"))
    if hours is None or hours < MIN_ANALYSIS_HOURS:
        return None
    return {
        "repo_name": repo_full,
        "pr_number": pr["number"],
        "state": pr["state"],
        "files_changed": pr.get("changedFiles", 0),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "created_at": pr["createdAt"],
        "merged_at": pr.get("mergedAt") or "",
        "closed_at": pr.get("closedAt") or "",
        "analysis_time_hours": hours,
        "body_char_count": len(pr.get("body") or ""),
        "review_count": review_count,
        "participants_count": pr.get("participants", {}).get("totalCount", 0),
        "comments_count": pr.get("comments", {}).get("totalCount", 0),
    }


def _collect_for_state(owner: str, name: str, query: str, limit: int) -> List[Dict]:
    collected: List[Dict] = []
    cursor = None
    page_size = PAGE_SIZE
    repo_full = f"{owner}/{name}"

    while len(collected) < limit:
        variables = {"owner": owner, "name": name, "pageSize": page_size, "cursor": cursor}
        try:
            data, resource_limited = _graphql_request(query, variables)
        except Exception as exc:
            print(f"    [{repo_full}] Erro fatal: {exc}")
            break

        if resource_limited:
            if page_size > 10:
                page_size = max(10, page_size // 2)
                print(f"    [{repo_full}] Reduzindo page_size -> {page_size}")
                time.sleep(2)
                continue
            print(f"    [{repo_full}] Nao foi possivel reduzir page_size. Encerrando.")
            break

        if not data or not data.get("repository"):
            break

        pr_data = data["repository"]["pullRequests"]
        for pr in pr_data.get("nodes") or []:
            if not pr or "number" not in pr:
                continue
            row = _process_node(pr, repo_full)
            if row:
                collected.append(row)
                if len(collected) >= limit:
                    break

        page_info = pr_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return collected


def _collect_repo(owner: str, name: str) -> List[Dict]:
    merged = _collect_for_state(owner, name, QUERY_MERGED, MAX_PRS_PER_REPO)
    remaining = MAX_PRS_PER_REPO - len(merged)
    closed = _collect_for_state(owner, name, QUERY_CLOSED, remaining) if remaining > 0 else []
    return merged + closed


def _load_repos() -> List[Dict]:
    if not REPOS_CSV.exists():
        raise FileNotFoundError(f"{REPOS_CSV} nao encontrado. Execute coleta_repos.py primeiro.")
    with open(REPOS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _already_collected() -> Set[str]:
    if not OUTPUT_CSV.exists():
        return set()
    with open(OUTPUT_CSV, encoding="utf-8") as f:
        return {row["repo_name"] for row in csv.DictReader(f)}


def _append_rows(rows: List[Dict]) -> None:
    file_exists = OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    repos = _load_repos()
    done = _already_collected()
    pending = [r for r in repos if r["name_with_owner"] not in done]

    if not pending:
        print("Todos os repositorios ja foram coletados.")
        return 0

    total = len(repos)
    start = time.time()
    total_prs = 0

    print(f"Repositorios: {total} | Ja coletados: {len(done)} | Pendentes: {len(pending)}")
    print(f"Page size: {PAGE_SIZE} | Max PRs/repo: {MAX_PRS_PER_REPO}")
    print(f"Lendo de:   {REPOS_CSV}")
    print(f"Salvando em: {OUTPUT_CSV}\n")

    for i, repo in enumerate(pending, start=1):
        name_with_owner = repo["name_with_owner"]
        owner, name = name_with_owner.split("/", 1)
        elapsed = time.time() - start
        print(f"[{len(done) + i}/{total}] {name_with_owner} ({elapsed:.0f}s)")

        try:
            prs = _collect_repo(owner, name)
        except Exception as exc:
            print(f"  ERRO em {name_with_owner}: {exc}")
            prs = []

        if prs:
            _append_rows(prs)

        total_prs += len(prs)
        print(f"  -> {len(prs)} PRs coletados (acumulado: {total_prs})")

    elapsed = time.time() - start
    print(f"\nConcluido em {elapsed:.1f}s | Total PRs: {total_prs} | {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
