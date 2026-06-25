# LAB05 — GraphQL vs REST: Um Experimento Controlado

**Disciplina:** Laboratório de Experimentação de Software  
**Curso:** Engenharia de Software — PUC Minas  
**Período:** 2026/1  
**Integrantes:** Leandro Pacheco · Lucas Maia  

---

## Objetivo

Investigar se a API GraphQL v4 do GitHub oferece vantagens sobre a API REST v3 em termos de **tempo de resposta** e **tamanho da resposta**, para os mesmos dados e os mesmos repositórios.

**RQ1:** Respostas a consultas GraphQL são mais rápidas que respostas REST?  
**RQ2:** Respostas a consultas GraphQL têm tamanho menor que respostas REST?

---

## Estrutura

```
LAB05/
├── sprint01/               # Desenho do experimento e coleta de dados
│   ├── design.html         # Documento de desenho experimental
│   ├── .env.example        # Template de configuração do token GitHub
│   ├── README.md           # Instruções detalhadas de execução
│   └── scripts/
│       ├── collector.py    # Coleta de dados (paralelizável com --workers)
│       ├── config.py       # Repositórios e parâmetros
│       ├── queries.py      # Queries GraphQL e URLs REST equivalentes
│       ├── requirements.txt
│       └── results.csv     # 4.800 medições coletadas
│
├── sprint02/               # Análise estatística e relatório
│   ├── report.html         # Relatório final auto-contido
│   ├── README.md           # Instruções de análise
│   └── scripts/
│       ├── analyze.py      # Wilcoxon, effect size, visualizações
│       └── requirements.txt
│
└── sprint03/               # Dashboard interativo
    ├── dashboard.py        # Dashboard Streamlit (4 abas + filtros)
    ├── requirements.txt
    └── .streamlit/
        └── config.toml     # Tema claro
```

---

## Delineamento Experimental

| Dimensão | Valor |
|---|---|
| Plataforma | API pública do GitHub (REST v3 e GraphQL v4) |
| Repositórios | 20 repositórios populares |
| Tipos de consulta | 4 — `repo_info`, `issues`, `pull_requests`, `commits` |
| Repetições por par | 30 |
| Total de medições | 4.800 (20 × 4 × 30 × 2 APIs) |
| Projeto experimental | Within-subjects — cada repositório medido nas duas APIs |
| Ordem de execução | Aleatorizada por repetição |
| Warm-up | 2 repetições descartadas por par (elimina cold-start) |

---

## Análise Estatística

- **Teste:** Wilcoxon Signed-Rank Pareado (não paramétrico)
- **Correção:** Bonferroni — α_adj = 0,05 / 8 = **0,00625**
- **Efeito:** Correlação rank-biserial *r*

---

## Resultados Principais

**RQ1 — Tempo:** resultado misto. GraphQL é levemente mais rápido em consultas simples (`repo_info`, `issues`), mas **mais lento** em `pull_requests` (+18%) e `commits` (+14%). Não há evidência consistente de vantagem de tempo.

**RQ2 — Tamanho:** resultado unânime. GraphQL produz respostas **92–98% menores** em todos os tipos. Todos os testes significativos com p < 0,001 e efeito grande (|r| > 0,5).

---

## Como Executar

### 1. Coletar os dados (Sprint 01)

```bash
cp LAB05/sprint01/.env.example LAB05/sprint01/.env
# Inserir token GitHub em .env (github.com/settings/tokens)

cd LAB05/sprint01/scripts
pip install -r requirements.txt
python collector.py --workers 3
```

### 2. Gerar o relatório HTML (Sprint 02)

```bash
cd LAB05/sprint02/scripts
pip install -r requirements.txt
python analyze.py
# Saída: LAB05/sprint02/report.html
```

### 3. Executar o dashboard (Sprint 03)

```bash
cd LAB05/sprint03
pip install -r requirements.txt
streamlit run dashboard.py
```

---

*Junho de 2026 | Laboratório de Experimentação de Software — PUC Minas*
