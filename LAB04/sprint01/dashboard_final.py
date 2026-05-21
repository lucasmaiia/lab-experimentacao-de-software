import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Dashboard CEAP 2024", layout="wide")

st.title("📊 BI - Cota Parlamentar (CEAP) 2024")
st.markdown("Dashboard de visualização dos gastos e análise de RQs para a disciplina de Laboratório de Experimentação de Software.")

@st.cache_data
def carregar_dados():
    csv_path = "../sprint01/Ano-2024.csv"
    if not os.path.exists(csv_path):
        st.error("Dataset não encontrado. Por favor, execute o script 'coleta_dados.py' da sprint01 e garanta que o arquivo 'Ano-2024.csv' está na pasta sprint01.")
        return None
    
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    df['vlrLiquido'] = df['vlrLiquido'].replace(',', '.', regex=True).astype(float)
    df = df[df['vlrLiquido'] > 0]
    return df

df = carregar_dados()

if df is not None:
    # Criação de Abas para separar a Sprint 01 da Sprint 02
    tab_carac, tab_rq1, tab_rq2, tab_rq3, tab_rq4 = st.tabs([
        "📈 Carac. (Sprint 01)", 
        "❓ RQ1: Despesas", 
        "❓ RQ2: Gastos/UF",
        "⚠️ RQ3: Anomalias",
        "📊 RQ4: Fornecedores"
    ])

    # ---------------------------------------------------------
    # ABA 1: CARACTERIZAÇÃO DO DATASET (Sprint 01)
    # ---------------------------------------------------------
    with tab_carac:
        st.header("Caracterização do Dataset")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Registros (Notas)", len(df))
        col2.metric("Total de Deputados Ativos", df['txNomeParlamentar'].nunique())
        col3.metric("Quantidade de Partidos", df['sgPartido'].nunique())
        col4.metric("Valor Total Gasto", f"R$ {df['vlrLiquido'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Registros por Partido")
            contagem_partido = df['sgPartido'].value_counts().head(10).reset_index()
            contagem_partido.columns = ['Partido', 'Quantidade de Notas']
            fig_partido = px.bar(contagem_partido, x='Partido', y='Quantidade de Notas', title="Top 10 Partidos com mais notas emitidas")
            fig_partido.update_traces(hovertemplate='Partido: %{x}<br>Notas Emitidas: %{y}')
            st.plotly_chart(fig_partido, use_container_width=True)
            
        with colB:
            st.subheader("Registros por Estado (UF)")
            contagem_uf = df['sgUF'].value_counts().reset_index()
            contagem_uf.columns = ['UF', 'Quantidade de Notas']
            fig_uf = px.bar(contagem_uf, x='UF', y='Quantidade de Notas', title="Quantidade de notas emitidas por Estado")
            fig_uf.update_traces(hovertemplate='Estado: %{x}<br>Notas Emitidas: %{y}')
            st.plotly_chart(fig_uf, use_container_width=True)

    # ---------------------------------------------------------
    # ABA 2: RQ1 (Sprint 02)
    # ---------------------------------------------------------
    with tab_rq1:
        st.header("RQ1: Quais são os tipos de despesas que mais consomem a Cota Parlamentar?")
        
        # Agrupa pelo tipo de despesa (txtDescricao)
        despesas_agrupadas = df.groupby('txtDescricao')['vlrLiquido'].sum().reset_index()
        despesas_agrupadas = despesas_agrupadas.sort_values(by='vlrLiquido', ascending=False)
        
        fig_rq1 = px.bar(
            despesas_agrupadas, 
            y='txtDescricao', 
            x='vlrLiquido', 
            orientation='h',
            title="Volume Financeiro Gasto por Tipo de Despesa",
            labels={'txtDescricao': 'Tipo de Despesa', 'vlrLiquido': 'Valor Gasto (R$)'},
            color='vlrLiquido',
            color_continuous_scale=px.colors.sequential.Blues
        )
        fig_rq1.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        fig_rq1.update_traces(hovertemplate='Despesa: %{y}<br>Valor Total: R$ %{x:,.2f}')
        st.plotly_chart(fig_rq1, use_container_width=True)
        
        st.markdown("**Análise e Resposta:** O gráfico acima apresenta a soma de todos os gastos da cota divididos pelas suas categorias. É possível identificar facilmente quais categorias consomem a maior fatia do orçamento parlamentar.")

    # ---------------------------------------------------------
    # ABA 3: RQ2 (Sprint 02)
    # ---------------------------------------------------------
    with tab_rq2:
        st.header("RQ2: Quais partidos e estados (UF) apresentam o maior gasto médio na câmara?")
        
        col_rq2_A, col_rq2_B = st.columns(2)
        
        with col_rq2_A:
            # Gasto médio por partido
            # 1. Soma dos gastos por deputado
            gasto_por_deputado = df.groupby(['txNomeParlamentar', 'sgPartido'])['vlrLiquido'].sum().reset_index()
            # 2. Média desses gastos por partido
            media_por_partido = gasto_por_deputado.groupby('sgPartido')['vlrLiquido'].mean().reset_index()
            media_por_partido = media_por_partido.sort_values(by='vlrLiquido', ascending=False).head(10)
            
            fig_rq2_partido = px.bar(
                media_por_partido, 
                x='sgPartido', 
                y='vlrLiquido',
                title="Top 10 - Gasto Médio por Deputado por Partido",
                labels={'sgPartido': 'Partido', 'vlrLiquido': 'Gasto Médio por Deputado (R$)'},
                color='vlrLiquido',
                color_continuous_scale=px.colors.sequential.Reds
            )
            fig_rq2_partido.update_traces(hovertemplate='Partido: %{x}<br>Gasto Médio: R$ %{y:,.2f}')
            st.plotly_chart(fig_rq2_partido, use_container_width=True)
            
        with col_rq2_B:
            # Gasto médio por estado
            gasto_por_deputado_uf = df.groupby(['txNomeParlamentar', 'sgUF'])['vlrLiquido'].sum().reset_index()
            media_por_uf = gasto_por_deputado_uf.groupby('sgUF')['vlrLiquido'].mean().reset_index()
            media_por_uf = media_por_uf.sort_values(by='vlrLiquido', ascending=False)
            
            fig_rq2_uf = px.bar(
                media_por_uf, 
                x='sgUF', 
                y='vlrLiquido',
                title="Gasto Médio por Deputado por Estado",
                labels={'sgUF': 'Estado (UF)', 'vlrLiquido': 'Gasto Médio por Deputado (R$)'},
                color='vlrLiquido',
                color_continuous_scale=px.colors.sequential.Greens
            )
            fig_rq2_uf.update_traces(hovertemplate='Estado: %{x}<br>Gasto Médio: R$ %{y:,.2f}')
            st.plotly_chart(fig_rq2_uf, use_container_width=True)
            
        st.markdown("**Análise e Resposta:** Avaliando o gasto médio (total gasto / número de parlamentares do grupo), podemos visualizar se existem partidos ou regiões que tendem a esgotar mais suas cotas proporcionalmente.")

    # ---------------------------------------------------------
    # ABA 4: RQ3 (Sprint 02) - OUTLIERS
    # ---------------------------------------------------------
    with tab_rq3:
        st.header("RQ3: Existem deputados com comportamento anômalo de gastos (Outliers)?")
        
        # Agrupa gasto total por deputado e cruza com partido
        df_outliers = df.groupby(['txNomeParlamentar', 'sgPartido'])['vlrLiquido'].sum().reset_index()
        
        # Filtra os top 15 maiores partidos para o gráfico não ficar ilegível
        top_partidos = df['sgPartido'].value_counts().head(15).index
        df_outliers_top = df_outliers[df_outliers['sgPartido'].isin(top_partidos)]
        
        fig_rq3 = px.box(
            df_outliers_top, 
            x='sgPartido', 
            y='vlrLiquido', 
            hover_data=['txNomeParlamentar'],
            title="Distribuição e Outliers de Gastos por Partido (Top 15 Partidos)",
            labels={'sgPartido': 'Partido', 'vlrLiquido': 'Total Gasto pelo Deputado (R$)'},
            color='sgPartido'
        )
        fig_rq3.update_traces(hovertemplate='Partido: %{x}<br>Gasto: R$ %{y:,.2f}<br>Deputado: %{customdata[0]}')
        st.plotly_chart(fig_rq3, use_container_width=True)
        
        st.markdown("**Análise e Resposta:** O Gráfico de Caixa (Boxplot) nos permite ver a média, a dispersão e os *outliers*. Cada 'ponto' que aparece fora do caixote superior ou inferior representa um parlamentar cujo gasto destoou estatisticamente do padrão do seu próprio partido, caracterizando uma anomalia (positiva ou negativa). Ao passar o mouse sobre o ponto isolado, podemos ver o nome de quem gastou muito além dos seus colegas de partido.")

    # ---------------------------------------------------------
    # ABA 5: RQ4 (Sprint 02) - MONOPÓLIOS/PARETO
    # ---------------------------------------------------------
    with tab_rq4:
        st.header("RQ4: Existe uma concentração alta de repasses em poucos fornecedores (Monopólio)?")
        
        # Agrupa pelo Fornecedor
        df_fornecedor = df.groupby('txtFornecedor')['vlrLiquido'].sum().reset_index()
        df_fornecedor = df_fornecedor.sort_values(by='vlrLiquido', ascending=False)
        
        # Calcula representatividade dos top 20
        top_20 = df_fornecedor.head(20)
        total_gasto = df_fornecedor['vlrLiquido'].sum()
        gasto_top_20 = top_20['vlrLiquido'].sum()
        
        col_pareto1, col_pareto2 = st.columns([3, 1])
        
        with col_pareto1:
            fig_rq4 = px.bar(
                top_20, 
                x='txtFornecedor', 
                y='vlrLiquido',
                title="Top 20 Fornecedores que mais recebem verba da Câmara",
                labels={'txtFornecedor': 'Fornecedor', 'vlrLiquido': 'Total Recebido (R$)'},
                color='vlrLiquido',
                color_continuous_scale=px.colors.sequential.Oranges
            )
            fig_rq4.update_traces(hovertemplate='Fornecedor: %{x}<br>Recebeu: R$ %{y:,.2f}')
            st.plotly_chart(fig_rq4, use_container_width=True)
            
        with col_pareto2:
            st.metric("Total Gasto (Câmara)", f"R$ {total_gasto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            st.metric("Total Gasto (Apenas Top 20 Empresas)", f"R$ {gasto_top_20:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            percentual = (gasto_top_20 / total_gasto) * 100
            st.metric("Concentração no Top 20", f"{percentual:.2f}% do orçamento total")
            
        st.markdown("**Análise e Resposta:** Uma análise de concentração demonstra se o mercado que atende o parlamento é difuso ou concentrado. Caso as top 20 empresas (de um total de dezenas de milhares de CNPJs no dataset) representem uma porcentagem alta dos milhões distribuídos, evidenciamos um monopólio de prestação de serviços (geralmente companhias aéreas ou grandes empresas de marketing/locação).")
