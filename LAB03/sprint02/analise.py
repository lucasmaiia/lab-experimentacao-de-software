"""
Análise estatística do dataset de Pull Requests — Lab03 Sprint 02

Correlações de Spearman entre métricas de PR e:
  A) Status do PR (MERGED=1, CLOSED=0) — RQ01–04
  B) Número de revisões (review_count)   — RQ05–08

Justificativa do teste: Spearman é robusto para distribuições não-normais
e dados ordinais/assimétricos, que são típicos de métricas de repositórios
open-source (muitos PRs com valores baixos e cauda longa).
"""

import sys
from pathlib import Path

import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# ── Caminhos ───────────────────────────────────────────────────────────────────
SPRINT02_DIR = Path(__file__).resolve().parent
SPRINT01_CSV = SPRINT02_DIR.parent / "sprint01" / "pull_requests.csv"
SPRINT02_CSV = SPRINT02_DIR / "pull_requests.csv"
FIGURES_DIR = SPRINT02_DIR / "figuras"
FIGURES_DIR.mkdir(exist_ok=True)


def _load_data() -> pd.DataFrame:
    csv_path = SPRINT02_CSV if SPRINT02_CSV.exists() else SPRINT01_CSV
    if not csv_path.exists():
        sys.exit(f"CSV não encontrado: {csv_path}\nExecute coleta_prs.py primeiro.")
    print(f"Carregando dados de: {csv_path}")
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["state", "analysis_time_hours"])
    df["merged"] = (df["state"] == "MERGED").astype(int)
    print(f"  {len(df):,} PRs carregados  ({df['merged'].sum():,} MERGED, {(~df['merged'].astype(bool)).sum():,} CLOSED)")
    print(f"  Repositórios únicos: {df['repo_name'].nunique()}\n")
    return df


# ── Spearman + Mann-Whitney ────────────────────────────────────────────────────
def _spearman(x: pd.Series, y: pd.Series, label_x: str, label_y: str) -> dict:
    mask = x.notna() & y.notna()
    r, p = stats.spearmanr(x[mask], y[mask])
    return {"metrica": label_x, "vs": label_y, "r_spearman": round(r, 4), "p_valor": round(p, 6), "n": int(mask.sum())}


def _mann_whitney(df: pd.DataFrame, col: str) -> dict:
    merged_vals = df.loc[df["merged"] == 1, col].dropna()
    closed_vals  = df.loc[df["merged"] == 0, col].dropna()
    u, p = stats.mannwhitneyu(merged_vals, closed_vals, alternative="two-sided")
    return {
        "metrica": col,
        "mediana_merged": round(merged_vals.median(), 4),
        "mediana_closed": round(closed_vals.median(), 4),
        "p_mw": round(p, 6),
    }


# ── Medianas globais ───────────────────────────────────────────────────────────
def _print_medians(df: pd.DataFrame) -> None:
    cols = ["files_changed", "additions", "deletions", "analysis_time_hours",
            "body_char_count", "participants_count", "comments_count", "review_count"]
    print("=" * 60)
    print("MEDIANAS GLOBAIS")
    print("=" * 60)
    for c in cols:
        print(f"  {c:<28} {df[c].median():.2f}")
    print()


# ── Correlações ────────────────────────────────────────────────────────────────
SIZE_COLS = ["files_changed", "additions", "deletions"]

RQ_GROUPS = [
    # (rq_label, x_cols,                       y_col,       y_label)
    ("RQ01", SIZE_COLS,                         "merged",    "status (merged=1)"),
    ("RQ02", ["analysis_time_hours"],           "merged",    "status (merged=1)"),
    ("RQ03", ["body_char_count"],               "merged",    "status (merged=1)"),
    ("RQ04", ["participants_count",
              "comments_count"],               "merged",    "status (merged=1)"),
    ("RQ05", SIZE_COLS,                         "review_count", "nº revisões"),
    ("RQ06", ["analysis_time_hours"],           "review_count", "nº revisões"),
    ("RQ07", ["body_char_count"],               "review_count", "nº revisões"),
    ("RQ08", ["participants_count",
              "comments_count"],               "review_count", "nº revisões"),
]


def _print_correlations(df: pd.DataFrame) -> list:
    results = []
    print("=" * 60)
    print("CORRELAÇÕES DE SPEARMAN")
    print("=" * 60)
    for rq, x_cols, y_col, y_label in RQ_GROUPS:
        print(f"\n{rq} — vs {y_label}")
        for x in x_cols:
            res = _spearman(df[x], df[y_col], x, y_col)
            sig = "***" if res["p_valor"] < 0.001 else ("**" if res["p_valor"] < 0.01 else ("*" if res["p_valor"] < 0.05 else "n.s."))
            print(f"  {x:<28} r={res['r_spearman']:+.4f}  p={res['p_valor']:.6f}  {sig}  (n={res['n']:,})")
            results.append({**res, "rq": rq, "sig": sig})
    print()
    return results


def _print_mann_whitney(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("MANN-WHITNEY U (MERGED vs CLOSED)")
    print("=" * 60)
    cols = ["files_changed", "additions", "deletions", "analysis_time_hours",
            "body_char_count", "participants_count", "comments_count"]
    for c in cols:
        res = _mann_whitney(df, c)
        sig = "***" if res["p_mw"] < 0.001 else ("**" if res["p_mw"] < 0.01 else ("*" if res["p_mw"] < 0.05 else "n.s."))
        print(
            f"  {c:<28} med_M={res['mediana_merged']:>10.2f}  "
            f"med_C={res['mediana_closed']:>10.2f}  p={res['p_mw']:.6f}  {sig}"
        )
    print()


# ── Gráficos ───────────────────────────────────────────────────────────────────
def _plot_boxplots(df: pd.DataFrame) -> None:
    """Box plots de métricas-chave por status do PR."""
    pairs = [
        ("files_changed",       "Arquivos alterados",    "Arquivos"),
        ("analysis_time_hours", "Tempo de análise (h)",  "Horas"),
        ("body_char_count",     "Tamanho da descrição",  "Caracteres"),
        ("comments_count",      "Comentários",           "Qtd"),
        ("review_count",        "Nº de revisões",        "Qtd"),
    ]
    fig, axes = plt.subplots(1, len(pairs), figsize=(20, 5))
    for ax, (col, title, ylabel) in zip(axes, pairs):
        data = [
            df.loc[df["state"] == "MERGED", col].dropna(),
            df.loc[df["state"] == "CLOSED", col].dropna(),
        ]
        ax.boxplot(data, tick_labels=["MERGED", "CLOSED"], showfliers=False)
        ax.set_title(title, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle("Distribuição de métricas por status do PR (sem outliers)", fontsize=12)
    plt.tight_layout()
    path = FIGURES_DIR / "boxplots_status.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Salvo: {path}")


def _plot_scatter_reviews(df: pd.DataFrame) -> None:
    """Scatter plots de métricas vs nº de revisões (amostra)."""
    pairs = [
        ("files_changed",       "Arquivos alterados"),
        ("analysis_time_hours", "Tempo de análise (h)"),
        ("body_char_count",     "Tamanho da descrição"),
        ("comments_count",      "Comentários"),
    ]
    sample = df.sample(min(2000, len(df)), random_state=42)
    fig, axes = plt.subplots(1, len(pairs), figsize=(20, 5))
    for ax, (col, label) in zip(axes, pairs):
        ax.scatter(sample[col], sample["review_count"], alpha=0.2, s=10)
        ax.set_xlabel(label, fontsize=8)
        ax.set_ylabel("Nº revisões", fontsize=8)
        ax.set_title(f"{label} vs Revisões", fontsize=9)
    fig.suptitle("Métricas vs Número de revisões (amostra aleatória de 2 000 PRs)", fontsize=12)
    plt.tight_layout()
    path = FIGURES_DIR / "scatter_reviews.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Salvo: {path}")


def _plot_correlation_heatmap(results: list) -> None:
    """Heatmap dos coeficientes de Spearman por RQ."""
    df_r = pd.DataFrame(results)
    pivot = df_r.pivot(index="metrica", columns="rq", values="r_spearman")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="RdBu_r", center=0,
                linewidths=0.5, ax=ax, vmin=-1, vmax=1)
    ax.set_title("Coeficientes de Spearman — Lab03 Sprint 02", fontsize=12)
    plt.tight_layout()
    path = FIGURES_DIR / "heatmap_correlacoes.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Salvo: {path}")


# ── Salva CSV de resultados ────────────────────────────────────────────────────
def _save_results_csv(results: list, df: pd.DataFrame) -> None:
    out_path = SPRINT02_DIR / "resultados_correlacoes.csv"
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"  Salvo: {out_path}")

    out_med = SPRINT02_DIR / "medianas.csv"
    cols = ["files_changed", "additions", "deletions", "analysis_time_hours",
            "body_char_count", "participants_count", "comments_count", "review_count"]
    med_all   = df[cols].median().rename("mediana_geral")
    med_merged = df[df["merged"] == 1][cols].median().rename("mediana_merged")
    med_closed = df[df["merged"] == 0][cols].median().rename("mediana_closed")
    pd.concat([med_all, med_merged, med_closed], axis=1).to_csv(out_med)
    print(f"  Salvo: {out_med}")


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    df = _load_data()
    _print_medians(df)
    results = _print_correlations(df)
    _print_mann_whitney(df)

    print("=" * 60)
    print("GERANDO GRÁFICOS")
    print("=" * 60)
    _plot_boxplots(df)
    _plot_scatter_reviews(df)
    _plot_correlation_heatmap(results)
    _save_results_csv(results, df)
    print("\nAnálise concluída.")


if __name__ == "__main__":
    main()
