"""
GraphQL vs REST — Data Collector
Measures response time and response size for equivalent queries on both APIs.

Usage:
    py collector.py                        # coleta completa (20 repos, 30 reps)
    py collector.py --workers 3            # 3 pares em paralelo (~3x mais rapido)
    py collector.py --dry-run              # 2 repos, 2 reps, verifica conectividade
    py collector.py --num-repos 10         # limita a 10 repositorios
    py collector.py --num-reps 15          # limita a 15 repeticoes por par
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import threading
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
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

load_dotenv(dotenv_path=Path(__file__).parents[1] / ".env", override=True)
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

# Rate limiter global: garante no maximo MAX_RPS requisicoes/segundo entre todas as threads
_rate_lock = threading.Lock()
_last_request_time = 0.0
MAX_RPS = 1.2  # requisicoes por segundo por thread (conservador para 3 workers)


def _throttle():
    """Espacamento minimo entre requisicoes para nao exceder rate limit do GitHub."""
    global _last_request_time
    with _rate_lock:
        now = time.monotonic()
        gap = now - _last_request_time
        min_gap = 1.0 / MAX_RPS
        if gap < min_gap:
            time.sleep(min_gap - gap)
        _last_request_time = time.monotonic()


def _handle_rate_limit(response) -> bool:
    if response.status_code not in (403, 429):
        return False
    reset_ts = response.headers.get("X-RateLimit-Reset")
    wait = max(RETRY_WAIT, int(reset_ts) - int(time.time()) + 5) if reset_ts else RETRY_WAIT
    print(f"\n  [rate limit] sleeping {wait}s ...", flush=True)
    time.sleep(wait)
    return True


def measure_rest(path: str) -> tuple:
    url = f"{REST_BASE_URL}{path}"
    for attempt in range(MAX_RETRIES):
        try:
            _throttle()
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
    payload = json.dumps({"query": query, "variables": variables})
    for attempt in range(MAX_RETRIES):
        try:
            _throttle()
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
                 label: str, query_type: str, n_reps: int,
                 delay: float = DELAY_BETWEEN_REQUESTS) -> list:
    # Warm-up
    for _ in range(WARMUP_REPS):
        measure_rest(rest_path)
        time.sleep(delay)
        measure_graphql(gql_query, gql_vars)
        time.sleep(delay)

    records = []
    for rep in range(1, n_reps + 1):
        ts = datetime.now().isoformat()
        if random.random() < 0.5:
            rt, rs, rcode = measure_rest(rest_path)
            time.sleep(delay)
            gt, gs, gcode = measure_graphql(gql_query, gql_vars)
        else:
            gt, gs, gcode = measure_graphql(gql_query, gql_vars)
            time.sleep(delay)
            rt, rs, rcode = measure_rest(rest_path)
        time.sleep(delay)

        if rt is not None:
            records.append({
                "query_type": query_type, "object": label, "repetition": rep,
                "api_type": "REST", "response_time_s": round(rt, 6),
                "response_size_bytes": rs, "status_code": rcode, "timestamp": ts,
            })
        if gt is not None:
            records.append({
                "query_type": query_type, "object": label, "repetition": rep,
                "api_type": "GraphQL", "response_time_s": round(gt, 6),
                "response_size_bytes": gs, "status_code": gcode, "timestamp": ts,
            })
    return records


def _collect_pair_task(args):
    qt, owner, repo, n_reps, delay = args
    label = f"{owner}/{repo}"
    rest_path = REST_QUERY_URLS[qt](owner, repo)
    gql_query = GRAPHQL_QUERY_STRINGS[qt]
    gql_vars  = {"owner": owner, "name": repo}
    records   = collect_pair(rest_path, gql_query, gql_vars, label, qt, n_reps, delay)
    return label, qt, records


def main():
    parser = argparse.ArgumentParser(description="Collect GraphQL vs REST measurements.")
    parser.add_argument("--dry-run",   action="store_true",
                        help="2 repos, 2 reps — verifica conectividade.")
    parser.add_argument("--num-repos", type=int, default=None,
                        help="Limita aos N primeiros repositorios.")
    parser.add_argument("--num-reps",  type=int, default=None,
                        help="Repeticoes por par (padrao: config).")
    parser.add_argument("--workers",   type=int, default=1,
                        help="Pares em paralelo (1=sequencial, 3=rapido). Padrao: 1.")
    args = parser.parse_args()

    if args.dry_run:
        repos, n_reps, workers = REPOS[:2], 2, 1
    else:
        repos   = REPOS[:args.num_repos] if args.num_repos else REPOS
        n_reps  = args.num_reps if args.num_reps else N_REPETITIONS
        workers = max(1, min(args.workers, 4))

    # Com multiplos workers, reduz delay para nao atrasar desnecessariamente
    delay = DELAY_BETWEEN_REQUESTS if workers == 1 else max(0.2, DELAY_BETWEEN_REQUESTS / workers)

    pairs = [(qt, owner, repo) for qt in QUERY_TYPES for owner, repo in repos]
    total = len(pairs)

    print("GitHub GraphQL vs REST — Data Collector")
    print(f"  repos={len(repos)} | query_types={len(QUERY_TYPES)} | reps/pair={n_reps}")
    print(f"  workers={workers} | delay={delay:.2f}s | pares={total}")
    if args.dry_run:
        print("  [DRY RUN]")
    print()

    tasks = [(qt, owner, repo, n_reps, delay) for qt, owner, repo in pairs]
    all_records = []
    done = 0

    pbar = tqdm(total=total, desc="pairs", unit="pair") if HAS_TQDM else None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_collect_pair_task, t): t for t in tasks}
        for future in as_completed(futures):
            label, qt, records = future.result()
            all_records.extend(records)
            done += 1
            if pbar:
                pbar.update(1)
                pbar.set_postfix({"ultimo": f"{label}:{qt}", "medidas": len(all_records)})
            else:
                print(f"  [{done}/{total}] {label}:{qt} ({len(records)} medidas)")

    if pbar:
        pbar.close()

    df  = pd.DataFrame(all_records)
    out = Path(__file__).parent / OUTPUT_FILE
    df.to_csv(out, index=False)
    print(f"\nSalvo: {len(df)} medicoes -> {out}")

    if not df.empty:
        ok = (df["status_code"] == 200).sum()
        print(f"Status 200: {ok}/{len(df)} ({ok/len(df)*100:.1f}%)")
        print("\n--- Resumo de medianas ---")
        summary = df[df["status_code"] == 200].groupby(["query_type", "api_type"]).agg(
            time_median=("response_time_s", "median"),
            size_median=("response_size_bytes", "median"),
            n=("response_time_s", "count"),
        ).round({"time_median": 4, "size_median": 0})
        print(summary.to_string())


if __name__ == "__main__":
    main()
