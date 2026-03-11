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

def get_query(stars_filter="stars:>0"):
    return f"""
    query($pageSize: Int!, $cursor: String) {{
        search(query: "{stars_filter} sort:stars-desc", type: REPOSITORY, first: $pageSize, after: $cursor) {{
            pageInfo {{ hasNextPage endCursor }}
            edges {{
                node {{
                    ... on Repository {{
                        nameWithOwner
                        stargazerCount
                        createdAt
                        pushedAt
                        primaryLanguage {{ name }}
                        isFork
                        isArchived
                        licenseInfo {{ spdxId }}
                        diskUsage
                        languages(first: 10) {{ totalSize nodes {{ name }} }}

                        pullRequests(states: MERGED) {{ totalCount }}
                        releases {{ totalCount }}

                        issuesOpen: issues(states: OPEN) {{ totalCount }}
                        issuesClosed: issues(states: CLOSED) {{ totalCount }}
                    }}
                }}
            }}
        }}
    }}
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
    # tempo de início para medir duração total e por página
    start_time = time.time()
    # informar objetivo da coleta ao usuário
    estimated_pages = (TARGET_REPOS + PAGE_SIZE - 1) // PAGE_SIZE
    print(f"Iniciando coleta: objetivo = {TARGET_REPOS} repositórios; tamanho de página = {PAGE_SIZE}; estimadas {estimated_pages} páginas.")
    print(f"Arquivo de saída: {OUTPUT_CSV}")

    rows = []
    cursor = None
    total = 0
    seen_repos = set()
    current_stars_filter = "stars:>0"
    last_seen_stars = None

    while total < TARGET_REPOS:
        variables = {"pageSize": PAGE_SIZE, "cursor": cursor}
        query_str = get_query(current_stars_filter)
        data = github_graphql(query_str, variables)
        
        elapsed = time.time() - start_time
        print(f"Coletando página... (Filtro: {current_stars_filter} | Total CSV: {total}) - Tempo: {elapsed:.1f}s")

        search = data["search"]
        edges = search["edges"]

        for edge in edges:
            repo = edge["node"]
            if not repo:
                continue

            # Campos básicos
            name = repo["nameWithOwner"]
            stars = repo["stargazerCount"]
            last_seen_stars = stars

            if name in seen_repos:
                continue
            seen_repos.add(name)

            # Datas
            created_at = iso_to_dt(repo["createdAt"])
            raw_pushed = repo.get("pushedAt") or repo["createdAt"]
            pushed_at = iso_to_dt(raw_pushed)

            age_days = max(0, (now - created_at).days)
            age_years = age_days / 365.25

            sec_diff = max(0, (now - pushed_at).total_seconds())
            days_since_update = round(sec_diff / 86400.0, 2)

            # Meta dados adicionais para filtragem
            is_fork = repo.get("isFork")
            is_archived = repo.get("isArchived")
            license_spdx = (repo.get("licenseInfo") or {}).get("spdxId")
            disk_usage = repo.get("diskUsage")  # geralmente em KB
            languages_conn = repo.get("languages") or {}
            lang_nodes = [n.get("name") for n in (languages_conn.get("nodes") or [])]
            primary_lang = (repo.get("primaryLanguage") or {}).get("name")

            merged_prs = repo["pullRequests"]["totalCount"]
            releases = repo["releases"]["totalCount"]

            issues_open = repo["issuesOpen"]["totalCount"]
            issues_closed = repo["issuesClosed"]["totalCount"]
            issues_total = issues_open + issues_closed
            issues_closed_ratio = safe_div(issues_closed, issues_total)

            # ===== Filtros =====
            # evitar forks e repositórios arquivados
            if is_fork or is_archived:
                # pular sem contar
                continue

            # exigir licença (assumir OSS se spdxId definido e diferente de NOASSERTION)
            if not license_spdx or license_spdx == "NOASSERTION":
                continue

            # tamanho mínimo em KB (3 MB = 3072 KB)
            try:
                size_ok = (disk_usage is not None) and (int(disk_usage) >= 3072)
            except Exception:
                size_ok = False
            if not size_ok:
                continue

            # exigir presença de linguagens de programação (evitar repositórios que são só docs/links)
            acceptable_langs = {
                'Python', 'JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'Go', 'Rust',
                'C#', 'Dart', 'Kotlin', 'Scala', 'PHP', 'Ruby', 'Swift', 'R', 'Shell'
            }
            has_prog = False
            if primary_lang in acceptable_langs:
                has_prog = True
            else:
                for ln in lang_nodes:
                    if ln in acceptable_langs:
                        has_prog = True
                        break
            if not has_prog:
                continue

            # se passou todos os filtros, adiciona ao resultado e conta
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
                "license_spdx": license_spdx,
                "disk_usage_kb": disk_usage,
                "language_nodes": ",".join(lang_nodes),
            })

            total += 1
            if total >= TARGET_REPOS:
                break

        page = search["pageInfo"]
        
        if page["hasNextPage"]:
            cursor = page["endCursor"]
        else:
            # A API do GitHub limitou em 1000 resultados para a query atual.
            # Começar uma nova query a partir da quantidade de estrelas do último repositório visto.
            if not edges or last_seen_stars is None:
                break # Evita loop infinito se não retornar nada
            current_stars_filter = f"stars:<={last_seen_stars}"
            cursor = None

        # timer pra não bater repetidamente
        time.sleep(0.5)

    # escrever o CSV
    fieldnames = list(rows[0].keys()) if rows else []
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    total_elapsed = time.time() - start_time
    print(f"OK: gerado {OUTPUT_CSV} com {len(rows)} repositórios.")
    print(f"Tempo total de coleta: {total_elapsed:.1f}s")

if __name__ == "__main__":
    main()