# Laboratório 04 - Business Intelligence com Dados Públicos

Este diretório contém os artefatos do LAB04 da disciplina de **Laboratório de Experimentação de Software**.
Como trabalho alternativo (para alunos não matriculados em TIS 6), utilizamos os **Dados Abertos Governamentais da Câmara dos Deputados** referentes à Cota para Exercício da Atividade Parlamentar (CEAP) do ano de 2024.

## Tecnologias Utilizadas
- **Linguagem:** Python
- **Dashboard/BI:** Streamlit
- **Gráficos:** Plotly Express
- **Manipulação de Dados:** Pandas

## Estrutura do LAB04

### Sprint 01
- Script de Coleta Automatizada de Dados Abertos.
- Dashboard inicial contendo a Caracterização do Dataset (métricas gerais, limpeza de dados e distribuição de notas por partido e estado).

### Sprint 02 
- Expansão do Dashboard com visualizações interativas para responder a duas Questões de Pesquisa (RQs).
- **RQ1:** Quais são os tipos de despesas que mais consomem a Cota Parlamentar?
- **RQ2:** Quais partidos e estados (UF) apresentam o maior gasto médio na câmara?
- **RQ3:** Existem deputados com comportamento anômalo de gastos (Outliers) comparados aos seus partidos?
- **RQ4:** Existe uma alta concentração de repasses em poucos fornecedores (Monopólios/Pareto)?

---

## Como Rodar o Dashboard Localmente

**Pré-requisitos:**  
Você precisará do Python instalado e das bibliotecas listadas abaixo.

1. Instale as dependências:
   ```bash
   pip install pandas streamlit plotly
   ```

2. Realize a coleta de dados (Sprint 01):
   Entre na pasta `sprint01` e execute o script de coleta para baixar o CSV atualizado de 2024:
   ```bash
   cd LAB04/sprint01
   python coleta_dados.py
   ```

3. Execute o Dashboard da Sprint 02 (Final):
   Vá para a pasta `sprint02` e inicie o Streamlit:
   ```bash
   cd ../sprint02
   streamlit run dashboard_final.py
   ```

*Uma página abrirá automaticamente no seu navegador padrão (`http://localhost:8501`) contendo o Dashboard.*

---
