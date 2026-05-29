import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard – Políticas de IA no GitHub",
    page_icon="🤖",
    layout="wide",
)

# ── Carrega dados ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_caracterizacao.csv")
    numeric_cols = [
        "stars", "age_days", "prs_opened", "prs_merged", "prs_closed_no_merge",
        "prs_merge_rate", "avg_pr_comments", "avg_pr_reviews", "avg_pr_commits",
        "median_pr_cycle_hours", "median_pr_first_response_hours",
        "issues_opened", "issues_closed", "avg_issue_comments",
        "median_issue_first_response_hours", "unique_collaborators",
        "avg_reviews_until_approval", "best_candidate_score",
        "candidate_count", "evidence_group_count",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

df = load_data()
COM = df[df["has_policy_bin"] == 1]
SEM = df[df["has_policy_bin"] == 0]

COLORS = {"COM política": "#EF553B", "SEM política": "#636EFA"}

# ── Paleta de estilo ───────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13),
    margin=dict(t=50, b=40, l=40, r=20),
)

# ══════════════════════════════════════════════════════════════════════════════
#  CABEÇALHO
# ══════════════════════════════════════════════════════════════════════════════
st.title("🤖 Políticas de Uso de IA em Repositórios GitHub")
st.markdown(
    "Dashboard de caracterização do dataset utilizado no estudo sobre "
    "**políticas de contribuição com IA** nos repositórios mais populares do GitHub."
)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 1 – VISÃO GERAL DO DATASET
# ══════════════════════════════════════════════════════════════════════════════
st.header("1. Visão Geral do Dataset")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de Repositórios", f"{len(df):,}")
c2.metric("COM Política de IA", f"{len(COM):,}", f"{len(COM)/len(df)*100:.1f}%")
c3.metric("SEM Política de IA", f"{len(SEM):,}", f"{len(SEM)/len(df)*100:.1f}%")
c4.metric("Mediana de Stars", f"{int(df['stars'].median()):,}")
c5.metric("Idade Mediana (dias)", f"{int(df['age_days'].median()):,}")

st.markdown("---")

# ── Donut: COM vs SEM política ─────────────────────────────────────────────
col_a, col_b = st.columns([1, 2])

with col_a:
    fig_donut = go.Figure(go.Pie(
        labels=["COM política", "SEM política"],
        values=[len(COM), len(SEM)],
        hole=0.55,
        marker_colors=["#EF553B", "#636EFA"],
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} repos<extra></extra>",
    ))
    fig_donut.update_layout(
        title="Proporção COM / SEM Política de IA",
        showlegend=False,
        **PLOT_LAYOUT,
    )
    st.plotly_chart(fig_donut, width="stretch")

with col_b:
    # Histograma de Stars (dataset completo)
    fig_stars = px.histogram(
        df, x="stars", nbins=40,
        color="has_policy", color_discrete_map=COLORS,
        barmode="overlay", opacity=0.75,
        labels={"stars": "Número de Stars", "has_policy": "Grupo"},
        title="Distribuição de Stars - Dataset Completo",
    )
    fig_stars.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_stars, width="stretch")

# ── Histograma de Idade ────────────────────────────────────────────────────
fig_age = px.histogram(
    df, x="age_days", nbins=40,
    color="has_policy", color_discrete_map=COLORS,
    barmode="overlay", opacity=0.75,
    labels={"age_days": "Idade do Repositório (dias)", "has_policy": "Grupo"},
    title="Distribuição da Idade dos Repositórios - Dataset Completo",
)
fig_age.update_layout(**PLOT_LAYOUT)
st.plotly_chart(fig_age, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 2 – COMPARATIVO ENTRE GRUPOS
# ══════════════════════════════════════════════════════════════════════════════
st.header("2. Comparativo: COM Política vs SEM Política de IA")

def box_compare(col, title, ylabel):
    fig = px.box(
        df.dropna(subset=[col]),
        x="has_policy", y=col,
        color="has_policy", color_discrete_map=COLORS,
        labels={"has_policy": "Grupo", col: ylabel},
        title=title,
        points=False,
    )
    fig.update_layout(showlegend=False, **PLOT_LAYOUT)
    return fig

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(box_compare("stars", "Stars por Grupo", "Stars"), width="stretch")
with col2:
    st.plotly_chart(box_compare("age_days", "Idade por Grupo (dias)", "Idade (dias)"), width="stretch")

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(
        box_compare("unique_collaborators", "Colaboradores Únicos por Grupo", "Colaboradores"),
        width="stretch",
    )
with col4:
    st.plotly_chart(
        box_compare("prs_merge_rate", "Taxa de Merge de PRs por Grupo (%)", "PR Merge Rate (%)"),
        width="stretch",
    )

col5, col6 = st.columns(2)
with col5:
    st.plotly_chart(
        box_compare("median_pr_cycle_hours", "Tempo Mediano de Ciclo de PR por Grupo (horas)", "Mediana Ciclo PR (h)"),
        width="stretch",
    )
with col6:
    st.plotly_chart(
        box_compare("avg_issue_comments", "Média de Comentários em Issues por Grupo", "Média de Comentários"),
        width="stretch",
    )

# ── Tabela de Medianas ─────────────────────────────────────────────────────
st.subheader("Medianas por Grupo")

metricas = {
    "Stars":                        "stars",
    "Idade (dias)":                 "age_days",
    "Colaboradores Únicos":         "unique_collaborators",
    "PR Merge Rate (%)":            "prs_merge_rate",
    "Ciclo Mediano de PR (h)":      "median_pr_cycle_hours",
    "Avg Comentários em Issues":    "avg_issue_comments",
    "Avg Comentários em PRs":       "avg_pr_comments",
    "Avg Reviews até Aprovação":    "avg_reviews_until_approval",
}

summary = pd.DataFrame({
    "Métrica": list(metricas.keys()),
    "COM Política (mediana)": [COM[v].median() for v in metricas.values()],
    "SEM Política (mediana)": [SEM[v].median() for v in metricas.values()],
})
summary["COM Política (mediana)"] = summary["COM Política (mediana)"].round(2)
summary["SEM Política (mediana)"] = summary["SEM Política (mediana)"].round(2)

st.dataframe(summary, width="stretch", hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SEÇÃO 3 – DETALHAMENTO DOS REPOS COM POLÍTICA
# ══════════════════════════════════════════════════════════════════════════════
st.header("3. Detalhamento - Repositórios COM Política de IA")

col_d1, col_d2 = st.columns(2)

# Linguagem restritiva vs permissiva
with col_d1:
    restricoes = COM["has_restrictive_language"].value_counts().reset_index()
    restricoes.columns = ["Tipo", "Contagem"]
    restricoes["Tipo"] = restricoes["Tipo"].map({"True": "Restritiva", "False": "Permissiva"})
    fig_rest = px.bar(
        restricoes, x="Tipo", y="Contagem",
        color="Tipo",
        color_discrete_map={"Restritiva": "#EF553B", "Permissiva": "#00CC96"},
        text="Contagem",
        title="Linguagem da Política: Restritiva vs Permissiva",
        labels={"Tipo": "Tipo de Linguagem", "Contagem": "Nº de Repositórios"},
    )
    fig_rest.update_traces(textposition="outside")
    fig_rest.update_layout(showlegend=False, **PLOT_LAYOUT)
    st.plotly_chart(fig_rest, width="stretch")

# Arquivo onde a política aparece
with col_d2:
    # Explode policy_files (podem ter múltiplos separados por &&)
    files_series = (
        COM["policy_files"]
        .dropna()
        .str.split(r"\s*&&\s*")
        .explode()
        .str.strip()
        .str.split("/").str[-1]   # pega só o nome do arquivo
    )
    file_counts = files_series.value_counts().head(10).reset_index()
    file_counts.columns = ["Arquivo", "Contagem"]
    fig_files = px.bar(
        file_counts, x="Contagem", y="Arquivo",
        orientation="h",
        text="Contagem",
        title="Top 10 Arquivos com Política de IA",
        labels={"Arquivo": "", "Contagem": "Nº de Repositórios"},
        color_discrete_sequence=["#AB63FA"],
    )
    fig_files.update_traces(textposition="outside")
    fig_files.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, **PLOT_LAYOUT)
    st.plotly_chart(fig_files, width="stretch")

# Termos de IA mais frequentes
ai_terms = (
    COM["matched_ai_terms"]
    .dropna()
    .str.split(r";\s*")
    .explode()
    .str.strip()
    .str.lower()
)
term_counts = ai_terms.value_counts().head(15).reset_index()
term_counts.columns = ["Termo", "Contagem"]

fig_terms = px.bar(
    term_counts, x="Contagem", y="Termo",
    orientation="h",
    text="Contagem",
    title="Termos de IA Mais Frequentes nas Políticas",
    labels={"Termo": "", "Contagem": "Frequência"},
    color_discrete_sequence=["#FFA15A"],
)
fig_terms.update_traces(textposition="outside")
fig_terms.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, **PLOT_LAYOUT)
st.plotly_chart(fig_terms, width="stretch")

# Score de candidatos
st.subheader("Score de Detecção das Políticas")
fig_score = px.histogram(
    COM, x="best_candidate_score", nbins=10,
    color_discrete_sequence=["#19D3F3"],
    labels={"best_candidate_score": "Score do Melhor Candidato", "count": "Repositórios"},
    title="Distribuição do Score de Detecção (Repos COM Política)",
)
fig_score.update_layout(**PLOT_LAYOUT)
st.plotly_chart(fig_score, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
#  RODAPÉ
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "Dados: top 1.000 repositórios do GitHub por estrelas · "
    "Métricas coletadas via GitHub API · "
    "Laboratório de Experimentação de Software"
)
