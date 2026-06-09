"""
GraphQL vs REST — Data Collector
Measures response time and response size for equivalent queries on both APIs.

Usage:
    python collector.py [--dry-run]

    --dry-run  Run only 2 reps on 2 repos to verify connectivity before the full run.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from config import (
    REPOS, QUERY_TYPES,
    N_REPETITIONS, WARMUP_REPS,
    DELAY_BETWEEN_REQUESTS, MAX_RETRIES, RETRY_WAIT,
    REST_BASE_URL, GRAPHQL_URL, OUTPUT_FILE, ERROR_LOG_FILE,
)
from queries import REST_QUERY_URLS, GRAPHQL_QUERY_STRINGS

load_dotenv(dotenv_path=Path(__file__).parents[1] / ".env")
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("ERROR: GITHUB_TOKEN is not set.")
    print("Copy LAB05/sprint01/.env.example to LAB05/sprint01/.env and fill in your token.")
    sys.exit(1)

logging.basicConfig(
    filename=Path(__file__).parent / ERROR_LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

_HEADERS_REST = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Cache-Control": "no-cache, no-store",
    "Pragma": "no-cache",
}
_HEADERS_GRAPHQL = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache, no-store",
    "Pragma": "no-cache",
}


def _handle_rate_limit(response) -> bool:
    """Return True and sleep if the response indicates rate limiting."""
    if response.status_code not in (403, 429):
        return False
    reset_ts = response.headers.get("X-RateLimit-Reset")
    wait = max(RETRY_WAIT, int(reset_ts) - int(time.time()) + 5) if reset_ts else RETRY_WAIT
    print(f"\n  [rate limit] sleeping {wait}s ...", flush=True)
    time.sleep(wait)
    return True


def measure_rest(path: str) -> tuple:
    """GET a REST endpoint. Returns (elapsed_s, size_bytes, status_code) or (None,None,None)."""
    url = f"{REST_BASE_URL}{path}"
    for attempt in range(MAX_RETRIES):
        try:
            start = time.perf_counter()
            resp = requests.get(url, headers=_HEADERS_REST, timeout=30)
            elapsed = time.perf_counter() - start
            if _handle_rate_limit(resp):
                continue
            return elapsed, len(resp.content), resp.status_code
        except requests.RequestException as exc:
            logging.error("REST attempt %d/%d failed: %s — %s", attempt + 1, MAX_RETRIES, url, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
    return None, None, None


def measure_graphql(query: str, variables: dict) -> tuple:
    """POST a GraphQL query. Returns (elapsed_s, size_bytes, status_code) or (None,None,None)."""
    payload = json.dumps({"query": query, "variables": variables})
    for attempt in range(MAX_RETRIES):
        try:
            start = time.perf_counter()
            resp = requests.post(GRAPHQL_URL, data=payload, headers=_HEADERS_GRAPHQL, timeout=30)
            elapsed = time.perf_counter() - start
            if _handle_rate_limit(resp):
                continue
            return elapsed, len(resp.content), resp.status_code
        except requests.RequestException as exc:
            logging.error("GraphQL attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
    return None, None, None


def collect_pair(rest_path: str, gql_query: str, gql_vars: dict,
                 label: str, query_type: str, n_reps: int) -> list:
    """
    Run warm-up then n_reps paired measurements (REST + GraphQL), interleaved in random order.
    Returns a list of result dicts.
    """
    # Warm-up: results discarded
    for _ in range(WARMUP_REPS):
        measure_rest(rest_path)
        time.sleep(DELAY_BETWEEN_REQUESTS)
        measure_graphql(gql_query, gql_vars)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    records = []
    for rep in range(1, n_reps + 1):
        ts = datetime.now().isoformat()

        if random.random() < 0.5:
            rt, rs, rcode = measure_rest(rest_path)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            gt, gs, gcode = measure_graphql(gql_query, gql_vars)
        else:
            gt, gs, gcode = measure_graphql(gql_query, gql_vars)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            rt, rs, rcode = measure_rest(rest_path)

        time.sleep(DELAY_BETWEEN_REQUESTS)

        if rt is not None:
            records.append({
                "query_type": query_type,
                "object": label,
                "repetition": rep,
                "api_type": "REST",
                "response_time_s": round(rt, 6),
                "response_size_bytes": rs,
                "status_code": rcode,
                "timestamp": ts,
            })
        if gt is not None:
            records.append({
                "query_type": query_type,
                "object": label,
                "repetition": rep,
                "api_type": "GraphQL",
                "response_time_s": round(gt, 6),
                "response_size_bytes": gs,
                "status_code": gcode,
                "timestamp": ts,
            })

    return records


def main():
    parser = argparse.ArgumentParser(description="Collect GraphQL vs REST measurements.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run 2 reps on 2 repos only, to verify connectivity.")
    args = parser.parse_args()

    repos = REPOS[:2] if args.dry_run else REPOS
    n_reps = 2 if args.dry_run else N_REPETITIONS

    print("GitHub GraphQL vs REST — Data Collector")
    print(f"  repos={len(repos)} | query_types={len(QUERY_TYPES)} | reps/pair={n_reps}")
    if args.dry_run:
        print("  [DRY RUN] — using 2 repos and 2 reps only")
    print()

    pairs = [(qt, owner, repo) for qt in QUERY_TYPES for owner, repo in repos]

    iterator = tqdm(pairs, desc="pairs", unit="pair") if HAS_TQDM else pairs
    all_records = []

    for qt, owner, repo in iterator:
        label = f"{owner}/{repo}"
        rest_path = REST_QUERY_URLS[qt](owner, repo)
        gql_query = GRAPHQL_QUERY_STRINGS[qt]
        gql_vars = {"owner": owner, "name": repo}

        if HAS_TQDM:
            iterator.set_postfix({"pair": f"{label}:{qt}"})
        else:
            print(f"  [{qt}] {label}")

        records = collect_pair(rest_path, gql_query, gql_vars, label, qt, n_reps)
        all_records.extend(records)

    df = pd.DataFrame(all_records)
    out = Path(__file__).parent / OUTPUT_FILE
    df.to_csv(out, index=False)
    print(f"\nSaved {len(df)} measurements → {out}")

    # Quick summary
    if not df.empty:
        print("\n--- Median summary ---")
        summary = df.groupby(["query_type", "api_type"]).agg(
            time_median=("response_time_s", "median"),
            size_median=("response_size_bytes", "median"),
            n=("response_time_s", "count"),
        ).round({"time_median": 4, "size_median": 0})
        print(summary.to_string())


if __name__ == "__main__":
    main()
