import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Caracterização de Dataset - CEAP 2024", layout="wide")

st.title("📊 Sprint 01 - Caracterização do Dataset")
st.markdown("Dashboard de visualização dos gastos da Cota para Exercício da Atividade Parlamentar (CEAP) em 2024.")

@st.cache_data
def carregar_dados():
    csv_path = "Ano-2024.csv"
    if not os.path.exists(csv_path):
        st.error("Dataset não encontrado. Por favor, execute o script 'coleta_dados.py' primeiro.")
        return None
    
    # O arquivo da câmara usa ponto e vírgula e enconding utf-8
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    # Tratamento básico
    df['vlrLiquido'] = df['vlrLiquido'].replace(',', '.', regex=True).astype(float)
    # Filtra valores negativos ou zerados (devoluções/erros)
    df = df[df['vlrLiquido'] > 0]
    return df

df = carregar_dados()

if df is not None:
    st.header("1. Visão Geral dos Dados")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total de Registros (Notas)", len(df))
    col2.metric("Total de Deputados Ativos", df['txNomeParlamentar'].nunique())
    col3.metric("Quantidade de Partidos", df['sgPartido'].nunique())
    col4.metric("Valor Total Gasto (R$)", f"R$ {df['vlrLiquido'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---")
    
    st.header("2. Caracterização do Dataset")
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Registros por Partido")
        contagem_partido = df['sgPartido'].value_counts().head(10).reset_index()
        contagem_partido.columns = ['Partido', 'Quantidade de Notas']
        st.bar_chart(data=contagem_partido.set_index('Partido'), height=400)
        
    with colB:
        st.subheader("Registros por Estado (UF)")
        contagem_uf = df['sgUF'].value_counts().reset_index()
        contagem_uf.columns = ['UF', 'Quantidade de Notas']
        st.bar_chart(data=contagem_uf.set_index('UF'), height=400)
    
    st.markdown("---")
    st.subheader("Amostra Bruta dos Dados")
    st.dataframe(df.head(100), use_container_width=True)
