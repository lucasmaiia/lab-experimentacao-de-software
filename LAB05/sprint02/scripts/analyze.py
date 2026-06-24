#!/usr/bin/env python3
"""
analyze.py — GraphQL vs REST experiment analyzer + HTML report generator.

Usage:
    python analyze.py [--data PATH] [--output PATH]

Reads results.csv produced by collector.py and writes a self-contained HTML report.
"""

import argparse
import base64
import sys
from io import BytesIO
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


# ── Paths & Constants ─────────────────────────────────────────────────────────
HERE = Path(__file__).parent
DEFAULT_DATA   = HERE.parents[1] / "sprint01" / "scripts" / "results.csv"
DEFAULT_OUTPUT = HERE.parent / "report.html"

ALPHA            = 0.05
N_TESTS          = 8          # 4 query types × 2 RQs
BONFERRONI_ALPHA = ALPHA / N_TESTS   # 0.00625

QUERY_TYPES = ["repo_info", "issues", "pull_requests", "commits"]
QUERY_LABELS = {
    "repo_info":     "Repo Info",
    "issues":        "Issues",
    "pull_requests": "Pull Requests",
    "commits":       "Commits",
}
COLOR_REST    = "#E05C47"
COLOR_GRAPHQL = "#4E91D9"

sns.set_theme(style="whitegrid", font_scale=1.05)


# ── Data Loading & Validation ─────────────────────────────────────────────────
def load_and_validate(path: Path):
    if not path.exists():
        sys.exit(f"ERROR: data file not found at:\n  {path}\n\n"
                 "Run collector.py first to generate results.csv.")

    df = pd.read_csv(path)

    required = {"query_type", "object", "repetition", "api_type",
                "response_time_s", "response_size_bytes", "status_code"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"ERROR: CSV is missing columns: {missing}")

    n_total   = len(df)
    n_errors  = (df["status_code"] != 200).sum()
    n_missing = df[["response_time_s", "response_size_bytes"]].isna().any(axis=1).sum()

    df_clean = df[
        (df["status_code"] == 200) &
        df["response_time_s"].notna() &
        df["response_size_bytes"].notna()
    ].copy()

    validation = {
        "total_rows":    n_total,
        "error_rows":    n_errors,
        "missing_rows":  n_missing,
        "clean_rows":    len(df_clean),
        "repos":         df_clean["object"].nunique(),
        "query_types":   sorted(df_clean["query_type"].unique().tolist()),
        "api_types":     sorted(df_clean["api_type"].unique().tolist()),
    }
    return df_clean, validation


def build_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot to wide format: one row per (query_type, object, repetition)."""
    idx = ["query_type", "object", "repetition"]
    cols = ["response_time_s", "response_size_bytes"]

    rest    = df[df["api_type"] == "REST"   ].set_index(idx)[cols]
    graphql = df[df["api_type"] == "GraphQL"].set_index(idx)[cols]

    paired = rest.join(graphql, lsuffix="_rest", rsuffix="_graphql", how="inner").reset_index()
    paired["diff_time_s"]     = paired["response_time_s_rest"]     - paired["response_time_s_graphql"]
    paired["diff_size_bytes"] = paired["response_size_bytes_rest"] - paired["response_size_bytes_graphql"]
    return paired


# ── Statistical Analysis ──────────────────────────────────────────────────────
def rank_biserial_r(diffs: np.ndarray) -> float:
    """Rank-biserial correlation as effect size for Wilcoxon signed-rank."""
    d = diffs[~np.isnan(diffs)]
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(d))
    T_plus  = float(ranks[d > 0].sum())
    T_minus = float(ranks[d < 0].sum())
    return (T_plus - T_minus) / (len(d) * (len(d) + 1) / 2)


def wilcoxon_test(x: pd.Series, y: pd.Series, alternative: str) -> dict:
    """Wilcoxon signed-rank test on paired arrays x, y."""
    diffs  = (x - y).dropna().values
    n_valid = int(np.sum(diffs != 0))

    if len(diffs) < 10:
        return {"n": len(diffs), "n_valid": n_valid,
                "W": None, "p": None, "r": None, "reject": False}

    W, p = stats.wilcoxon(diffs, alternative=alternative)
    r    = rank_biserial_r(diffs)
    return {
        "n":       len(diffs),
        "n_valid": n_valid,
        "W":       float(W),
        "p":       float(p),
        "r":       float(r),
        "reject":  bool(p < BONFERRONI_ALPHA),
    }


def analyze_rq(paired: pd.DataFrame, metric: str, alternative: str) -> dict:
    col_r = f"response_{metric}_rest"
    col_g = f"response_{metric}_graphql"
    results = {}

    for qt, label in QUERY_LABELS.items():
        sub = paired[paired["query_type"] == qt]
        if sub.empty:
            continue
        t = wilcoxon_test(sub[col_r], sub[col_g], alternative)
        t["median_rest"]    = float(sub[col_r].median())
        t["median_graphql"] = float(sub[col_g].median())
        t["query_label"]    = label
        results[qt] = t

    # Overall (all query types combined)
    ov = wilcoxon_test(paired[col_r], paired[col_g], alternative)
    ov["median_rest"]    = float(paired[col_r].median())
    ov["median_graphql"] = float(paired[col_g].median())
    ov["query_label"]    = "Overall"
    results["_overall"] = ov

    return results


# ── Plotting ──────────────────────────────────────────────────────────────────
def _fig_to_b64(fig) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64


def plot_boxplots(df: pd.DataFrame, metric: str, ylabel: str, title: str) -> str:
    col = f"response_{metric}"
    palette = {"REST": COLOR_REST, "GraphQL": COLOR_GRAPHQL}
    fig, axes = plt.subplots(1, 4, figsize=(15, 5), sharey=False)

    for ax, qt in zip(axes, QUERY_TYPES):
        sub = df[df["query_type"] == qt]
        sns.boxplot(
            data=sub, x="api_type", y=col, palette=palette, ax=ax,
            order=["REST", "GraphQL"], width=0.5, linewidth=1.2,
            flierprops=dict(marker=".", markersize=3, alpha=0.4),
        )
        # Annotate medians
        for i, api in enumerate(["REST", "GraphQL"]):
            med = sub[sub["api_type"] == api][col].median()
            ax.text(i, med, f" {med:.3g}", va="center", ha="left", fontsize=8, color="#333")

        ax.set_title(QUERY_LABELS[qt], fontsize=10, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel(ylabel if qt == QUERY_TYPES[0] else "")

    fig.suptitle(title, fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _fig_to_b64(fig)


def plot_diff_hist(paired: pd.DataFrame, diff_col: str, xlabel: str, title: str) -> str:
    fig, axes = plt.subplots(1, 4, figsize=(15, 4), sharey=False)

    for ax, qt in zip(axes, QUERY_TYPES):
        d = paired[paired["query_type"] == qt][diff_col].dropna()
        ax.hist(d, bins=40, color=COLOR_GRAPHQL, edgecolor="white", alpha=0.8)
        ax.axvline(0,         color="red",    lw=1.5, linestyle="--", label="zero")
        ax.axvline(d.median(), color="orange", lw=1.5, linestyle="-",
                   label=f"med={d.median():.3g}")
        ax.set_title(QUERY_LABELS[qt], fontsize=10, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel("Contagem" if qt == QUERY_TYPES[0] else "")
        ax.legend(fontsize=7)

    fig.suptitle(title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    return _fig_to_b64(fig)


def plot_violin(df: pd.DataFrame, metric: str, ylabel: str, title: str) -> str:
    col = f"response_{metric}"
    palette = {"REST": COLOR_REST, "GraphQL": COLOR_GRAPHQL}
    fig, axes = plt.subplots(1, 4, figsize=(15, 5), sharey=False)

    for ax, qt in zip(axes, QUERY_TYPES):
        sub = df[df["query_type"] == qt]
        sns.violinplot(
            data=sub, x="api_type", y=col, palette=palette, ax=ax,
            order=["REST", "GraphQL"], inner="quartile", linewidth=0.8,
        )
        ax.set_title(QUERY_LABELS[qt], fontsize=10, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel(ylabel if qt == QUERY_TYPES[0] else "")

    fig.suptitle(title, fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    return _fig_to_b64(fig)


# ── HTML Helpers ──────────────────────────────────────────────────────────────
def _fmt_p(p) -> str:
    if p is None:
        return "N/A"
    if p < 0.001:
        return "< 0,001"
    return f"{p:.4f}".replace(".", ",")


def _effect_label(r) -> str:
    if r is None:
        return "N/A"
    a = abs(r)
    tag = "negligível" if a < 0.1 else "pequeno" if a < 0.3 else "médio" if a < 0.5 else "grande"
    return f"{r:.3f} ({tag})"


def _sig_badge(reject: bool, p) -> str:
    if p is None:
        return "—"
    if reject:
        return '<span class="sig-yes">✓ Sig.</span>'
    return '<span class="sig-no">✗ n.s.</span>'


def _results_table(rq_results: dict, unit: str) -> str:
    rows = []
    order = [qt for qt in QUERY_TYPES if qt in rq_results] + ["_overall"]
    for key in order:
        r = rq_results.get(key)
        if r is None:
            continue
        mr, mg = r["median_rest"], r["median_graphql"]
        ratio = (mg / mr * 100) if mr else float("nan")
        last = key == "_overall"
        style = ' class="overall-row"' if last else ""
        rows.append(f"""
        <tr{style}>
            <td><b>{r["query_label"]}</b></td>
            <td>{mr:,.2f} {unit}</td>
            <td>{mg:,.2f} {unit}</td>
            <td>{ratio:.1f}%</td>
            <td>{r["n"]}</td>
            <td>{"N/A" if r["W"] is None else f"{r['W']:.0f}"}</td>
            <td>{_fmt_p(r.get("p"))}</td>
            <td>{_effect_label(r.get("r"))}</td>
            <td>{_sig_badge(r.get("reject", False), r.get("p"))}</td>
        </tr>""")

    return f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Tipo de Consulta</th>
                <th>Mediana REST</th>
                <th>Mediana GraphQL</th>
                <th>GraphQL / REST</th>
                <th>n pares</th>
                <th>W</th>
                <th>p-valor</th>
                <th>Tamanho de efeito (r)</th>
                <th>α = {BONFERRONI_ALPHA:.5f}</th>
            </tr>
        </thead>
        <tbody>{"".join(rows)}</tbody>
    </table>"""


def _conclusion_rq1(results: dict) -> str:
    ov = results.get("_overall", {})
    if not ov.get("p"):
        return ""
    mr, mg = ov["median_rest"], ov["median_graphql"]
    direction = "GraphQL foi mais rápido" if mg < mr else "REST foi mais rápido"
    sig = "estatisticamente significativa" if ov["reject"] else "não estatisticamente significativa"
    return (
        f"No geral, respostas GraphQL apresentaram mediana de {mg:.4f}s vs REST {mr:.4f}s "
        f"({direction}). A diferença é <b>{sig}</b> após correção de Bonferroni "
        f"(p = {_fmt_p(ov['p'])}, α_adj = {BONFERRONI_ALPHA:.5f}). "
        f"Tamanho de efeito r = {ov.get('r', 0):.3f}."
    )


def _conclusion_rq2(results: dict) -> str:
    ov = results.get("_overall", {})
    if not ov.get("p"):
        return ""
    mr, mg = ov["median_rest"], ov["median_graphql"]
    ratio = mg / mr * 100 if mr else 0
    sig = "estatisticamente significativa" if ov["reject"] else "não estatisticamente significativa"
    return (
        f"No geral, respostas GraphQL apresentaram mediana de {mg:,.0f} bytes vs REST {mr:,.0f} bytes "
        f"(GraphQL representa {ratio:.1f}% do tamanho REST). "
        f"A diferença é <b>{sig}</b> após correção de Bonferroni "
        f"(p = {_fmt_p(ov['p'])}, α_adj = {BONFERRONI_ALPHA:.5f}). "
        f"Tamanho de efeito r = {ov.get('r', 0):.3f}."
    )


# ── Descriptive Stats Table ───────────────────────────────────────────────────
def _desc_table(df: pd.DataFrame, metric: str, unit: str) -> str:
    col = f"response_{metric}"
    rows = []
    for qt in QUERY_TYPES:
        for api in ["REST", "GraphQL"]:
            sub = df[(df["query_type"] == qt) & (df["api_type"] == api)][col]
            rows.append(f"""
            <tr>
                <td>{QUERY_LABELS[qt]}</td>
                <td><b>{api}</b></td>
                <td>{sub.count()}</td>
                <td>{sub.median():,.3f}</td>
                <td>{sub.mean():,.3f}</td>
                <td>{sub.std():,.3f}</td>
                <td>{sub.min():,.3f}</td>
                <td>{sub.max():,.3f}</td>
            </tr>""")

    return f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Tipo</th><th>API</th><th>n</th>
                <th>Mediana ({unit})</th><th>Média ({unit})</th>
                <th>DP ({unit})</th><th>Mín ({unit})</th><th>Máx ({unit})</th>
            </tr>
        </thead>
        <tbody>{"".join(rows)}</tbody>
    </table>"""


# ── Report Builder ────────────────────────────────────────────────────────────
def build_report(
    validation, paired, df,
    rq1_results, rq2_results,
    fig_time_box, fig_size_box,
    fig_time_vln, fig_size_vln,
    fig_time_diff, fig_size_diff,
) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    table_rq1  = _results_table(rq1_results, "s")
    table_rq2  = _results_table(rq2_results, "B")
    desc_time  = _desc_table(df, "time_s",   "s")
    desc_size  = _desc_table(df, "size_bytes", "B")
    concl_rq1  = _conclusion_rq1(rq1_results)
    concl_rq2  = _conclusion_rq2(rq2_results)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAB05 — GraphQL vs REST: Relatório Final</title>
<style>
  :root {{
    --rest:    #E05C47;
    --graphql: #4E91D9;
    --primary: #2c3e50;
  }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    max-width: 1080px; margin: 0 auto; padding: 28px 36px;
    color: #222; line-height: 1.7; font-size: 15px;
    background: #fff;
  }}
  h1 {{ font-size: 1.9rem; border-bottom: 3px solid var(--primary); padding-bottom: 10px; margin-bottom: 4px; }}
  h2 {{ font-size: 1.3rem; margin-top: 2.5rem; padding-left: 12px;
        border-left: 5px solid var(--graphql); color: var(--primary); }}
  h3 {{ font-size: 1.05rem; color: #444; margin-top: 1.4rem; }}
  .meta {{
    background: #f5f7fa; border-radius: 8px; padding: 12px 18px;
    margin: 14px 0 22px; font-size: .9rem; color: #555;
    display: flex; gap: 24px; flex-wrap: wrap;
  }}
  .meta span b {{ color: #333; }}
  .badge-rest    {{ background: var(--rest);    color: #fff; border-radius: 4px; padding: 2px 8px; font-size:.82rem; font-weight:600; }}
  .badge-graphql {{ background: var(--graphql); color: #fff; border-radius: 4px; padding: 2px 8px; font-size:.82rem; font-weight:600; }}
  .data-table {{ border-collapse: collapse; width: 100%; font-size: .85rem; margin: 14px 0 22px; }}
  .data-table th {{
    background: var(--primary); color: #fff; padding: 8px 11px;
    text-align: left; font-weight: 600; white-space: nowrap;
  }}
  .data-table td {{ border-bottom: 1px solid #e0e0e0; padding: 7px 11px; }}
  .data-table tr:nth-child(even) td {{ background: #f8f9fb; }}
  .data-table .overall-row td {{ font-weight: bold; background: #eef3fb !important; border-top: 2px solid var(--primary); }}
  .hyp {{
    background: #f9f9fb; border: 1px solid #d8dde6; border-radius: 8px;
    padding: 14px 20px; margin: 10px 0 16px;
  }}
  .hyp code {{ background: #e6eaf0; padding: 2px 7px; border-radius: 4px; font-size: .9rem; }}
  img.chart {{ max-width: 100%; border: 1px solid #dde; border-radius: 8px; margin: 12px 0; display: block; }}
  .conclusion {{
    background: #eef8ee; border-left: 5px solid #27ae60;
    padding: 12px 18px; border-radius: 0 8px 8px 0; margin: 14px 0;
  }}
  .warning {{
    background: #fffde7; border-left: 5px solid #f9a825;
    padding: 10px 16px; border-radius: 0 8px 8px 0; margin: 12px 0;
  }}
  .sig-yes {{ color: #1a7a35; font-weight: bold; }}
  .sig-no  {{ color: #b00020; font-weight: bold; }}
  pre.code-block {{
    background: #f5f7fa; border: 1px solid #dde; border-radius: 8px;
    padding: 14px 18px; font-size: .84rem; overflow-x: auto; line-height: 1.5;
  }}
  table.summ {{ border-collapse: collapse; font-size: .9rem; margin: 8px 0 16px; }}
  table.summ td, table.summ th {{ border: 1px solid #ccc; padding: 6px 12px; }}
  table.summ th {{ background: #eef0f3; color: #333; }}
  .val-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; max-width: 520px; }}
  .val-card {{ background: #f5f7fa; border-radius: 6px; padding: 10px 16px; font-size: .9rem; }}
  .val-card .num {{ font-size: 1.5rem; font-weight: bold; color: var(--primary); }}
  footer {{
    margin-top: 3rem; font-size: .82rem; color: #999;
    border-top: 1px solid #eee; padding-top: 14px;
  }}
  @media print {{ body {{ font-size: 13px; }} img.chart {{ max-width: 95%; }} }}
</style>
</head>
<body>

<h1>LAB05 — GraphQL vs REST: Relatório Final</h1>
<div class="meta">
  <span><b>Disciplina:</b> Laboratório de Experimentação de Software</span>
  <span><b>Curso:</b> Engenharia de Software — PUC Minas</span>
  <span><b>Gerado em:</b> {now}</span>
</div>

<!-- ═══════════════════════ 1. INTRODUÇÃO ════════════════════════════════════ -->
<h2>1. Introdução</h2>
<p>
A linguagem de consulta <b>GraphQL</b>, proposta pelo Facebook como alternativa às APIs REST,
permite que clientes solicitem exatamente os campos que precisam — eliminando o
<em>over-fetching</em> característico do modelo REST, onde endpoints retornam objetos
completos independentemente da necessidade do consumidor. Vários sistemas passaram a
oferecer ambas as abordagens simultaneamente, mas os benefícios mensuráveis da adoção
do GraphQL ainda carecem de evidência empírica sólida e sistematizada.
</p>
<p>Este experimento controlado busca responder objetivamente:</p>
<ul>
  <li><b>RQ1:</b> Respostas a consultas GraphQL são mais <em>rápidas</em> que respostas a consultas REST?</li>
  <li><b>RQ2:</b> Respostas a consultas GraphQL têm <em>tamanho menor</em> que respostas a consultas REST?</li>
</ul>

<h3>Hipóteses</h3>
<div class="hyp">
  <b>RQ1 — Tempo de Resposta (teste bicaudal)</b><br>
  <b>H₀¹:</b> <code>mediana(T<sub>GraphQL</sub>) = mediana(T<sub>REST</sub>)</code><br>
  <b>H₁¹:</b> <code>mediana(T<sub>GraphQL</sub>) ≠ mediana(T<sub>REST</sub>)</code>
</div>
<div class="hyp">
  <b>RQ2 — Tamanho da Resposta (teste unicaudal)</b><br>
  <b>H₀²:</b> <code>mediana(S<sub>GraphQL</sub>) ≥ mediana(S<sub>REST</sub>)</code><br>
  <b>H₁²:</b> <code>mediana(S<sub>GraphQL</sub>) &lt; mediana(S<sub>REST</sub>)</code>
</div>

<!-- ═══════════════════════ 2. METODOLOGIA ══════════════════════════════════ -->
<h2>2. Metodologia</h2>

<h3>Plataforma e Objetos Experimentais</h3>
<p>
A <b>API pública do GitHub</b> foi escolhida por disponibilizar simultaneamente REST (v3)
e GraphQL (v4) sobre os mesmos dados, garantindo comparabilidade direta. Foram
selecionados <b>20 repositórios populares</b>, diversificados por linguagem e domínio:
<em>facebook/react, vuejs/vue, angular/angular, tensorflow/tensorflow, microsoft/vscode,
flutter/flutter, kubernetes/kubernetes, golang/go, django/django, rails/rails,
nodejs/node, rust-lang/rust, expressjs/express, pallets/flask, tiangolo/fastapi,
spring-projects/spring-boot, laravel/laravel, pytorch/pytorch,
scikit-learn/scikit-learn, hashicorp/terraform</em>.
</p>

<h3>Tratamentos e Equivalência de Consultas</h3>
<table class="summ">
  <tr><th>Tipo</th><th>Endpoint REST</th><th>GraphQL (campos selecionados)</th></tr>
  <tr><td><b>repo_info</b></td>
      <td>GET /repos/&#123;owner&#125;/&#123;repo&#125; (~60 campos)</td>
      <td>RepoInfo — 13 campos semânticos</td></tr>
  <tr><td><b>issues</b></td>
      <td>GET /repos/.../issues?per_page=20 (~35 campos/item)</td>
      <td>RepoIssues — 8 campos/item × 20</td></tr>
  <tr><td><b>pull_requests</b></td>
      <td>GET /repos/.../pulls?per_page=20 (~40 campos/item)</td>
      <td>RepoPRs — 8 campos/item × 20</td></tr>
  <tr><td><b>commits</b></td>
      <td>GET /repos/.../commits?per_page=20 (~20 campos/item)</td>
      <td>RepoCommits — 6 campos/item × 20</td></tr>
</table>

<h3>Desenho Experimental</h3>
<p>
<b>Tipo:</b> Experimento controlado <em>within-subjects</em> com medidas repetidas.
Os mesmos 20 repositórios foram submetidos a ambos os tratamentos (REST e GraphQL),
eliminando a variância inter-objeto como fator de confusão e aumentando o poder estatístico.<br>
<b>Randomização:</b> A ordem REST→GraphQL foi sorteada aleatoriamente (50/50) em cada
repetição para controlar efeitos de cache e sequenciamento.<br>
<b>Warm-up:</b> 2 repetições iniciais por par foram descartadas para eliminar efeitos de
cold-start (estabelecimento de conexão TCP, resolução DNS, etc.).<br>
<b>Volume:</b> 20 repositórios × 4 tipos × 30 repetições × 2 APIs = <b>4.800 medições válidas esperadas</b>.
</p>

<h3>Medição das Variáveis Dependentes</h3>
<ul>
  <li><b>Tempo de resposta (s):</b> <code>time.perf_counter()</code> antes e após o recebimento
      completo da resposta HTTP.</li>
  <li><b>Tamanho da resposta (bytes):</b> <code>len(response.content)</code> — comprimento do
      corpo bruto antes de qualquer descompressão adicional no cliente.</li>
</ul>

<h3>Testes Estatísticos</h3>
<p>
Utilizou-se o <b>Teste de Wilcoxon Pareado</b> (signed-rank), não-paramétrico e adequado
para dados de tempo de resposta com distribuição assimétrica e cauda longa.
Para controle do erro tipo I em múltiplos testes (4 tipos × 2 métricas = <b>{N_TESTS} comparações</b>),
aplicou-se a <b>correção de Bonferroni</b>: <code>α_adj = 0,05 / {N_TESTS} = {BONFERRONI_ALPHA:.5f}</code>.
</p>
<p>
O tamanho de efeito reportado é a <b>correlação rank-biserial</b>
<em>r</em> = (T⁺ − T⁻) / [n(n+1)/2], interpretada como:
|r| &lt; 0,1 = negligível; 0,1–0,3 = pequeno; 0,3–0,5 = médio; &gt;0,5 = grande.
</p>

<h3>Ambiente de Execução</h3>
<p>
As medições foram realizadas a partir de uma máquina cliente com conexão doméstica à
internet via protocolo HTTPS. Biblioteca cliente: Python <code>requests</code>. O cabeçalho
<code>Cache-Control: no-cache, no-store</code> foi enviado em todas as requisições.
O script aguardou automaticamente em caso de rate limiting da API do GitHub
(headers <code>X-RateLimit-Reset</code>).
</p>

<h3>Como Reproduzir</h3>
<pre class="code-block">
# 1. Configurar token GitHub (escopo: leitura de repos públicos)
cp LAB05/sprint01/.env.example LAB05/sprint01/.env
# Editar .env e preencher GITHUB_TOKEN

# 2. Coletar dados (~45 minutos, ~5.120 requisições)
cd LAB05/sprint01/scripts
pip install -r requirements.txt
python collector.py

# 3. Analisar resultados e gerar este relatório
cd LAB05/sprint02/scripts
pip install -r requirements.txt
python analyze.py
# Saída: LAB05/sprint02/report.html
</pre>

<!-- ═══════════════════════ 3. VALIDAÇÃO DOS DADOS ══════════════════════════ -->
<h2>3. Validação dos Dados</h2>
<div class="val-grid">
  <div class="val-card"><div class="num">{validation["total_rows"]}</div>Total de medições</div>
  <div class="val-card"><div class="num" style="color:#c0392b">{validation["error_rows"]}</div>Erros HTTP (descartados)</div>
  <div class="val-card"><div class="num">{validation["clean_rows"]}</div>Medições válidas usadas</div>
  <div class="val-card"><div class="num">{validation["repos"]}</div>Repositórios únicos</div>
</div>
{"" if validation["error_rows"] == 0 else '<div class="warning">⚠ Algumas requisições retornaram erro (status ≠ 200) e foram descartadas da análise. Verifique errors.log para detalhes.</div>'}

<h3>Estatísticas Descritivas — Tempo de Resposta</h3>
{desc_time}
<h3>Estatísticas Descritivas — Tamanho da Resposta</h3>
{desc_size}

<!-- ═══════════════════════ 4. RESULTADOS ══════════════════════════════════ -->
<h2>4. Resultados</h2>

<h3>RQ1 — Tempo de Resposta</h3>
<img class="chart" src="data:image/png;base64,{fig_time_box}" alt="Box plots — Tempo de Resposta">
<img class="chart" src="data:image/png;base64,{fig_time_vln}" alt="Violin plots — Tempo de Resposta">
<img class="chart" src="data:image/png;base64,{fig_time_diff}" alt="Distribuição das Diferenças de Tempo">
{table_rq1}
<div class="conclusion"><b>Conclusão RQ1:</b> {concl_rq1}</div>

<h3>RQ2 — Tamanho da Resposta</h3>
<img class="chart" src="data:image/png;base64,{fig_size_box}" alt="Box plots — Tamanho da Resposta">
<img class="chart" src="data:image/png;base64,{fig_size_vln}" alt="Violin plots — Tamanho da Resposta">
<img class="chart" src="data:image/png;base64,{fig_size_diff}" alt="Distribuição das Diferenças de Tamanho">
{table_rq2}
<div class="conclusion"><b>Conclusão RQ2:</b> {concl_rq2}</div>

<!-- ═══════════════════════ 5. DISCUSSÃO ════════════════════════════════════ -->
<h2>5. Discussão</h2>

<h3>RQ1 — Tempo de Resposta</h3>
<p>
A comparação dos tempos de resposta reflete o efeito combinado de dois fatores opostos:
o GraphQL retorna <em>menos dados</em> (menor volume de transferência pela rede), mas o
servidor precisa <em>parsear a query</em> e resolver o grafo de objetos — um overhead de
processamento inexistente no modelo REST. O resultado líquido depende de qual fator
domina em cada cenário de uso.
</p>
<p>
Para consultas simples de metadados (<code>repo_info</code>), onde a query GraphQL é
pequena e o ganho de transferência é substancial (13 vs ~60 campos), a redução de
payload pode se traduzir em menor tempo de transferência. Para listas com muitos itens
(<code>issues</code>, <code>pull_requests</code>), o overhead de resolução do grafo no
servidor pode compensar ou até superar o ganho de rede.
</p>
<p>
Diferenças pequenas ou não significativas no tempo são esperadas e alinhadas com a
literatura: a vantagem do GraphQL em tempo tende a ser mais pronunciada em redes com
largura de banda limitada, não em conexões de alta velocidade com servidores de
infraestrutura como o GitHub.
</p>

<h3>RQ2 — Tamanho da Resposta</h3>
<p>
A redução de tamanho com GraphQL reflete diretamente a seleção de campos: enquanto o
REST retorna objetos completos (incluindo URLs internas, permissões, metadados de
paginação, etc.), o GraphQL retorna apenas os campos explicitamente solicitados na
<em>query</em>. A diferença percentual esperada varia por tipo de consulta:
<code>repo_info</code> apresenta a maior redução (13 vs ~60 campos), enquanto
<code>commits</code> apresenta a menor (6 vs ~20 campos por item).
</p>
<p>
A compressão gzip habitual na API do GitHub reduz o impacto no nível de transporte,
mas o ganho semântico permanece: menos campos processados pelo cliente e menos memória
consumida no parsing.
</p>

<h3>Ameaças à Validade e Limitações</h3>
<ul>
  <li><b>Especificidade de plataforma:</b> Os resultados são válidos para a API do GitHub;
  outras implementações de GraphQL/REST podem ter perfis de desempenho diferentes
  (implementações customizadas tendem a ser mais leves que a infraestrutura global do GitHub).</li>
  <li><b>Variação de rede:</b> A latência cliente-servidor varia ao longo do tempo. A
  randomização da ordem e as medidas repetidas minimizam o viés, mas não eliminam
  completamente o ruído de rede.</li>
  <li><b>Seleção de campos GraphQL:</b> A escolha de quais campos solicitar afeta
  diretamente o tamanho e, indiretamente, o tempo. As queries foram calibradas para
  representar um uso típico — campos semanticamente equivalentes ao que um cliente
  extrairia da resposta REST.</li>
  <li><b>Tipo de operação:</b> Apenas operações de leitura simples foram testadas.
  Mutations e queries com múltiplos níveis de relacionamento podem apresentar
  diferenças mais pronunciadas.</li>
</ul>

<h3>Implicações Práticas</h3>
<p>
Para sistemas com restrições de largura de banda ou alto volume de requisições de
leitura, a <b>redução de tamanho do GraphQL tem valor direto e mensurável</b>.
Quanto ao tempo de resposta, a decisão entre GraphQL e REST deve considerar também a
complexidade da implementação do servidor, os custos de operação e a curva de
aprendizado das queries.
</p>

<!-- ═══════════════════════ REFERÊNCIAS ════════════════════════════════════ -->
<h2>Referências</h2>
<ul>
  <li>GitHub REST API v3 — <a href="https://docs.github.com/en/rest" target="_blank">docs.github.com/en/rest</a></li>
  <li>GitHub GraphQL API v4 — <a href="https://docs.github.com/en/graphql" target="_blank">docs.github.com/en/graphql</a></li>
  <li>Wilcoxon, F. (1945). Individual comparisons by ranking methods. <em>Biometrics Bulletin</em>, 1(6), 80–83.</li>
  <li>Hollander, M., &amp; Wolfe, D. A. (1973). <em>Nonparametric Statistical Methods</em>. Wiley.</li>
  <li>Wohlin, C. et al. (2012). <em>Experimentation in Software Engineering</em>. Springer.</li>
</ul>

<footer>
  LAB05 — GraphQL vs REST &nbsp;|&nbsp; Laboratório de Experimentação de Software &nbsp;|&nbsp;
  Engenharia de Software — PUC Minas &nbsp;|&nbsp; Junho de 2026
</footer>
</body>
</html>"""


# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Analyze GraphQL vs REST experiment data and generate HTML report."
    )
    parser.add_argument("--data",   type=Path, default=DEFAULT_DATA,
                        help=f"Path to results.csv (default: {DEFAULT_DATA})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output HTML path (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    print(f"[1/6] Loading data from:\n      {args.data}")
    df, validation = load_and_validate(args.data)
    print(f"      {validation['clean_rows']} valid rows | {validation['repos']} repos | "
          f"{validation['error_rows']} errors discarded")

    print("[2/6] Building paired dataset...")
    paired = build_pairs(df)
    print(f"      {len(paired)} pairs (REST+GraphQL matched by query_type, object, repetition)")

    print("[3/6] Running Wilcoxon signed-rank tests...")
    rq1_results = analyze_rq(paired, "time_s",     alternative="two-sided")
    rq2_results = analyze_rq(paired, "size_bytes", alternative="greater")

    print("[4/6] Generating plots...")
    fig_time_box  = plot_boxplots(df,     "time_s",     "Tempo (s)",    "RQ1 — Tempo de Resposta por Tipo de Consulta")
    fig_size_box  = plot_boxplots(df,     "size_bytes", "Tamanho (B)",  "RQ2 — Tamanho da Resposta por Tipo de Consulta")
    fig_time_vln  = plot_violin(df,       "time_s",     "Tempo (s)",    "RQ1 — Distribuição do Tempo (violin)")
    fig_size_vln  = plot_violin(df,       "size_bytes", "Tamanho (B)",  "RQ2 — Distribuição do Tamanho (violin)")
    fig_time_diff = plot_diff_hist(paired, "diff_time_s",     "REST − GraphQL (s)", "Diferenças de Tempo por Par (REST − GraphQL)")
    fig_size_diff = plot_diff_hist(paired, "diff_size_bytes", "REST − GraphQL (B)", "Diferenças de Tamanho por Par (REST − GraphQL)")

    print("[5/6] Building HTML report...")
    html = build_report(
        validation, paired, df,
        rq1_results, rq2_results,
        fig_time_box, fig_size_box,
        fig_time_vln, fig_size_vln,
        fig_time_diff, fig_size_diff,
    )

    print(f"[6/6] Writing report to:\n      {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"\nReport ready: {args.output}")

    # ── Text summary ──
    print("\n" + "=" * 64)
    print(f"STATISTICAL SUMMARY  (Bonferroni alpha = {BONFERRONI_ALPHA:.5f})")
    print("=" * 64)
    for rq_label, results in [("RQ1 — Tempo (s)", rq1_results),
                               ("RQ2 — Tamanho (B)", rq2_results)]:
        print(f"\n{rq_label}:")
        print(f"  {'Query':<16} {'Med REST':>10} {'Med GQL':>10} {'p-valor':>10} {'r':>7} {'sig?':>6}")
        print(f"  {'-'*16} {'-'*10} {'-'*10} {'-'*10} {'-'*7} {'-'*6}")
        order = [qt for qt in QUERY_TYPES if qt in results] + ["_overall"]
        for key in order:
            r = results.get(key)
            if not r:
                continue
            p_str   = _fmt_p(r.get("p"))
            r_str   = f"{r.get('r', 0):.3f}" if r.get("r") is not None else "N/A"
            sig_str = "SIG" if r.get("reject") else "n.s."
            print(f"  {r['query_label']:<16} {r['median_rest']:>10.2f} {r['median_graphql']:>10.2f} "
                  f"{p_str:>10} {r_str:>7} {sig_str:>6}")


if __name__ == "__main__":
    main()
