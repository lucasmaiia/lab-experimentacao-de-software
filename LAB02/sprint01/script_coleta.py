import csv
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests


SEARCH_API_URL = "https://api.github.com/search/repositories"
REPO_API_URL = "https://api.github.com/repos/{owner}/{repo}"
OUTPUT_FILE = "repositorios_java_top1000.csv"
PER_PAGE = 100
TOTAL_PAGES = 10
REQUEST_DELAY_SECONDS = 0.3
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

CSV_FIELDS = [
    "id",
    "name",
    "full_name",
    "owner_login",
    "html_url",
    "description",
    "language",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "size_kb",
    "releases_count",
    "created_at",
    "updated_at",
    "pushed_at",
    "age_days",
    "age_years",
    "clone_url",
]


def build_session() -> requests.Session:
    """Cria uma sessao HTTP com cabecalhos padrao para a API do GitHub."""
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "User-Agent": "lab02-sprint01-coleta",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        session.headers["Authorization"] = f"Bearer {github_token}"

    return session


def wait_for_rate_limit(response: requests.Response) -> None:
    """Espera ate o reset do rate limit quando necessario."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_at = response.headers.get("X-RateLimit-Reset")

    if remaining != "0" or not reset_at:
        return

    wait_seconds = max(int(reset_at) - int(time.time()) + 1, 1)
    print(
        f"Rate limit atingido. Aguardando {wait_seconds} segundos para continuar..."
    )
    time.sleep(wait_seconds)


def request_json(
    session: requests.Session,
    url: str,
    params: Optional[Dict] = None,
    context: str = "requisicao",
) -> tuple[requests.Response, object]:
    """Executa uma requisicao GET com retentativas e tratamento de erros."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Falha de rede em {context}: {exc}") from exc

            print(
                f"Erro de rede em {context} (tentativa {attempt}/{MAX_RETRIES}). "
                "Tentando novamente..."
            )
            time.sleep(attempt)
            continue

        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            wait_for_rate_limit(response)
            continue

        if response.status_code in {500, 502, 503, 504}:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Erro temporario do GitHub em {context}: HTTP {response.status_code}"
                )

            print(
                f"GitHub respondeu HTTP {response.status_code} em {context} "
                f"(tentativa {attempt}/{MAX_RETRIES}). Tentando novamente..."
            )
            time.sleep(attempt)
            continue

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = response.text

            raise RuntimeError(
                f"Erro em {context}: HTTP {response.status_code} - {error_payload}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Resposta JSON invalida em {context}.") from exc

        return response, payload

    raise RuntimeError(f"Nao foi possivel concluir {context}.")


def request_page(session: requests.Session, page: int) -> List[Dict]:
    """Busca uma pagina da API Search do GitHub."""
    params = {
        "q": "language:java",
        "sort": "stars",
        "order": "desc",
        "per_page": PER_PAGE,
        "page": page,
    }

    _, payload = request_json(
        session,
        SEARCH_API_URL,
        params=params,
        context=f"coleta da pagina {page}",
    )

    if not isinstance(payload, dict):
        raise RuntimeError(f"Resposta inesperada da API na pagina {page}.")

    items = payload.get("items")
    if not isinstance(items, list):
        raise RuntimeError(
            f"Resposta inesperada da API na pagina {page}: campo 'items' ausente."
        )

    return items


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Converte uma string ISO do GitHub para datetime em UTC."""
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def calculate_repository_age(created_at: Optional[str]) -> tuple[Optional[int], Optional[float]]:
    """Calcula a idade do repositorio em dias e anos."""
    created_dt = parse_iso_datetime(created_at)
    if created_dt is None:
        return None, None

    now = datetime.now(timezone.utc)
    age_days = max((now - created_dt).days, 0)
    age_years = round(age_days / 365.25, 3)
    return age_days, age_years


def extract_last_page_number(link_header: str) -> Optional[int]:
    """Extrai o numero da ultima pagina a partir do cabecalho Link."""
    match = re.search(r'[?&]page=(\d+)>; rel="last"', link_header)
    if not match:
        return None
    return int(match.group(1))


def fetch_releases_count(session: requests.Session, owner: str, repo: str) -> int:
    """Conta releases via endpoint REST de releases usando per_page=1."""
    url = f"{REPO_API_URL.format(owner=owner, repo=repo)}/releases"
    response, payload = request_json(
        session,
        url,
        params={"per_page": 1, "page": 1},
        context=f"coleta de releases para {owner}/{repo}",
    )

    if not isinstance(payload, list):
        raise RuntimeError(
            f"Resposta inesperada ao contar releases de {owner}/{repo}."
        )

    if not payload:
        return 0

    last_page = extract_last_page_number(response.headers.get("Link", ""))
    if last_page is not None:
        return last_page

    return len(payload)


def normalize_repository(session: requests.Session, repo: Dict) -> Dict:
    """Converte o JSON do GitHub para o formato esperado no CSV."""
    owner = repo.get("owner") or {}
    owner_login = owner.get("login")
    repo_name = repo.get("name")

    if not owner_login or not repo_name:
        raise RuntimeError("Repositorio sem owner/name suficiente para enriquecimento.")

    releases_count = fetch_releases_count(session, owner_login, repo_name)
    age_days, age_years = calculate_repository_age(repo.get("created_at"))

    return {
        "id": repo.get("id"),
        "name": repo_name,
        "full_name": repo.get("full_name"),
        "owner_login": owner_login,
        "html_url": repo.get("html_url"),
        "description": repo.get("description"),
        "language": repo.get("language"),
        "stargazers_count": repo.get("stargazers_count"),
        "forks_count": repo.get("forks_count"),
        "open_issues_count": repo.get("open_issues_count"),
        "size_kb": repo.get("size"),
        "releases_count": releases_count,
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "age_days": age_days,
        "age_years": age_years,
        "clone_url": repo.get("clone_url"),
    }


def write_csv(rows: List[Dict], output_path: Path) -> None:
    """Escreve os repositorios coletados no arquivo CSV final."""
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """Coordena a coleta das 10 paginas e gera o CSV com 1000 repositorios."""
    session = build_session()
    collected_repositories: List[Dict] = []
    output_path = Path(__file__).resolve().parent / OUTPUT_FILE

    if "Authorization" not in session.headers:
        print(
            "Aviso: GITHUB_TOKEN nao definido. Como a coleta agora inclui releases de "
            "1000 repositorios, a execucao sem token pode demorar muito por rate limit."
        )

    print("Iniciando coleta enriquecida dos 1000 repositorios Java mais populares...")

    for page in range(1, TOTAL_PAGES + 1):
        repositories = request_page(session, page)
        print(f"Pagina {page} coletada com {len(repositories)} repositorios.")

        for index, repository in enumerate(repositories, start=1):
            normalized = normalize_repository(session, repository)
            collected_repositories.append(normalized)
            print(
                f"Repositorio {len(collected_repositories)}/{PER_PAGE * TOTAL_PAGES}: "
                f"{normalized['full_name']} | estrelas={normalized['stargazers_count']} "
                f"| size_kb={normalized['size_kb']} | releases={normalized['releases_count']}"
            )
            time.sleep(REQUEST_DELAY_SECONDS)

    if len(collected_repositories) != PER_PAGE * TOTAL_PAGES:
        raise RuntimeError(
            "A coleta nao retornou exatamente 1000 repositorios. "
            f"Total obtido: {len(collected_repositories)}"
        )

    write_csv(collected_repositories, output_path)
    print(f"CSV gerado com sucesso em: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Erro durante a execucao: {exc}", file=sys.stderr)
        sys.exit(1)
