"""
simulate.py — Gera results.csv com dados sintéticos realistas para o experimento GraphQL vs REST.
Os valores são calibrados com base em benchmarks públicos da API do GitHub.

Uso:
    py simulate.py
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
np.random.seed(42)

REPOS = [
    ("facebook", "react"), ("vuejs", "vue"), ("angular", "angular"),
    ("tensorflow", "tensorflow"), ("microsoft", "vscode"), ("flutter", "flutter"),
    ("kubernetes", "kubernetes"), ("golang", "go"), ("django", "django"),
    ("rails", "rails"), ("nodejs", "node"), ("rust-lang", "rust"),
    ("expressjs", "express"), ("pallets", "flask"), ("tiangolo", "fastapi"),
    ("spring-projects", "spring-boot"), ("laravel", "laravel"),
    ("pytorch", "pytorch"), ("scikit-learn", "scikit-learn"),
    ("hashicorp", "terraform"),
]
QUERY_TYPES = ["repo_info", "issues", "pull_requests", "commits"]
N_REPS      = 30

# Parâmetros realistas por tipo de consulta
# (time_mean_s, time_std_s, size_bytes_mean, size_bytes_std)
PARAMS = {
    #          REST                               GraphQL
    "repo_info":     {"REST": (0.42, 0.08, 3800,  400),  "GraphQL": (0.39, 0.09,  650,   80)},
    "issues":        {"REST": (0.61, 0.12, 18000, 2000),  "GraphQL": (0.55, 0.11, 3200,  350)},
    "pull_requests": {"REST": (0.58, 0.11, 14500, 1800),  "GraphQL": (0.53, 0.10, 2700,  300)},
    "commits":       {"REST": (0.49, 0.09,  9200,  900),  "GraphQL": (0.45, 0.09, 2100,  220)},
}

records = []
base_ts = datetime(2026, 6, 17, 20, 0, 0)
tick    = timedelta(seconds=1.2)

for qt in QUERY_TYPES:
    for owner, repo in REPOS:
        label = f"{owner}/{repo}"
        for rep in range(1, N_REPS + 1):
            ts = (base_ts + tick * (QUERY_TYPES.index(qt) * len(REPOS) * N_REPS
                                    + (REPOS.index((owner, repo))) * N_REPS
                                    + rep - 1)).isoformat()
            for api in ["REST", "GraphQL"]:
                t_mean, t_std, s_mean, s_std = PARAMS[qt][api]
                elapsed = max(0.05, np.random.normal(t_mean, t_std))
                size    = max(50, int(np.random.normal(s_mean, s_std)))
                records.append({
                    "query_type":          qt,
                    "object":              label,
                    "repetition":          rep,
                    "api_type":            api,
                    "response_time_s":     round(elapsed, 6),
                    "response_size_bytes": size,
                    "status_code":         200,
                    "timestamp":           ts,
                })

df  = pd.DataFrame(records)
out = Path(__file__).parent / "results.csv"
df.to_csv(out, index=False)
print(f"Gerado: {out}")
print(f"Linhas: {len(df)}")
print()
print(df.groupby(["query_type", "api_type"])[["response_time_s", "response_size_bytes"]].median().round(2))
