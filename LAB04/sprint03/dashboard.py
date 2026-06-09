import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard – Políticas de IA no GitHub",
    page_icon="🤖",
    layout="wide",
)

# ══════════════════════════════════════════════════════════════════════════════
#  DADOS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_caracterizacao.csv")

    # ── Merge evidence_blocks e matched_policy_terms do CSV de políticas ──────
    policy_raw = pd.read_csv("policy_candidates_grouped_by_repo.csv")[
        ["repo_full_name", "evidence_blocks", "matched_policy_terms"]
    ]
    df = df.merge(
        policy_raw,
        left_on="repo",
        right_on="repo_full_name",
        how="left",
    ).drop(columns=["repo_full_name"])

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

    # ── Classificação em 4 tipos de política ──────────────────────────────────
    def classify(row):
        if row["has_policy_bin"] == 0:
            return "Ausência de Política"
        ev    = str(row.get("evidence_blocks", "")).lower()
        terms = str(row.get("matched_policy_terms", "")).lower()

        prohib_kw = [
            "not co-authored", "not generated", "ai-free", "no ai",
            "not allowed", "prohibited", "not accepted", "not acceptable",
            "without using ai", "without ai", "ai slop", "denouncement",
            "ban", "reject ai", "we do not accept", "not welcome",
            "not permit", "do not submit", "not use ai", "never use",
        ]
        discl_kw = [
            "disclose", "disclosure", "declare", "must disclose",
            "please disclose", "acknowledge", "was generative ai",
            "ai disclosure", "ai-generated pr check", "indicate if",
            "co-authored using",
        ]
        for kw in prohib_kw:
            if kw in ev:
                return "Proibição Total"
        for kw in discl_kw:
            if kw in ev or "disclose" in terms:
                return "Exigência de Disclosure"
        return "Uso Assistivo Permitido"

    df["policy_type"] = df.apply(classify, axis=1)
    return df

df = load_data()

# Sub-grupos reutilizados
COM = df[df["has_policy_bin"] == 1]
SEM = df[df["has_policy_bin"] == 0]

POLICY_ORDER  = ["Ausência de Política", "Uso Assistivo Permitido",
                 "Exigência de Disclosure", "Proibição Total"]
POLICY_COLORS = {
    "Ausência de Política":     "#636EFA",
    "Uso Assistivo Permitido":  "#00CC96",
    "Exigência de Disclosure":  "#FFA15A",
    "Proibição Total":          "#EF553B",
}
GROUP_COLORS = {"COM política": "#EF553B", "SEM política": "#636EFA"}

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13),
    margin=dict(t=55, b=40, l=40, r=20),
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def box_by_type(col, title, ylabel, log_y=False):
    data = df[df["policy_type"].isin(POLICY_ORDER)].dropna(subset=[col])
    fig  = px.box(
        data, x="policy_type", y=col,
        category_orders={"policy_type": POLICY_ORDER},
        color="policy_type", color_discrete_map=POLICY_COLORS,
        labels={"policy_type": "Tipo de Política", col: ylabel},
        title=title, points=False, log_y=log_y,
    )
    fig.update_layout(showlegend=False, **PLOT_LAYOUT)
    return fig

def box_com_sem(col, title, ylabel):
    fig = px.box(
        df.dropna(subset=[col]),
        x="has_policy", y=col,
        color="has_policy", color_discrete_map=GROUP_COLORS,
        labels={"has_policy": "Grupo", col: ylabel},
        title=title, points=False,
    )
    fig.update_layout(showlegend=False, **PLOT_LAYOUT)
    return fig

def summary_table(cols_map, groups):
    rows = []
    for label, col in cols_map.items():
        row = {"Métrica": label}
        for gname, gdf in groups.items():
            row[gname] = round(gdf[col].median(), 2)
        rows.append(row)
    return pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════════════════
#  CABEÇALHO
# ══════════════════════════════════════════════════════════════════════════════
st.title("Políticas de Uso de IA em Repositórios GitHub")
st.markdown(
    "Estudo sobre a **adoção de políticas de contribuição com IA** nos "
    "1.000 repositórios mais populares do GitHub e seu impacto no engajamento "
    "e na eficiência do fluxo de contribuição."
)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "Caracterização do Dataset",
    "RQ1 — Adoção & Classificação",
    "RQ2 — Engajamento",
    "RQ3 — Colaboração",
])

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 – CARACTERIZAÇÃO DO DATASET
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Caracterização do Dataset")
    st.markdown(
        "O dataset é composto pelos **1.000 repositórios mais populares** do GitHub "
        "(por número de estrelas). Os repositórios são particionados em dois grupos: "
        "aqueles que possuem **política de uso de IA** nas contribuições e os que **não possuem**."
    )

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Repositórios",  f"{len(df):,}")
    c2.metric("COM Política de IA",     f"{len(COM):,}",  f"{len(COM)/len(df)*100:.1f}%")
    c3.metric("SEM Política de IA",     f"{len(SEM):,}",  f"{len(SEM)/len(df)*100:.1f}%")
    c4.metric("Mediana de Stars",       f"{int(df['stars'].median()):,}")
    c5.metric("Idade Mediana (dias)",   f"{int(df['age_days'].median()):,}")
    st.divider()

    # Donut + Histograma Stars
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
        fig_donut.update_layout(title="Proporção COM / SEM Política", showlegend=False, **PLOT_LAYOUT)
        st.plotly_chart(fig_donut, width="stretch")

    with col_b:
        fig_stars = px.histogram(
            df, x="stars", nbins=40,
            color="has_policy", color_discrete_map=GROUP_COLORS,
            barmode="overlay", opacity=0.75,
            labels={"stars": "Número de Stars", "has_policy": "Grupo"},
            title="Distribuição de Stars — Dataset Completo",
        )
        fig_stars.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig_stars, width="stretch")

    # Histograma Idade
    fig_age = px.histogram(
        df, x="age_days", nbins=40,
        color="has_policy", color_discrete_map=GROUP_COLORS,
        barmode="overlay", opacity=0.75,
        labels={"age_days": "Idade do Repositório (dias)", "has_policy": "Grupo"},
        title="Distribuição da Idade dos Repositórios",
    )
    fig_age.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_age, width="stretch")

    st.subheader("Comparativo por Grupo — Características Gerais")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(box_com_sem("stars",               "Stars por Grupo",              "Stars"),              width="stretch")
    with col2:
        st.plotly_chart(box_com_sem("age_days",            "Idade por Grupo (dias)",        "Idade (dias)"),       width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(box_com_sem("unique_collaborators","Colaboradores Únicos por Grupo","Colaboradores"),      width="stretch")
    with col4:
        st.plotly_chart(box_com_sem("prs_merge_rate",      "PR Merge Rate por Grupo (%)",   "Merge Rate (%)"),     width="stretch")

    st.subheader("Medianas por Grupo")
    t1_metricas = {
        "Stars":                     "stars",
        "Idade (dias)":              "age_days",
        "Colaboradores Únicos":      "unique_collaborators",
        "PR Merge Rate (%)":         "prs_merge_rate",
        "Ciclo Mediano de PR (h)":   "median_pr_cycle_hours",
        "Avg Comentários em Issues": "avg_issue_comments",
        "Avg Comentários em PRs":    "avg_pr_comments",
    }
    st.dataframe(
        summary_table(t1_metricas, {"COM Política (mediana)": COM, "SEM Política (mediana)": SEM}),
        width="stretch", hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 – RQ1: ADOÇÃO & CLASSIFICAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("RQ1 — Adoção & Classificação")
    st.info(
        "**RQ1:** Qual é o nível de adoção de políticas de uso de IA em repositórios "
        "open-source populares e quais padrões (tipos) de políticas emergem?\n\n"
        "**Tipos esperados:** Proibição Total | Exigência de Disclosure | "
        "Uso Assistivo Permitido | Ausência de Política"
    )
    st.divider()

    type_counts = (
        df["policy_type"]
        .value_counts()
        .reindex(POLICY_ORDER)
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    type_counts.columns = ["Tipo", "Repositórios"]
    type_counts["Percentual (%)"] = (type_counts["Repositórios"] / len(df) * 100).round(1)

    # KPIs por tipo
    k1, k2, k3, k4 = st.columns(4)
    for col_w, tipo in zip([k1, k2, k3, k4], POLICY_ORDER):
        row = type_counts[type_counts["Tipo"] == tipo].iloc[0]
        col_w.metric(tipo, f"{int(row['Repositórios']):,}", f"{row['Percentual (%)']:.1f}%")
    st.divider()

    col_a, col_b = st.columns([1, 1])

    # Donut com os 4 tipos
    with col_a:
        st.markdown("**Distribuição dos 4 Tipos de Política**")
        fig_d4 = go.Figure(go.Pie(
            labels=type_counts["Tipo"],
            values=type_counts["Repositórios"],
            hole=0.50,
            marker_colors=[POLICY_COLORS[t] for t in type_counts["Tipo"]],
            textinfo="percent",
            textposition="inside",
            insidetextorientation="radial",
            hovertemplate="%{label}: %{value} repos (%{percent})<extra></extra>",
        ))
        fig_d4.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.05,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
            ),
            margin=dict(t=10, b=10, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=13),
            height=360,
        )
        st.plotly_chart(fig_d4, width="stretch")

    # Barra horizontal por tipo
    with col_b:
        fig_bar4 = px.bar(
            type_counts.sort_values("Repositórios"),
            x="Repositórios", y="Tipo",
            orientation="h",
            color="Tipo", color_discrete_map=POLICY_COLORS,
            text="Repositórios",
            title="Quantidade de Repositórios por Tipo de Política",
            labels={"Tipo": "", "Repositórios": "Nº de Repositórios"},
        )
        fig_bar4.update_traces(textposition="outside")
        fig_bar4.update_layout(showlegend=False, **PLOT_LAYOUT)
        st.plotly_chart(fig_bar4, width="stretch")

    st.divider()
    st.subheader("Detalhamento dos Repositórios COM Política")

    col_c, col_d = st.columns(2)

    # Linguagem restritiva vs permissiva
    with col_c:
        restricoes = COM["has_restrictive_language"].value_counts().reset_index()
        restricoes.columns = ["Tipo", "Contagem"]
        # coluna é bool nativo → chaves booleanas no map
        restricoes["Tipo"] = restricoes["Tipo"].map({True: "Linguagem Restritiva", False: "Linguagem Permissiva"})
        fig_rest = px.bar(
            restricoes, x="Tipo", y="Contagem",
            color="Tipo",
            color_discrete_map={"Linguagem Restritiva": "#EF553B", "Linguagem Permissiva": "#00CC96"},
            text="Contagem",
            title="Linguagem da Política: Restritiva vs Permissiva",
            labels={"Tipo": "", "Contagem": "Nº de Repositórios"},
        )
        fig_rest.update_traces(textposition="outside")
        fig_rest.update_layout(showlegend=False, **PLOT_LAYOUT)
        st.plotly_chart(fig_rest, width="stretch")

    # Top arquivos com política
    with col_d:
        files_series = (
            COM["policy_files"].dropna()
            .str.split(r"\s*&&\s*").explode()
            .str.strip().str.split("/").str[-1]
        )
        file_counts = files_series.value_counts().head(10).reset_index()
        file_counts.columns = ["Arquivo", "Contagem"]
        fig_files = px.bar(
            file_counts, x="Contagem", y="Arquivo",
            orientation="h", text="Contagem",
            title="Top 10 Arquivos com Política de IA",
            labels={"Arquivo": "", "Contagem": "Nº de Repositórios"},
            color_discrete_sequence=["#AB63FA"],
        )
        fig_files.update_traces(textposition="outside")
        fig_files.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, **PLOT_LAYOUT)
        st.plotly_chart(fig_files, width="stretch")

    # Termos de IA mais frequentes
    ai_terms = (
        COM["matched_ai_terms"].dropna()
        .str.split(r";\s*").explode()
        .str.strip().str.lower()
    )
    term_counts = ai_terms.value_counts().head(15).reset_index()
    term_counts.columns = ["Termo", "Contagem"]
    fig_terms = px.bar(
        term_counts, x="Contagem", y="Termo",
        orientation="h", text="Contagem",
        title="Termos de IA Mais Frequentes nas Políticas",
        labels={"Termo": "", "Contagem": "Frequência"},
        color_discrete_sequence=["#FFA15A"],
    )
    fig_terms.update_traces(textposition="outside")
    fig_terms.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, **PLOT_LAYOUT)
    st.plotly_chart(fig_terms, width="stretch")

    # Tabela resumo
    st.subheader("Resumo — Adoção por Tipo")
    st.dataframe(type_counts.rename(columns={"Tipo": "Tipo de Política"}), width="stretch", hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 – RQ2: IMPACTO NO ENGAJAMENTO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("RQ2 — Impacto no Engajamento")
    st.info(
        "**RQ2:** Como a presença e o tipo de política de IA se relacionam com o "
        "**volume de contribuições** e o **nível de engajamento** em projetos open-source?\n\n"
        "Métricas analisadas: PRs abertos · Issues abertas · Colaboradores únicos · "
        "Média de comentários em PRs · Média de comentários em Issues"
    )
    st.divider()

    # KPIs medianas por grupo (COM vs SEM)
    st.subheader("Medianas — COM Política vs SEM Política")
    k1, k2, k3, k4, k5 = st.columns(5)
    eng_metricas = [
        ("PRs Abertos",           "prs_opened",          k1),
        ("Issues Abertas",        "issues_opened",        k2),
        ("Colaboradores",         "unique_collaborators", k3),
        ("Coment. em PRs",        "avg_pr_comments",      k4),
        ("Coment. em Issues",     "avg_issue_comments",   k5),
    ]
    for label, col, widget in eng_metricas:
        med_com = round(COM[col].median(), 1)
        med_sem = round(SEM[col].median(), 1)
        delta   = round(med_com - med_sem, 1)
        widget.metric(f"{label} (mediana)", f"{med_com}", f"{delta:+.1f} vs SEM")
    st.divider()

    st.subheader("Volume de Contribuições por Tipo de Política")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            box_by_type("prs_opened",  "PRs Abertos por Tipo de Política",   "PRs Abertos (mediana)", log_y=True),
            width="stretch",
        )
    with col2:
        st.plotly_chart(
            box_by_type("issues_opened", "Issues Abertas por Tipo de Política", "Issues Abertas (mediana)", log_y=True),
            width="stretch",
        )

    st.subheader("Nível de Engajamento por Tipo de Política")
    col3, col4, col5 = st.columns(3)
    with col3:
        st.plotly_chart(
            box_by_type("unique_collaborators", "Colaboradores Únicos por Tipo", "Colaboradores"),
            width="stretch",
        )
    with col4:
        st.plotly_chart(
            box_by_type("avg_pr_comments", "Média de Comentários em PRs", "Avg Comentários / PR"),
            width="stretch",
        )
    with col5:
        st.plotly_chart(
            box_by_type("avg_issue_comments", "Média de Comentários em Issues", "Avg Comentários / Issue"),
            width="stretch",
        )

    # Tabela de medianas por tipo
    st.subheader("Medianas por Tipo de Política")
    rq2_metricas = {
        "PRs Abertos":            "prs_opened",
        "Issues Abertas":         "issues_opened",
        "Colaboradores Únicos":   "unique_collaborators",
        "Avg Comentários em PRs": "avg_pr_comments",
        "Avg Comentários em Issues": "avg_issue_comments",
    }
    grupos_tipo = {t: df[df["policy_type"] == t] for t in POLICY_ORDER}
    st.dataframe(
        summary_table(rq2_metricas, {t: grupos_tipo[t] for t in POLICY_ORDER}),
        width="stretch", hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 – RQ3: IMPACTO NA COLABORAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("RQ3 — Impacto na Colaboração")
    st.info(
        "**RQ3:** Como a presença e o tipo de política de IA se relacionam com a "
        "**responsividade** e a **eficiência do fluxo de contribuição** nos projetos?\n\n"
        "Métricas analisadas: PR Merge Rate · Tempo de Ciclo de PR · "
        "Tempo de 1ª resposta em PRs · Tempo de 1ª resposta em Issues · "
        "Média de reviews até aprovação"
    )
    st.divider()

    # KPIs
    st.subheader("Medianas — COM Política vs SEM Política")
    k1, k2, k3, k4, k5 = st.columns(5)
    col_metricas = [
        ("PR Merge Rate (%)",        "prs_merge_rate",                    k1),
        ("Ciclo PR (h)",             "median_pr_cycle_hours",             k2),
        ("1ª Resp. PR (h)",          "median_pr_first_response_hours",    k3),
        ("1ª Resp. Issue (h)",       "median_issue_first_response_hours", k4),
        ("Reviews p/ Aprovação",     "avg_reviews_until_approval",        k5),
    ]
    for label, col, widget in col_metricas:
        med_com = round(COM[col].median(), 2)
        med_sem = round(SEM[col].median(), 2)
        delta   = round(med_com - med_sem, 2)
        widget.metric(f"{label} (mediana)", f"{med_com}", f"{delta:+.2f} vs SEM")
    st.divider()

    st.subheader("Eficiência do Fluxo de Contribuição por Tipo de Política")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            box_by_type("prs_merge_rate", "PR Merge Rate por Tipo de Política (%)", "Merge Rate (%)"),
            width="stretch",
        )
    with col2:
        st.plotly_chart(
            box_by_type("median_pr_cycle_hours", "Tempo Mediano de Ciclo de PR (horas)", "Ciclo PR (h)", log_y=True),
            width="stretch",
        )

    st.subheader("Responsividade por Tipo de Política")
    col3, col4, col5 = st.columns(3)
    with col3:
        st.plotly_chart(
            box_by_type("median_pr_first_response_hours",    "1ª Resposta em PRs (h)",    "Horas", log_y=True),
            width="stretch",
        )
    with col4:
        st.plotly_chart(
            box_by_type("median_issue_first_response_hours", "1ª Resposta em Issues (h)", "Horas", log_y=True),
            width="stretch",
        )
    with col5:
        st.plotly_chart(
            box_by_type("avg_reviews_until_approval", "Média de Reviews até Aprovação", "Reviews"),
            width="stretch",
        )

    # Tabela de medianas
    st.subheader("Medianas por Tipo de Política")
    rq3_metricas = {
        "PR Merge Rate (%)":              "prs_merge_rate",
        "Ciclo Mediano de PR (h)":        "median_pr_cycle_hours",
        "1ª Resposta em PRs (h)":         "median_pr_first_response_hours",
        "1ª Resposta em Issues (h)":      "median_issue_first_response_hours",
        "Avg Reviews até Aprovação":      "avg_reviews_until_approval",
    }
    grupos_tipo = {t: df[df["policy_type"] == t] for t in POLICY_ORDER}
    st.dataframe(
        summary_table(rq3_metricas, {t: grupos_tipo[t] for t in POLICY_ORDER}),
        width="stretch", hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  RODAPÉ
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "Dados: top 1.000 repositórios do GitHub por estrelas · "
    "Métricas coletadas via GitHub API · "
    "Laboratório de Experimentação de Software — TIS6"
)
