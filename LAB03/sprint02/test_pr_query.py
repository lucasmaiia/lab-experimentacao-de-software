import urllib.request, json, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('LAB01/.env'), override=True)
token = os.getenv('GITHUB_TOKEN')

query = """
query($owner: String!, $name: String!, $pageSize: Int!, $cursor: String) {
    repository(owner: $owner, name: $name) {
        pullRequests(
            states: MERGED,
            first: $pageSize,
            after: $cursor,
            orderBy: {field: CREATED_AT, direction: DESC}
        ) {
            pageInfo { hasNextPage endCursor }
            nodes {
                number state createdAt mergedAt closedAt
                changedFiles additions deletions body
                reviews      { totalCount }
                participants { totalCount }
                comments     { totalCount }
            }
        }
    }
}
"""

for page_size in [10, 30, 50, 100]:
    payload = json.dumps({"query": query, "variables": {"owner": "EbookFoundation", "name": "free-programming-books", "pageSize": page_size, "cursor": None}}).encode()
    req = urllib.request.Request(
        'https://api.github.com/graphql', data=payload, method='POST',
        headers={'Authorization': f'token {token}', 'Content-Type': 'application/json', 'User-Agent': 'test'}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
            nodes = body.get('data', {}).get('repository', {}).get('pullRequests', {}).get('nodes', [])
            print(f'page_size={page_size:3d} -> OK, {len(nodes)} PRs')
    except urllib.error.HTTPError as e:
        print(f'page_size={page_size:3d} -> HTTP {e.code}: {e.read().decode()[:80]}')
    except Exception as e:
        print(f'page_size={page_size:3d} -> Erro: {e}')
