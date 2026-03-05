import os
import json
import csv
import time
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("definir variavel env GITHUB_TOKEN")

# primeiro 100, depois 1000
TARGET_REPOS = 1000  
PAGE_SIZE = 10     # paginação por busca
OUTPUT_CSV = "coleta_repos.csv"

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($pageSize: Int!, $cursor: String) {
  search(query: "stars:>0 sort:stars-desc", type: REPOSITORY, first: $pageSize, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        ... on Repository {
          nameWithOwner
          stargazerCount
          createdAt
          pushedAt
          primaryLanguage { name }

          pullRequests(states: MERGED) { totalCount }
          releases { totalCount }

          issuesOpen: issues(states: OPEN) { totalCount }
          issuesClosed: issues(states: CLOSED) { totalCount }
        }
      }
    }
  }
}
"""

def github_graphql(query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "lab01-coleta"
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        data = json.loads(body)

    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]

def iso_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def safe_div(a: int, b: int) -> float:
    return (a / b) if b else 0.0

def main():
    # Apaga coleta anterior
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)

    now = datetime.now(timezone.utc)

    rows = []
    cursor = None
    total = 0

    while total < TARGET_REPOS:
        variables = {"pageSize": PAGE_SIZE, "cursor": cursor}
        data = github_graphql(QUERY, variables)
        print(f"Coletando página... (Total atual: {total})")

        search = data["search"]
        edges = search["edges"]

        for edge in edges:
            repo = edge["node"]
            if not repo:
                continue

            name = repo["nameWithOwner"]
            stars = repo["stargazerCount"]

            created_at = iso_to_dt(repo["createdAt"])
            raw_pushed = repo.get("pushedAt") or repo["createdAt"]
            pushed_at = iso_to_dt(raw_pushed)

            age_days = max(0, (now - created_at).days)
            age_years = age_days / 365.25

            days_since_update = max(0, (now - pushed_at).days)

            primary_lang = (repo.get("primaryLanguage") or {}).get("name")

            merged_prs = repo["pullRequests"]["totalCount"]
            releases = repo["releases"]["totalCount"]

            issues_open = repo["issuesOpen"]["totalCount"]
            issues_closed = repo["issuesClosed"]["totalCount"]
            issues_total = issues_open + issues_closed
            issues_closed_ratio = safe_div(issues_closed, issues_total)

            rows.append({
                "name_with_owner": name,
                "stars": stars,
                "created_at": repo["createdAt"],
                "age_days": age_days,
                "age_years": round(age_years, 3),

                "updated_at": raw_pushed,
                "days_since_update": days_since_update,
                "primary_language": primary_lang,
                "merged_pull_requests": merged_prs,
                "releases_total": releases,
                "issues_open": issues_open,
                "issues_closed": issues_closed,
                "issues_total": issues_total,
                "issues_closed_ratio": round(issues_closed_ratio, 6),
            })

            total += 1
            if total >= TARGET_REPOS:
                break

        page = search["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]

        # timer pra não bater repetidamente
        time.sleep(0.5)

    # escrever o CSV
    fieldnames = list(rows[0].keys()) if rows else []
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"OK: gerado {OUTPUT_CSV} com {len(rows)} repositórios.")

if __name__ == "__main__":
    main()