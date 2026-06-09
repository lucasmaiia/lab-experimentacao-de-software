REPOS = [
    ("facebook", "react"),
    ("vuejs", "vue"),
    ("angular", "angular"),
    ("tensorflow", "tensorflow"),
    ("microsoft", "vscode"),
    ("flutter", "flutter"),
    ("kubernetes", "kubernetes"),
    ("golang", "go"),
    ("django", "django"),
    ("rails", "rails"),
    ("nodejs", "node"),
    ("rust-lang", "rust"),
    ("expressjs", "express"),
    ("pallets", "flask"),
    ("tiangolo", "fastapi"),
    ("spring-projects", "spring-boot"),
    ("laravel", "laravel"),
    ("pytorch", "pytorch"),
    ("scikit-learn", "scikit-learn"),
    ("hashicorp", "terraform"),
]

QUERY_TYPES = ["repo_info", "issues", "pull_requests", "commits"]

N_REPETITIONS = 30
WARMUP_REPS = 2
DELAY_BETWEEN_REQUESTS = 0.5   # seconds between individual requests
MAX_RETRIES = 3
RETRY_WAIT = 65                 # seconds to wait when rate-limited

REST_BASE_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
OUTPUT_FILE = "results.csv"
ERROR_LOG_FILE = "errors.log"
