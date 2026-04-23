import csv
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / "LAB01" / ".env"
load_dotenv(ENV_PATH)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError(f"GITHUB_TOKEN não encontrado. Verifique o arquivo: {ENV_PATH}")

GRAPHQL_URL = "https://api.github.com/graphql"
TARGET_REPOS = 200
PAGE_SIZE = 10
MIN_PRS = 100
OUTPUT_CSV = Path(__file__).resolve().parent / "repositorios.csv"

CSV_FIELDS = [
    "name_with_owner",
    "stars",
    "primary_language",
    "prs_merged",
    "prs_closed",
    "prs_total",
]

QUERY = """
query($pageSize: Int!, $cursor: String, $starsFilter: String!) {
    search(query: $starsFilter, type: REPOSITORY, first: $pageSize, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        edges {
            node {
                ... on Repository {
                    nameWithOwner
                    stargazerCount
                    primaryLanguage { name }
                    prsMerged: pullRequests(states: MERGED) { totalCount }
                    prsClosed: pullRequests(states: CLOSED) { totalCount }
                }
            }
        }
    }
}
"""


def graphql_request(query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "lab03-coleta-repos",
        },
    )

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if attempt == 3:
                raise
            print(f"  Erro na requisição (tentativa {attempt}/3): {exc}")
            time.sleep(attempt * 2)
            continue

        if "errors" in body:
            raise RuntimeError(f"GraphQL errors: {body['errors']}")

        return body["data"]

    raise RuntimeError("Falha após 3 tentativas.")


def main() -> int:
    start = time.time()
    print(f"Objetivo: {TARGET_REPOS} repositórios com ≥{MIN_PRS} PRs (MERGED+CLOSED)")
    print(f"Arquivo de saída: {OUTPUT_CSV}")

    rows = []
    seen = set()
    cursor = None
    stars_filter = "stars:>0 sort:stars-desc"
    last_stars = None
    skipped = 0

    while len(rows) < TARGET_REPOS:
        variables = {
            "pageSize": PAGE_SIZE,
            "cursor": cursor,
            "starsFilter": stars_filter,
        }
        data = graphql_request(QUERY, variables)
        search = data["search"]
        edges = search["edges"]

        if not edges:
            print("Sem mais resultados. Encerrando.")
            break

        for edge in edges:
            node = edge.get("node")
            if not node:
                continue

            name = node["nameWithOwner"]
            stars = node["stargazerCount"]
            last_stars = stars

            if name in seen:
                continue
            seen.add(name)

            merged = node["prsMerged"]["totalCount"]
            closed = node["prsClosed"]["totalCount"]
            total_prs = merged + closed

            if total_prs < MIN_PRS:
                skipped += 1
                continue

            primary_lang = (node.get("primaryLanguage") or {}).get("name", "")

            rows.append({
                "name_with_owner": name,
                "stars": stars,
                "primary_language": primary_lang,
                "prs_merged": merged,
                "prs_closed": closed,
                "prs_total": total_prs,
            })

            elapsed = time.time() - start
            print(
                f"  [{len(rows)}/{TARGET_REPOS}] {name} "
                f"(★{stars} | PRs={total_prs}) — {elapsed:.0f}s"
            )

            if len(rows) >= TARGET_REPOS:
                break

        page_info = search["pageInfo"]
        if page_info["hasNextPage"]:
            cursor = page_info["endCursor"]
        else:
            if last_stars is None:
                break
            stars_filter = f"stars:<={last_stars} sort:stars-desc"
            cursor = None

        time.sleep(0.5)

    if not rows:
        print("Nenhum repositório coletado.", file=sys.stderr)
        return 1

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - start
    print(f"\nConcluído: {len(rows)} repositórios salvos em {OUTPUT_CSV}")
    print(f"Repositórios ignorados (PRs < {MIN_PRS}): {skipped}")
    print(f"Tempo total: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
