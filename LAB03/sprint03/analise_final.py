"""
Análise Final - Lab03 Sprint 03
Gera visualizações refinadas para o relatório final.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

SPRINT03_DIR = Path(__file__).resolve().parent
SPRINT02_DIR = SPRINT03_DIR.parent / "sprint02"
DATA_CSV = SPRINT02_DIR / "pull_requests.csv"
CORR_CSV = SPRINT02_DIR / "resultados_correlacoes.csv"
FIGURES_DIR = SPRINT03_DIR / "figuras"
FIGURES_DIR.mkdir(exist_ok=True)

COLOR_MERGED = "#1976D2"
COLOR_CLOSED = "#D32F2F"

LABEL_MAP = {
    "files_changed":       "Arquivos alterados",
    "additions":           "Linhas adicionadas",
    "deletions":           "Linhas removidas",
    "analysis_time_hours": "Tempo de análise",
    "body_char_count":     "Tam. da descrição",
    "participants_count":  "Participantes",
    "comments_count":      "Comentários",
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV)
    df = df.dropna(subset=["state", "analysis_time_hours"])
    df["merged"] = (df["state"] == "MERGED").astype(int)
    print(f"Dataset: {len(df):,} PRs ({df['merged'].sum():,} MERGED, {(~df['merged'].astype(bool)).sum():,} CLOSED)")
    print(f"Repositórios únicos: {df['repo_name'].nunique()}")
    return df


def figura1_distribuicao(df: pd.DataFrame) -> None:
    """Figura 1 - Distribuição geral do dataset."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    counts = df["state"].value_counts()
    axes[0].pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        colors=[COLOR_MERGED, COLOR_CLOSED],
        startangle=90,
        textprops={"fontsize": 13},
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
    )
    axes[0].set_title(f"Distribuição por Status\n(n = {len(df):,} PRs)", fontsize=12, fontweight="bold")

    top_repos = df.groupby("repo_name").size().sort_values(ascending=True).tail(20)
    short = [r.split("/")[-1] for r in top_repos.index]
    axes[1].barh(range(len(top_repos)), top_repos.values, color=COLOR_MERGED, alpha=0.75)
    axes[1].set_yticks(range(len(top_repos)))
    axes[1].set_yticklabels(short, fontsize=7)
    axes[1].set_xlabel("Número de PRs coletados", fontsize=10)
    axes[1].set_title("Top 20 Repositórios por Volume de PRs", fontsize=12, fontweight="bold")
    axes[1].grid(axis="x", alpha=0.3)

    plt.tight_layout()
    path = FIGURES_DIR / "figura1_distribuicao.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Salvo: {path}")


def _boxplot_grid(df: pd.DataFrame, pairs: list, title: str, path) -> None:
    """Renderiza um grid 2×2 de boxplots com escala logarítmica."""
    merged_data = df[df["state"] == "MERGED"]
    closed_data = df[df["state"] == "CLOSED"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes_flat = axes.flatten()

    for ax, (col, subplot_title, ylabel) in zip(axes_flat, pairs):
        # Remove zeros para não quebrar a escala log
        m_vals = merged_data[col].dropna()
        c_vals = closed_data[col].dropna()
        m_vals = m_vals[m_vals > 0]
        c_vals = c_vals[c_vals > 0]

        bp = ax.boxplot(
            [m_vals, c_vals],
            tick_labels=["MERGED", "CLOSED"],
            showfliers=False,
            patch_artist=True,
            medianprops={"color": "black", "linewidth": 2},
            whiskerprops={"linewidth": 1.2},
            boxprops={"linewidth": 1.2},
        )
        bp["boxes"][0].set_facecolor(COLOR_MERGED + "55")
        bp["boxes"][1].set_facecolor(COLOR_CLOSED + "55")

        ax.set_yscale("log")
        ax.set_title(subplot_title, fontsize=11, fontweight="bold", pad=8)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.tick_params(axis="x", labelsize=10)
        ax.grid(axis="y", alpha=0.3, which="both")

        # Anotação das medianas
        for pos, vals, color in [(1, m_vals, COLOR_MERGED), (2, c_vals, COLOR_CLOSED)]:
            med = vals.median()
            ax.text(pos, med * 1.15, f"{med:.1f}", ha="center", va="bottom",
                    fontsize=8, color=color, fontweight="bold")

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Salvo: {path}")


def figura2a_tamanho_tempo(df: pd.DataFrame) -> None:
    """Figura 2a - Tamanho e Tempo (escala log)."""
    pairs = [
        ("files_changed",       "Arquivos alterados",  "Arquivos (log)"),
        ("additions",           "Linhas adicionadas",  "Linhas (log)"),
        ("deletions",           "Linhas removidas",    "Linhas (log)"),
        ("analysis_time_hours", "Tempo de análise",    "Horas (log)"),
    ]
    _boxplot_grid(
        df, pairs,
        title="Figura 2a - Tamanho e Tempo por Status do PR (escala logarítmica)",
        path=FIGURES_DIR / "figura2a_tamanho_tempo.png",
    )


def figura2b_descricao_interacoes(df: pd.DataFrame) -> None:
    """Figura 2b - Descrição e Interações (escala log)."""
    pairs = [
        ("body_char_count",    "Tamanho da descrição", "Caracteres (log)"),
        ("participants_count", "Participantes",        "Qtd (log)"),
        ("comments_count",     "Comentários",          "Qtd (log)"),
        ("review_count",       "Nº de revisões",       "Qtd (log)"),
    ]
    _boxplot_grid(
        df, pairs,
        title="Figura 2b - Descrição e Interações por Status do PR (escala logarítmica)",
        path=FIGURES_DIR / "figura2b_descricao_interacoes.png",
    )


def figura3_correlacoes_dim_a(df_r: pd.DataFrame) -> None:
    """Figura 3 - Correlações de Spearman - Dimensão A (status)."""
    dim_a = df_r[df_r["vs"] == "merged"].copy()
    dim_a["metrica_label"] = dim_a["metrica"].map(LABEL_MAP).fillna(dim_a["metrica"])
    dim_a = dim_a.sort_values("r_spearman")

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [COLOR_MERGED if r >= 0 else COLOR_CLOSED for r in dim_a["r_spearman"]]
    bars = ax.barh(dim_a["metrica_label"], dim_a["r_spearman"], color=colors, alpha=0.8)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Coeficiente de Spearman (ρ)", fontsize=11)
    ax.set_title(
        "Dimensão A: Correlações com Status do PR\n(MERGED = 1, CLOSED = 0)",
        fontsize=12, fontweight="bold",
    )
    ax.grid(axis="x", alpha=0.3)

    for bar, (_, row) in zip(bars, dim_a.iterrows()):
        x = row["r_spearman"]
        offset = 0.003 if x >= 0 else -0.003
        ha = "left" if x >= 0 else "right"
        ax.text(x + offset, bar.get_y() + bar.get_height() / 2,
                f"ρ = {x:+.4f}  ({row['rq']})", va="center", ha=ha, fontsize=8)

    ax.set_xlim(-0.25, 0.18)
    plt.tight_layout()
    path = FIGURES_DIR / "figura3_correlacoes_dim_a.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Salvo: {path}")


def figura4_correlacoes_dim_b(df_r: pd.DataFrame) -> None:
    """Figura 4 - Correlações de Spearman - Dimensão B (revisões)."""
    dim_b = df_r[df_r["vs"] == "review_count"].copy()
    dim_b["metrica_label"] = dim_b["metrica"].map(LABEL_MAP).fillna(dim_b["metrica"])
    dim_b = dim_b.sort_values("r_spearman")

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(dim_b["metrica_label"], dim_b["r_spearman"], color="#43A047", alpha=0.8)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Coeficiente de Spearman (ρ)", fontsize=11)
    ax.set_title(
        "Dimensão B: Correlações com Número de Revisões",
        fontsize=12, fontweight="bold",
    )
    ax.grid(axis="x", alpha=0.3)

    for bar, (_, row) in zip(bars, dim_b.iterrows()):
        x = row["r_spearman"]
        ax.text(x + 0.005, bar.get_y() + bar.get_height() / 2,
                f"ρ = {x:+.4f}  ({row['rq']})", va="center", ha="left", fontsize=8)

    ax.set_xlim(0, 0.5)
    plt.tight_layout()
    path = FIGURES_DIR / "figura4_correlacoes_dim_b.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Salvo: {path}")


def figura5_heatmap(df_r: pd.DataFrame) -> None:
    """Figura 5 - Heatmap de todos os coeficientes de Spearman."""
    df_r2 = df_r.copy()
    df_r2["metrica_label"] = df_r2["metrica"].map(LABEL_MAP).fillna(df_r2["metrica"])
    pivot = df_r2.pivot(index="metrica_label", columns="rq", values="r_spearman")

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(
        pivot, annot=True, fmt=".3f", cmap="RdBu_r", center=0,
        linewidths=0.5, ax=ax, vmin=-0.45, vmax=0.45,
        annot_kws={"size": 9},
    )
    ax.set_title(
        "Coeficientes de Correlação de Spearman - RQ01 a RQ08\n"
        "(todos os resultados: p < 0,001 ***)",
        fontsize=12, fontweight="bold",
    )
    ax.set_xlabel("Questão de Pesquisa", fontsize=11)
    ax.set_ylabel("Métrica Independente", fontsize=11)
    plt.tight_layout()
    path = FIGURES_DIR / "figura5_heatmap_correlacoes.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Salvo: {path}")


def main() -> None:
    print("=" * 60)
    print("Análise Final - Lab03 Sprint 03")
    print("=" * 60)
    df = load_data()
    df_r = pd.read_csv(CORR_CSV)

    print("\nGerando figuras...")
    figura1_distribuicao(df)
    figura2a_tamanho_tempo(df)
    figura2b_descricao_interacoes(df)
    figura3_correlacoes_dim_a(df_r)
    figura4_correlacoes_dim_b(df_r)
    figura5_heatmap(df_r)
    print(f"\nConcluído! Figuras em: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
