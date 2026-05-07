import requests, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('LAB01/.env'), override=True)
token = os.getenv('GITHUB_TOKEN')
headers = {'Authorization': 'token ' + token, 'Content-Type': 'application/json'}

for page_size in [10, 30, 50, 100]:
    q = """query($n: Int!) { repository(owner: "facebook", name: "react") {
        pullRequests(states: MERGED, first: $n, orderBy: {field: CREATED_AT, direction: DESC}) {
            nodes { number state createdAt mergedAt closedAt changedFiles additions deletions body
                    reviews { totalCount } participants { totalCount } comments { totalCount } }
        }
    } }"""
    r = requests.post('https://api.github.com/graphql',
                      json={'query': q, 'variables': {'n': page_size}},
                      headers=headers, timeout=30)
    count = 0
    if r.status_code == 200:
        data = r.json()
        nodes = data.get('data', {}).get('repository', {}).get('pullRequests', {}).get('nodes', [])
        count = len(nodes) if nodes else 0
    print(f'page_size={page_size:3d} -> HTTP {r.status_code} | PRs={count}')
