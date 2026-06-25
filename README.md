# Laboratório de Experimentação de Software

Este repositório contém os materiais, scripts e relatórios desenvolvidos ao longo da disciplina **Laboratório de Experimentação de Software**, cursada no **6º período do curso de Engenharia de Software da PUC Minas**.

O objetivo deste repositório é organizar as atividades práticas realizadas durante o semestre, incluindo coleta de dados, análises experimentais, implementação de scripts e documentação dos resultados obtidos ao longo dos laboratórios da disciplina.

---

## Estrutura do Repositório

O repositório está organizado para armazenar os diferentes laboratórios e seus respectivos artefatos, tais como:

- Scripts de coleta e processamento de dados  
- Arquivos de resultados (CSV, relatórios e análises)  
- Dashboards e visualizações  
- Documentação das atividades desenvolvidas  

Cada laboratório pode conter sua própria estrutura de código, dados coletados e relatórios associados.

---

## Disciplina

**Laboratório de Experimentação de Software**  
Curso: Engenharia de Software  
Instituição: Pontifícia Universidade Católica de Minas Gerais (PUC Minas)

A disciplina tem como objetivo aplicar métodos experimentais para análise de dados relacionados ao desenvolvimento de software, explorando técnicas de coleta, análise e interpretação de métricas em repositórios e projetos de software.

---

## Integrantes

**Alunos**
- Leandro Pacheco  
- Lucas Maia  

**Professor**
- Danilo de Quadros Maia Filho  

---

## Período

PUC Minas - **2026/1**

---

## LAB05 — GraphQL vs REST: Um Experimento Controlado

### Objetivo

Comparar as APIs **REST v3** e **GraphQL v4** do GitHub em duas dimensões:

- **RQ1:** Respostas a consultas GraphQL são mais rápidas que respostas REST?
- **RQ2:** Respostas a consultas GraphQL têm tamanho menor que respostas REST?

---

### Delineamento Experimental

| Dimensão | Configuração |
|---|---|
| Plataforma | API pública do GitHub (REST v3 e GraphQL v4) |
| Repositórios | 20 repositórios populares (React, Vue, TensorFlow, VSCode...) |
| Tipos de consulta | 4 — `repo_info`, `issues`, `pull_requests`, `commits` |
| Repetições por par | 30 |
| Total de medições | 4.800 (20 × 4 × 30 × 2 APIs) |
| Projeto experimental | Within-subjects — cada repositório medido nas duas APIs |
| Ordem de execução | Aleatorizada por repetição para evitar viés de ordenação |
| Warm-up | 2 repetições descartadas por par para eliminar cold-start |

**Variáveis dependentes:** tempo de resposta (segundos) e tamanho da resposta (bytes).  
**Variável independente:** tipo de API (REST ou GraphQL).

---

### Hipóteses

**RQ1 — Tempo (bicaudal)**
- H₀: `mediana(T_GraphQL) = mediana(T_REST)`
- H₁: `mediana(T_GraphQL) ≠ mediana(T_REST)`

**RQ2 — Tamanho (unicaudal)**
- H₀: `mediana(S_GraphQL) = mediana(S_REST)`
- H₁: `mediana(S_GraphQL) < mediana(S_REST)`

---

### Análise Estatística

- **Teste:** Wilcoxon Signed-Rank Pareado (não paramétrico — adequado para distribuições assimétricas)
- **Correção de múltiplos testes:** Bonferroni — α_adj = 0,05 / 8 = **0,00625**
- **Tamanho de efeito:** Correlação rank-biserial *r* (< 0,1 negligível · 0,1–0,3 pequeno · 0,3–0,5 médio · > 0,5 grande)

---

### Resultados Principais

**RQ1 — Tempo de resposta:** resultado **misto**.
- GraphQL levemente mais rápido em `repo_info` e `issues`, mas **mais lento** em `pull_requests` (+18%) e `commits` (+14%).
- Diferenças não são estatisticamente significativas após correção de Bonferroni para os tipos mais pesados.
- Conclusão: não há evidência consistente de vantagem de tempo para GraphQL.

**RQ2 — Tamanho da resposta:** resultado **unânime e expressivo**.
- GraphQL produz respostas **92–98% menores** em todos os tipos de consulta.
- Todos os testes significativos com p < 0,001 e |r| > 0,5 (efeito grande).
- Causa: GraphQL retorna apenas os campos solicitados na query, eliminando o overfetching estrutural do REST.

---

### Estrutura do LAB05

```
LAB05/
├── sprint01/               # Desenho e coleta de dados
│   ├── design.html         # Documento de desenho do experimento
│   ├── .env.example        # Template de configuração do token GitHub
│   └── scripts/
│       ├── collector.py    # Script de coleta (suporte a --workers para paralelismo)
│       ├── config.py       # Repositórios e parâmetros do experimento
│       ├── queries.py      # Queries GraphQL e URLs REST equivalentes
│       ├── requirements.txt
│       └── results.csv     # 4.800 medições coletadas
│
├── sprint02/               # Análise estatística e relatório
│   ├── report.html         # Relatório final auto-contido
│   └── scripts/
│       ├── analyze.py      # Análise completa: Wilcoxon, efeito, visualizações
│       └── requirements.txt
│
└── sprint03/               # Dashboard interativo
    ├── dashboard.py        # Dashboard Streamlit com 4 abas e filtros
    └── requirements.txt
```

---

### Como Reproduzir

#### 1. Configurar o token GitHub

```bash
cp LAB05/sprint01/.env.example LAB05/sprint01/.env
# Editar .env e inserir o token (github.com/settings/tokens)
```

#### 2. Instalar dependências e coletar dados

```bash
cd LAB05/sprint01/scripts
pip install -r requirements.txt
python collector.py --workers 3   # coleta completa (~15 min com 3 workers)
```

#### 3. Gerar o relatório HTML

```bash
cd LAB05/sprint02/scripts
pip install -r requirements.txt
python analyze.py
# Relatório salvo em LAB05/sprint02/report.html
```

#### 4. Executar o dashboard interativo

```bash
cd LAB05/sprint03
pip install -r requirements.txt
streamlit run dashboard.py
```

O dashboard possui 4 abas — **Visão Geral**, **RQ1 Tempo**, **RQ2 Tamanho** e **Análise Estatística** — com filtros por tipo de consulta e repositório.