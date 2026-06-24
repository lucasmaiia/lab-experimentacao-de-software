"""
dashboard.py — LAB05 Sprint 03
GraphQL vs REST | Navegacao por abas com rolagem vertical.

Execucao:
    cd LAB05/sprint03
    py -m streamlit run dashboard.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from pathlib import Path
from scipy import stats

# ══ Configuracao da pagina ════════════════════════════════════════════════════
st.set_page_config(
    page_title="GraphQL vs REST",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  #MainMenu, footer, header { visibility: hidden; }
  .block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
  }
  .stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 2px solid #dee2e6;
    margin-top: 0.3rem;
  }
  .stTabs [data-baseweb="tab"] {
    height: 38px;
    padding: 0 22px;
    font-weight: 600;
    font-size: 0.88rem;
  }
  .stTabs [aria-selected="true"] {
    color: #4E91D9 !important;
    border-bottom: 3px solid #4E91D9 !important;
  }
  div[data-testid="metric-container"] {
    background: #f8f9fb;
    border: 1px solid #e4e8ef;
    border-radius: 8px;
    padding: 10px 14px;
  }
  hr { margin: 0.6rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ══ Constantes ════════════════════════════════════════════════════════════════
COLOR       = {"REST": "#E05C47", "GraphQL": "#4E91D9"}
ALPHA_ADJ   = 0.05 / 8
QUERY_ORDER = ["repo_info", "issues", "pull_requests", "commits"]
Q_LABEL     = {
    "repo_info":     "Repo Info",
    "issues":        "Issues",
    "pull_requests": "Pull Requests",
    "commits":       "Commits",
}

# ══ Funcoes de dados ══════════════════════════════════════════════════════════
@st.cache_data
def _load_raw() -> pd.DataFrame | None:
    path = Path(__file__).parents[1] / "sprint01" / "scripts" / "results.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["status_code"] == 200].copy()
    if df.empty:
        return None
    return df


@st.cache_data
def build_pairs(df: pd.DataFrame) -> pd.DataFrame:
    idx = ["query_type", "object", "repetition"]
    r = df[df["api_type"] == "REST"   ].set_index(idx)[["response_time_s", "response_size_bytes"]]
    g = df[df["api_type"] == "GraphQL"].set_index(idx)[["response_time_s", "response_size_bytes"]]
    return r.join(g, lsuffix="_rest", rsuffix="_graphql", how="inner").reset_index()


def _rank_biserial_r(x: pd.Series, y: pd.Series) -> float:
    diffs = (x - y).dropna()
    diffs = diffs[diffs != 0]
    n = len(diffs)
    if n == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(diffs))
    W_plus = float(np.sum(ranks[diffs.values > 0]))
    return (W_plus - n * (n + 1) / 4) / (n * (n + 1) / 4)


@st.cache_data
def wilcoxon_results(paired: pd.DataFrame, metric: str, alt: str, query_types: tuple) -> pd.DataFrame:
    cr, cg = f"response_{metric}_rest", f"response_{metric}_graphql"
    rows = []
    for qt in query_types:
        sub = paired[paired["query_type"] == qt]
        d   = (sub[cr] - sub[cg]).dropna().values
        if len(d) < 2:
            continue
        W, pv = stats.wilcoxon(d, alternative=alt)
        r_val = _rank_biserial_r(sub[cr], sub[cg])
        rows.append({
            "Consulta": Q_LABEL[qt], "n": len(d),
            "Med. REST": sub[cr].median(), "Med. GraphQL": sub[cg].median(),
            "W": int(W), "p": pv, "r": r_val, "sig": pv < ALPHA_ADJ,
        })
    d_all = (paired[cr] - paired[cg]).dropna().values
    if len(d_all) >= 2:
        W, pv  = stats.wilcoxon(d_all, alternative=alt)
        r_all  = _rank_biserial_r(paired[cr], paired[cg])
        rows.append({
            "Consulta": "Overall", "n": len(d_all),
            "Med. REST": paired[cr].median(), "Med. GraphQL": paired[cg].median(),
            "W": int(W), "p": pv, "r": r_all, "sig": pv < ALPHA_ADJ,
        })
    return pd.DataFrame(rows)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_p(v: float) -> str:
    return "< 0,001" if v < 0.001 else f"{v:.5f}".replace(".", ",")


def _layout(h=None, **kwargs):
    d = dict(margin=dict(l=4, r=4, t=40, b=4), height=h,
             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(size=12))
    d.update(kwargs)
    return d


def _dumbbell_size(s_wide, y_col, title, categories, h=340):
    fig = go.Figure()
    for _, row in s_wide.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["REST"], row["GraphQL"]], y=[row[y_col], row[y_col]],
            mode="lines", line=dict(color="#c8d3e0", width=2.5),
            showlegend=False, hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        x=s_wide["REST"], y=s_wide[y_col],
        mode="markers+text",
        marker=dict(size=15, color=COLOR["REST"], line=dict(width=1.5, color="white")),
        name="REST",
        text=s_wide["REST"].map("{:,.0f} B".format),
        textposition="bottom center", textfont_size=10,
    ))
    fig.add_trace(go.Scatter(
        x=s_wide["GraphQL"], y=s_wide[y_col],
        mode="markers+text",
        marker=dict(size=15, color=COLOR["GraphQL"], line=dict(width=1.5, color="white")),
        name="GraphQL",
        text=s_wide["GraphQL"].map("{:,.0f} B".format),
        textposition="top center", textfont_size=10,
    ))
    fig.update_layout(
        **_layout(h=h), title=title,
        xaxis=dict(title="bytes (escala log)", type="log"),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(categories))),
        legend=dict(orientation="h", y=1.12, x=0),
    )
    return fig


# ══ Carrega dados brutos ══════════════════════════════════════════════════════
df_raw = _load_raw()
if df_raw is None:
    st.error("Nenhuma medicao valida encontrada. Aguarde a coleta terminar e reinicie o servidor.")
    st.stop()

all_repos = sorted(df_raw["object"].unique().tolist())

# ══ Cabecalho + Filtros via popover ══════════════════════════════════════════
hcol, fcol = st.columns([9, 1])
with hcol:
    st.markdown(
        "<div style='padding:2px 0 6px'>"
        "<span style='font-size:1.2rem;font-weight:700'>GraphQL vs REST — Experimento Controlado</span>"
        "&nbsp;&nbsp;<span style='font-size:.8rem;color:#999'>LAB05 · Engenharia de Software · PUC Minas</span>"
        "</div>",
        unsafe_allow_html=True,
    )
with fcol:
    with st.popover("Filtros", use_container_width=True):
        st.markdown("**Tipos de consulta**")
        sel_qtypes = st.multiselect(
            "Tipos de consulta",
            options=QUERY_ORDER,
            default=QUERY_ORDER,
            format_func=lambda x: Q_LABEL[x],
            label_visibility="collapsed",
        )
        if not sel_qtypes:
            sel_qtypes = QUERY_ORDER[:]

        st.markdown("**Repositórios**")
        sel_repos = st.multiselect(
            "Repositórios",
            options=all_repos,
            default=all_repos,
            label_visibility="collapsed",
        )
        if not sel_repos:
            sel_repos = all_repos[:]

        n_active = len(
            df_raw[df_raw["query_type"].isin(sel_qtypes) & df_raw["object"].isin(sel_repos)]
        )
        st.caption(
            f"{len(sel_qtypes)}/{len(QUERY_ORDER)} tipos · "
            f"{len(sel_repos)}/{len(all_repos)} repos · "
            f"{n_active:,} medições"
        )

# ══ Aplica filtros ════════════════════════════════════════════════════════════
QL_active = [Q_LABEL[q] for q in QUERY_ORDER if q in sel_qtypes]

df = df_raw[
    df_raw["query_type"].isin(sel_qtypes) &
    df_raw["object"].isin(sel_repos)
].copy()
df["query_label"] = pd.Categorical(
    df["query_type"].map(Q_LABEL),
    categories=QL_active,
    ordered=True,
)

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados. Limpe os filtros acima para redefinir.")
    st.stop()

paired = build_pairs(df)
TIME_CLIP = float(df["response_time_s"].quantile(0.995))

# ══ Abas ══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "Visão Geral",
    "RQ1 — Tempo de Resposta",
    "RQ2 — Tamanho da Resposta",
    "Análise Estatística",
])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — VISAO GERAL
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    rest_df = df[df["api_type"] == "REST"]
    gql_df  = df[df["api_type"] == "GraphQL"]
    rt_med  = rest_df["response_time_s"].median()
    gt_med  = gql_df["response_time_s"].median()
    rs_med  = rest_df["response_size_bytes"].median()
    gs_med  = gql_df["response_size_bytes"].median()

    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Medições válidas", f"{len(df):,}")
    with m2:
        st.metric("Repositórios", df["object"].nunique())
    with m3:
        d_t = (gt_med - rt_med) / rt_med * 100
        st.metric("Tempo REST (mediana)", f"{rt_med:.3f} s",
                  delta=f"GraphQL {d_t:+.1f}%", delta_color="inverse")
    with m4:
        d_s = (gs_med - rs_med) / rs_med * 100
        st.metric("Tamanho REST (mediana)", f"{rs_med:,.0f} B",
                  delta=f"GraphQL {d_s:+.1f}%", delta_color="inverse")
    with m5:
        st.metric("Tipos de consulta", len(sel_qtypes))

    st.markdown("---")

    med = (df.groupby(["query_label", "api_type"], observed=True)
             [["response_time_s", "response_size_bytes"]]
             .median().reset_index())

    col_l, col_r = st.columns(2)

    with col_l:
        s = med.pivot(index="query_label", columns="api_type", values="response_time_s").reset_index()
        s.columns.name = None
        s["query_label"] = s["query_label"].astype(str)
        s["delta_pct"] = (s["GraphQL"] - s["REST"]) / s["REST"] * 100
        bar_colors = [COLOR["GraphQL"] if v < 0 else COLOR["REST"] for v in s["delta_pct"]]

        fig = go.Figure(go.Bar(
            x=s["delta_pct"], y=s["query_label"], orientation="h",
            marker_color=bar_colors,
            text=s["delta_pct"].map("{:+.1f}%".format),
            textposition="outside", textfont_size=12,
            customdata=np.stack([s["REST"], s["GraphQL"]], axis=-1),
            hovertemplate="REST: %{customdata[0]:.3f}s<br>GraphQL: %{customdata[1]:.3f}s<extra></extra>",
        ))
        fig.add_vline(x=0, line_color="#555", line_width=1.5)
        fig.update_layout(
            **_layout(h=320),
            title="<b>RQ1</b> — Variação de Tempo GraphQL vs REST (mediana)",
            xaxis=dict(
                title="Δ% em relação ao REST",
                zeroline=False,
                range=[min(s["delta_pct"]) * 1.45, max(s["delta_pct"]) * 1.45],
            ),
            yaxis=dict(categoryorder="array", categoryarray=list(reversed(QL_active))),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Azul = GraphQL mais rápido (Δ negativo); vermelho = REST mais rápido. "
            "Resultado misto: GraphQL é mais lento em Pull Requests e Commits. Hover para valores absolutos."
        )

    with col_r:
        s2 = med.pivot(index="query_label", columns="api_type", values="response_size_bytes").reset_index()
        s2.columns.name = None
        s2["query_label"] = s2["query_label"].astype(str)
        fig2 = _dumbbell_size(
            s2, "query_label",
            "<b>RQ2</b> — Tamanho Mediano de Resposta",
            QL_active, h=320,
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "Escala logarítmica — necessária pela disparidade entre APIs "
            "(Pull Requests REST ~343 kB vs GraphQL ~5 kB). "
            "O ponto azul está sempre à esquerda: GraphQL transfere menos bytes em todos os tipos."
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — RQ1: TEMPO
# Gráfico principal em largura total; tabela + diferenças pareadas abaixo.
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    # Gráfico principal — largura total
    fig = px.box(
        df, x="api_type", y="response_time_s", color="api_type",
        facet_col="query_label", facet_col_spacing=0.05,
        color_discrete_map=COLOR,
        category_orders={"api_type": ["REST", "GraphQL"], "query_label": QL_active},
        labels={"response_time_s": "Tempo (s)", "api_type": ""},
        title=f"Distribuição do Tempo de Resposta por Tipo de Consulta — REST vs GraphQL",
        notched=True,
    )
    TIME_MIN = float(df["response_time_s"].quantile(0.005))
    fig.update_layout(**_layout(h=420), showlegend=False)
    fig.update_yaxes(range=[TIME_MIN * 0.92, TIME_CLIP])
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Box plots com entalhe (notch): entalhes sem sobreposição indicam diferença nas medianas com ~95% de confiança. "
        f"Eixo Y clipado no percentil 99,5% ({TIME_CLIP:.2f}s) — outliers existem mas distorceriam a escala. "
        "Linha central = mediana; caixa = IQR (Q25–Q75)."
    )

    st.markdown("---")

    # Linha auxiliar: tabela de medianas + diferenças pareadas
    col_tbl, col_diff = st.columns([1, 2])

    with col_tbl:
        st.markdown("**Medianas por tipo de consulta**")
        tbl = df.pivot_table(
            index="query_label", columns="api_type",
            values="response_time_s", aggfunc="median", observed=True,
        ).reset_index().rename(columns={"query_label": "Tipo", "REST": "REST (s)", "GraphQL": "GQL (s)"})
        tbl["Δ (%)"]    = ((tbl["GQL (s)"] - tbl["REST (s)"]) / tbl["REST (s)"] * 100).map("{:+.1f}%".format)
        tbl["REST (s)"] = tbl["REST (s)"].map("{:.4f}".format)
        tbl["GQL (s)"]  = tbl["GQL (s)"].map("{:.4f}".format)
        st.dataframe(tbl[["Tipo", "REST (s)", "GQL (s)", "Δ (%)"]], hide_index=True,
                     use_container_width=True, height=178)

    with col_diff:
        rows_d = []
        for qt in sel_qtypes:
            sub = paired[paired["query_type"] == qt]
            for v in (sub["response_time_s_rest"] - sub["response_time_s_graphql"]):
                rows_d.append({"Tipo": Q_LABEL[qt], "Δ (s)": float(v)})
        diff_df = pd.DataFrame(rows_d)
        diff_clip = float(diff_df["Δ (s)"].abs().quantile(0.98)) * 1.1

        fig_d = px.box(
            diff_df, x="Δ (s)", y="Tipo", orientation="h", color="Tipo",
            color_discrete_sequence=[COLOR["GraphQL"]] * len(sel_qtypes),
            title="Diferenças Pareadas REST − GraphQL por Tipo",
            category_orders={"Tipo": list(reversed(QL_active))},
        )
        fig_d.add_vline(x=0, line_dash="dash", line_color=COLOR["REST"], line_width=1.5)
        fig_d.update_xaxes(range=[-diff_clip, diff_clip])
        fig_d.update_layout(**_layout(h=220), showlegend=False, yaxis_title="")
        st.plotly_chart(fig_d, use_container_width=True)
        st.caption(
            "Diferença REST − GraphQL para cada par de medição no mesmo repositório. "
            "Positivo = REST foi mais lento. Linha tracejada vermelha = zero (sem diferença)."
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — RQ2: TAMANHO
# Gráfico principal em largura total; tabela + lollipop abaixo.
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    # Gráfico principal — largura total
    s_sz = (df.groupby(["query_label", "api_type"], observed=True)["response_size_bytes"]
            .agg(median="median", q25=lambda x: x.quantile(0.25), q75=lambda x: x.quantile(0.75))
            .reset_index())
    s_sz["query_label"] = s_sz["query_label"].astype(str)

    fig = go.Figure()
    for api in ["REST", "GraphQL"]:
        sub = s_sz[s_sz["api_type"] == api].copy()
        avail = [q for q in reversed(QL_active) if q in sub["query_label"].values]
        sub = sub.set_index("query_label").loc[avail].reset_index()
        fig.add_trace(go.Bar(
            name=api, y=sub["query_label"], x=sub["median"], orientation="h",
            marker_color=COLOR[api], opacity=0.88,
            text=sub["median"].map(lambda v: f"{v:,.0f} B"),
            textposition="outside", textfont_size=11,
            error_x=dict(
                type="data", symmetric=False,
                array=(sub["q75"] - sub["median"]).values,
                arrayminus=(sub["median"] - sub["q25"]).values,
                color="#666", thickness=1.5, width=5,
            ),
            hovertemplate=f"<b>{api}</b><br>Mediana: %{{x:,.0f}} B<extra></extra>",
        ))

    fig.update_layout(
        **_layout(h=420),
        barmode="group",
        title="Tamanho de Resposta por Tipo de Consulta — REST vs GraphQL (escala logarítmica)",
        xaxis=dict(title="bytes", type="log"),
        yaxis=dict(title="", categoryorder="array", categoryarray=list(reversed(QL_active))),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Escala logarítmica — necessária pela disparidade de magnitude (REST chega a 343 kB em Pull Requests, "
        "GraphQL ~5 kB para os mesmos dados). Barras = mediana; traços = IQR. "
        "GraphQL retorna apenas os campos solicitados na query, eliminando o overfetching do REST."
    )

    st.markdown("---")

    # Linha auxiliar: tabela + lollipop de redução
    col_tbl, col_lol = st.columns([1, 2])

    with col_tbl:
        st.markdown("**Medianas e redução percentual**")
        sz = df.pivot_table(
            index="query_label", columns="api_type",
            values="response_size_bytes", aggfunc="median", observed=True,
        ).reset_index().rename(columns={"query_label": "Tipo", "REST": "REST (B)", "GraphQL": "GQL (B)"})
        sz["Redução"]  = ((1 - sz["GQL (B)"] / sz["REST (B)"]) * 100).map("{:.1f}%".format)
        sz["REST (B)"] = sz["REST (B)"].map("{:,.0f}".format)
        sz["GQL (B)"]  = sz["GQL (B)"].map("{:,.0f}".format)
        st.dataframe(sz[["Tipo", "REST (B)", "GQL (B)", "Redução"]], hide_index=True,
                     use_container_width=True, height=178)

    with col_lol:
        sz_raw = df.pivot_table(
            index="query_label", columns="api_type",
            values="response_size_bytes", aggfunc="median", observed=True,
        ).reset_index().rename(columns={"query_label": "Tipo"})
        sz_raw["Redução (%)"] = (1 - sz_raw["GraphQL"] / sz_raw["REST"]) * 100
        sz_raw["Tipo"] = sz_raw["Tipo"].astype(str)
        avail = [q for q in reversed(QL_active) if q in sz_raw["Tipo"].values]
        sz_raw = sz_raw.set_index("Tipo").loc[avail].reset_index()

        fig_l = go.Figure()
        for _, row in sz_raw.iterrows():
            fig_l.add_trace(go.Scatter(
                x=[0, row["Redução (%)"]], y=[row["Tipo"], row["Tipo"]],
                mode="lines", line=dict(color="#c8d3e0", width=2.5),
                showlegend=False, hoverinfo="skip",
            ))
        fig_l.add_trace(go.Scatter(
            x=sz_raw["Redução (%)"], y=sz_raw["Tipo"],
            mode="markers+text",
            marker=dict(size=16, color=COLOR["GraphQL"], line=dict(width=1.5, color="white")),
            text=sz_raw["Redução (%)"].map("{:.1f}%".format),
            textposition="middle right", textfont_size=12,
            showlegend=False,
        ))
        fig_l.update_layout(
            **_layout(h=220),
            title="Redução de Tamanho ao Usar GraphQL",
            xaxis=dict(title="redução (%)", range=[0, sz_raw["Redução (%)"].max() * 1.3]),
            yaxis=dict(title="", categoryorder="array", categoryarray=list(sz_raw["Tipo"])),
        )
        st.plotly_chart(fig_l, use_container_width=True)
        st.caption(
            "Redução percentual sobre as medianas. "
            "Valores acima de 90% indicam eliminação massiva de dados desnecessários (overfetching)."
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — ANALISE ESTATISTICA
# Tabelas lado a lado; gráfico de efeito em largura total abaixo.
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.caption(
        f"**Wilcoxon Signed-Rank Pareado** com correção de **Bonferroni** — "
        f"α_adj = 0,05 / 8 = {ALPHA_ADJ:.5f} · "
        "Tamanho de efeito: rank-biserial |r| "
        "(< 0,1 negligível · 0,1–0,3 pequeno · 0,3–0,5 médio · > 0,5 grande)"
    )

    wt_raw = wilcoxon_results(paired, "time_s",     "two-sided", tuple(sel_qtypes))
    ws_raw = wilcoxon_results(paired, "size_bytes", "greater",   tuple(sel_qtypes))

    def fmt_wilcoxon_table(raw: pd.DataFrame, unit: str, is_time: bool) -> pd.DataFrame:
        d = raw.copy()
        fmt = "{:.4f}" if is_time else "{:,.0f}"
        d["Med. REST"]    = d["Med. REST"].map((fmt + f" {unit}").format)
        d["Med. GraphQL"] = d["Med. GraphQL"].map((fmt + f" {unit}").format)
        d["p-valor"]      = d["p"].apply(fmt_p)
        d["W"]            = d["W"].astype(str)
        d["r (efeito)"]   = d["r"].map("{:.3f}".format)
        d["Sig."]         = d["sig"].map({True: "Sim", False: "n.s."})
        return d[["Consulta", "n", "Med. REST", "Med. GraphQL", "W", "p-valor", "r (efeito)", "Sig."]]

    col_t, col_s = st.columns(2)

    with col_t:
        st.markdown("#### RQ1 — Tempo de Resposta _(bicaudal)_")
        st.caption("H0: medianas iguais · Ha: medianas diferem · r positivo = REST mais lento")
        st.dataframe(
            fmt_wilcoxon_table(wt_raw, "s", True).set_index("Consulta"),
            use_container_width=True, height=225,
        )

    with col_s:
        st.markdown("#### RQ2 — Tamanho da Resposta _(unicaudal: REST > GraphQL)_")
        st.caption("H0: REST não maior · Ha: REST > GraphQL em bytes · r positivo = REST transfere mais")
        st.dataframe(
            fmt_wilcoxon_table(ws_raw, "B", False).set_index("Consulta"),
            use_container_width=True, height=225,
        )

    st.markdown("---")

    # Gráfico de efeito — largura total
    labels_q = wt_raw["Consulta"].tolist()
    fig_eff = go.Figure()
    fig_eff.add_trace(go.Bar(
        name="RQ1 — Tempo",
        x=labels_q, y=np.abs(wt_raw["r"].values),
        marker_color=COLOR["REST"], opacity=0.85,
        text=wt_raw["r"].map("{:+.3f}".format), textposition="outside", textfont_size=11,
    ))
    fig_eff.add_trace(go.Bar(
        name="RQ2 — Tamanho",
        x=labels_q, y=np.abs(ws_raw["r"].values),
        marker_color=COLOR["GraphQL"], opacity=0.85,
        text=ws_raw["r"].map("{:+.3f}".format), textposition="outside", textfont_size=11,
    ))
    for y_ref, label_ref in [(0.1, "pequeno"), (0.3, "médio"), (0.5, "grande")]:
        fig_eff.add_hline(
            y=y_ref, line_dash="dot", line_color="#aaa", line_width=1,
            annotation_text=label_ref, annotation_position="top right",
            annotation_font_size=10,
        )
    fig_eff.update_layout(
        **_layout(h=320),
        title="Tamanho de Efeito — Correlação Rank-Biserial |r| por Métrica e Tipo de Consulta",
        barmode="group",
        yaxis=dict(title="|r|", range=[0, 1.18]),
        xaxis_title="",
        legend=dict(orientation="h", y=1.1, x=0),
    )
    st.plotly_chart(fig_eff, use_container_width=True)
    st.caption(
        "|r| mede a magnitude do efeito independentemente do p-valor — um efeito pode ser significativo e ainda assim pequeno. "
        "O sinal original de r indica direção: positivo (+) = REST foi maior ou mais lento. "
        "Linhas tracejadas: limiares de Cohen para efeito pequeno (0,1), médio (0,3) e grande (0,5)."
    )
