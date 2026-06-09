# Lab 04 — Business Intelligence em Repositórios Open Source
## Relatório Final — Sprint 03

**Disciplina:** Laboratório de Experimentação de Software  
**Curso:** Engenharia de Software — PUC Minas  
**Autores:** Lucas Maia, Leandro Caldas  
**Data:** Maio de 2026

---

## Índice

1. [Introdução e Hipóteses](#1-introdução-e-hipóteses)
2. [Questões de Pesquisa](#2-questões-de-pesquisa)
3. [Metodologia](#3-metodologia)
4. [Caracterização do Dataset](#4-caracterização-do-dataset)
5. [Resultados Obtidos](#5-resultados-obtidos)
6. [Discussão das Hipóteses](#6-discussão-das-hipóteses)
7. [Conclusão](#7-conclusão)

---

## 1. Introdução e Hipóteses

O uso de ferramentas de Inteligência Artificial (IA) generativa no desenvolvimento de software cresceu de maneira expressiva nos últimos anos. Assistentes como GitHub Copilot, ChatGPT e Claude Code passaram a fazer parte do fluxo cotidiano de desenvolvedores, levantando questões importantes sobre a qualidade, a autoria e a rastreabilidade das contribuições em projetos open source.

Diante desse cenário, mantenedores de repositórios populares no GitHub começaram a adotar **políticas explícitas de uso de IA**, regulando como e em que medida ferramentas de IA podem ser utilizadas nas contribuições. Essas políticas variam desde a **proibição total** de código gerado por IA até exigências de *disclosure* ou permissão irrestrita de uso assistivo.

Este estudo aplica técnicas de **Business Intelligence (BI)** para explorar e visualizar dados coletados sobre os 1.000 repositórios mais populares do GitHub, buscando entender o nível de adoção dessas políticas e seu impacto nas dinâmicas de engajamento e colaboração dos projetos.

### 1.1 Hipóteses Iniciais

| RQ | Pergunta (resumida) | Hipótese inicial |
|----|---------------------|-----------------|
| RQ1 | Adoção e tipos de políticas | Esperamos que a adoção seja baixa — a maioria dos repositórios ainda não trata explicitamente o tema. Dos que adotam, esperamos predominância de políticas de *disclosure* em detrimento de proibições. |
| RQ2 | Política × engajamento | Repositórios com política de IA tendem a ser mais maduros e gerenciados, com maior volume de PRs e issues — reflexo de uma cultura de contribuição mais estruturada. |
| RQ3 | Política × colaboração | Projetos com política apresentam processos mais eficientes: maior taxa de merge e menor tempo de ciclo de PR, indicando maior clareza nas diretrizes de contribuição. |

---

## 2. Questões de Pesquisa

> **RQ1 — Adoção & Classificação:** Qual é o nível de adoção de políticas de uso de IA em repositórios open-source populares e quais padrões (tipos) de políticas emergem?

> **RQ2 — Impacto no Engajamento:** Como a presença e o tipo de política de IA se relacionam com o volume de contribuições e o nível de engajamento em projetos open-source?

> **RQ3 — Impacto na Colaboração:** Como a presença e o tipo de política de IA se relacionam com a responsividade e a eficiência do fluxo de contribuição nos projetos?

---

## 3. Metodologia

### 3.1 Visão Geral do Processo

O processo metodológico é composto por três etapas principais: coleta e filtragem dos repositórios, detecção automática de políticas de IA e construção do dashboard de BI.

```
top_repos_filtered.csv          policy_candidates_grouped_by_repo.csv
(1.000 repos, stars/idade)  +   (125 repos com política detectada)
              ↓                              ↓
         repository_metrics.csv             ↓
    (998 repos, métricas de PR/issues)      ↓
              ↓                              ↓
         ─────────── dataset_caracterizacao.csv ────────────
                     (1.000 linhas × 28 colunas)
                               ↓
                  Classificação em 4 tipos de política
                               ↓
                   Dashboard Streamlit (dashboard.py)
                    Tab 1: Caracterização do Dataset
                    Tab 2: RQ1 — Adoção & Classificação
                    Tab 3: RQ2 — Impacto no Engajamento
                    Tab 4: RQ3 — Impacto na Colaboração
```

### 3.2 Seleção dos Repositórios

O dataset base é composto pelos **1.000 repositórios mais populares do GitHub**, ranqueados por número de estrelas. Os dados de popularidade e maturidade (estrelas, idade em dias, data de atividade mais recente) foram coletados via GitHub API e armazenados em `top_repos_filtered.csv`.

**Critério de inclusão:** repositório público com presença entre os top 1.000 por estrelas, sem restrição de linguagem de programação.

### 3.3 Coleta de Métricas dos Repositórios

Para 998 dos 1.000 repositórios (2 falharam por limitações da API), foram coletadas métricas detalhadas de atividade via amostragem estatística com amostragem temporal aleatória (*temporal-random sampling*), utilizando a fórmula de Cochran com correção de população finita (nível de confiança 95%, margem de erro 10%).

As métricas coletadas estão descritas na tabela abaixo:

| Dimensão | Métrica | Campo |
|----------|---------|-------|
| Pull Requests | PRs abertos, fechados, mergeados | `prs_opened`, `prs_merged`, `prs_closed_no_merge` |
| Pull Requests | Taxa de merge | `prs_merge_rate` |
| Pull Requests | Tempo mediano de ciclo | `median_pr_cycle_hours` |
| Pull Requests | Tempo mediano até 1ª resposta | `median_pr_first_response_hours` |
| Pull Requests | Avg comentários e reviews | `avg_pr_comments`, `avg_pr_reviews` |
| Pull Requests | Reviews até aprovação | `avg_reviews_until_approval` |
| Issues | Issues abertas e fechadas | `issues_opened`, `issues_closed` |
| Issues | Tempo mediano até 1ª resposta | `median_issue_first_response_hours` |
| Issues | Avg comentários | `avg_issue_comments` |
| Colaboração | Colaboradores únicos | `unique_collaborators` |

### 3.4 Detecção de Políticas de IA

A identificação de repositórios com política de uso de IA foi realizada por meio de um **pipeline de detecção baseado em expressões regulares e correspondência de termos**, aplicado sobre os arquivos de contribuição de cada repositório (CONTRIBUTING.md, .github/PULL_REQUEST_TEMPLATE.md e similares).

O pipeline gera para cada repositório:

| Campo | Descrição |
|-------|-----------|
| `policy_files` | Arquivo(s) onde a política foi encontrada |
| `matched_ai_terms` | Termos de IA detectados (ex.: `AI-generated`, `LLM`, `generative AI`) |
| `matched_policy_terms` | Termos de política detectados (ex.: `disclose`, `must`, `prohibited`) |
| `has_restrictive_language` | Booleano — indica presença de linguagem restritiva |
| `best_candidate_score` | Score do trecho com melhor correspondência (1–5) |
| `evidence_blocks` | Trechos de texto completos que motivaram a detecção |

Dos 1.000 repositórios analisados, **125 (12,5%)** tiveram política de IA detectada.

### 3.5 Classificação em Tipos de Política

Os 125 repositórios com política detectada foram classificados em três tipos, com base em correspondência de palavras-chave nos campos `evidence_blocks` e `matched_policy_terms`:

| Tipo | Critério de Classificação | Exemplos de keywords |
|------|--------------------------|----------------------|
| **Proibição Total** | Linguagem que proíbe explicitamente contribuições geradas por IA | `not co-authored`, `not allowed`, `prohibited`, `ai slop`, `denouncement`, `not accepted` |
| **Exigência de Disclosure** | Exige que o contribuidor declare o uso de IA, sem proibir | `disclose`, `disclosure`, `declare`, `must disclose`, `ai-generated pr check`, `co-authored using` |
| **Uso Assistivo Permitido** | Menciona IA mas sem restrição explícita nem obrigação de declaração | Demais casos com política detectada |

Os 875 repositórios sem política detectada foram classificados como **Ausência de Política**.

A prioridade de classificação é: *Proibição Total* > *Exigência de Disclosure* > *Uso Assistivo Permitido*, garantindo que um repositório seja alocado sempre na categoria mais restritiva que se aplica ao seu conteúdo.

### 3.6 Consolidação do Dataset

Os três arquivos de origem foram combinados em um único dataset consolidado (`dataset_caracterizacao.csv`) com **1.000 linhas × 28 colunas**, contendo:

- Dados de identificação e popularidade (`repo`, `url`, `stars`, `age_days`)
- Métricas de PR e issues (17 colunas)
- Variáveis de política (`has_policy`, `has_policy_bin`, `policy_type`, `has_restrictive_language`, `policy_files`, `matched_ai_terms`, `best_candidate_score`)

### 3.7 Construção do Dashboard

O dashboard foi desenvolvido em **Python** utilizando as bibliotecas **Streamlit** (interface web interativa) e **Plotly** (visualizações gráficas). A aplicação é organizada em quatro abas:

| Aba | Conteúdo |
|-----|----------|
| **Caracterização do Dataset** | KPIs gerais, histogramas de stars e idade, box plots comparativos COM vs SEM política, tabela de medianas |
| **RQ1 — Adoção & Classificação** | KPIs dos 4 tipos, donut chart, gráfico de barras por tipo, arquivos mais frequentes, termos de IA, linguagem restritiva vs. permissiva |
| **RQ2 — Engajamento** | KPIs de medianas COM vs SEM, box plots por tipo de política para volume de PRs, issues, colaboradores e comentários |
| **RQ3 — Colaboração** | KPIs de medianas COM vs SEM, box plots por tipo de política para merge rate, ciclo de PR, tempo de 1ª resposta e reviews até aprovação |

A medida de tendência central adotada em todas as visualizações é a **mediana**, por ser robusta a distribuições assimétricas de cauda longa, características típicas de métricas de repositórios open source. Gráficos com diferenças de escala pronunciada utilizam **escala logarítmica no eixo Y** para preservar a legibilidade.

---

## 4. Caracterização do Dataset

### 4.1 Visão Geral

| Atributo | Valor |
|----------|-------|
| Total de repositórios | 1.000 |
| Repositórios COM política de IA | 125 (12,5%) |
| Repositórios SEM política de IA | 875 (87,5%) |
| Repositórios com métricas coletadas | 998 |
| Mediana de estrelas | 39.673 |
| Mediana de idade | 2.749 dias (~7,5 anos) |
| Mínimo de estrelas | 14.366 |
| Máximo de estrelas | 443.636 |

*(Ver: Dashboard, aba **Caracterização do Dataset** — KPI Cards e gráfico "Proporção COM / SEM Política")*

### 4.2 Distribuição de Stars e Idade

A distribuição de estrelas é fortemente assimétrica à direita (cauda longa): a maioria dos repositórios concentra-se entre 14.000 e 60.000 estrelas, enquanto poucos ultrapassam 200.000. Os repositórios COM política de IA apresentam distribuição de stars e idade semelhante ao grupo SEM política, indicando que a adoção de políticas não está diretamente correlacionada com a popularidade absoluta do projeto.

*(Ver: Dashboard, aba **Caracterização do Dataset** — gráficos "Distribuição de Stars — Dataset Completo" e "Distribuição da Idade dos Repositórios")*

### 4.3 Comparativo por Grupo

| Métrica | COM Política (mediana) | SEM Política (mediana) |
|---------|:---------------------:|:---------------------:|
| Colaboradores Únicos | 97,5 | 91,0 |
| PR Merge Rate (%) | 75,3 | 69,6 |
| Ciclo Mediano de PR (h) | 16,9 | 20,5 |
| Avg Comentários em PRs | 2,0 | 1,4 |
| Avg Comentários em Issues | 4,1 | 3,1 |

*(Ver: Dashboard, aba **Caracterização do Dataset** — box plots "Stars por Grupo", "Idade por Grupo", "Colaboradores Únicos por Grupo" e "PR Merge Rate por Grupo"; e tabela "Medianas por Grupo")*

---

## 5. Resultados Obtidos

### 5.1 RQ1 — Adoção & Classificação

#### Nível de Adoção

Apenas **12,5% dos 1.000 repositórios mais populares** do GitHub possuem alguma política explícita de uso de IA nas contribuições. A grande maioria (87,5%) não aborda o tema em seus arquivos de contribuição.

| Tipo de Política | Repositórios | Percentual |
|-----------------|:------------:|:----------:|
| Ausência de Política | 875 | 87,5% |
| Uso Assistivo Permitido | 64 | 6,4% |
| Exigência de Disclosure | 31 | 3,1% |
| Proibição Total | 30 | 3,0% |

*(Ver: Dashboard, aba **RQ1 — Adoção & Classificação** — KPI Cards dos 4 tipos de política)*

*(Ver: Dashboard, aba **RQ1 — Adoção & Classificação** — gráficos "Distribuição dos 4 Tipos de Política" e "Quantidade de Repositórios por Tipo de Política")*

#### Tipos de Política

Dos 125 repositórios com política:

- **64 (51,2%)** adotam postura permissiva, mencionando IA mas sem impor restrições.
- **31 (24,8%)** exigem *disclosure* — o colaborador deve declarar o uso de IA, sem proibição.
- **30 (24,0%)** proíbem explicitamente contribuições geradas por IA.

Em termos de linguagem utilizada nos documentos, **80 repositórios (64%)** empregam linguagem restritiva e **45 (36%)** utilizam linguagem permissiva ou neutra.

*(Ver: Dashboard, aba **RQ1 — Adoção & Classificação** — gráfico "Linguagem da Política: Restritiva vs Permissiva")*

#### Arquivos e Termos Mais Frequentes

O arquivo mais utilizado para registrar políticas de IA é o `CONTRIBUTING.md`, presente na maioria dos casos. Em segundo lugar aparecem templates de Pull Request (`.github/PULL_REQUEST_TEMPLATE.md`), indicando que parte dos projetos opta por exigir declarações diretamente no momento da submissão de contribuições.

Os termos de IA mais frequentes nas políticas são variações de `AI-generated`, `LLM`, `generative AI` e `AI tools`, refletindo a terminologia dominante no discurso atual sobre o tema.

*(Ver: Dashboard, aba **RQ1 — Adoção & Classificação** — gráficos "Top 10 Arquivos com Política de IA" e "Termos de IA Mais Frequentes nas Políticas")*

---

### 5.2 RQ2 — Impacto no Engajamento

A tabela abaixo apresenta as medianas das métricas de engajamento para os grupos COM e SEM política de IA:

| Métrica | COM Política (mediana) | SEM Política (mediana) | Delta |
|---------|:---------------------:|:---------------------:|:-----:|
| PRs Abertos | 133,5 | 45,5 | +88,0 |
| Issues Abertas | 427,0 | 174,0 | +253,0 |
| Colaboradores Únicos | 97,5 | 91,0 | +6,5 |
| Avg Comentários em PRs | 2,0 | 1,4 | +0,6 |
| Avg Comentários em Issues | 4,1 | 3,1 | +1,0 |

Repositórios COM política de IA apresentam consistentemente **maior volume de contribuições** em todas as métricas analisadas. O delta mais expressivo ocorre nas issues abertas (+253 em mediana), sugerindo que projetos com política de IA são proporcionalmente mais ativos.

*(Ver: Dashboard, aba **RQ2 — Engajamento** — KPI Cards "Medianas — COM Política vs SEM Política")*

*(Ver: Dashboard, aba **RQ2 — Engajamento** — gráficos "PRs Abertos por Tipo de Política" e "Issues Abertas por Tipo de Política")*

*(Ver: Dashboard, aba **RQ2 — Engajamento** — gráficos "Colaboradores Únicos por Tipo", "Média de Comentários em PRs" e "Média de Comentários em Issues"; e tabela "Medianas por Tipo de Política")*

A análise por tipo de política revela que repositórios com **Proibição Total** e **Exigência de Disclosure** tendem a apresentar valores mais elevados de volume de contribuições, enquanto os de **Uso Assistivo Permitido** apresentam valores mais próximos ao grupo sem política. Isso sugere que a adoção de políticas mais rígidas está associada a projetos com maior maturidade e movimento de contribuições — o que faz sentido, pois são projetos com mais a perder em termos de qualidade do código.

---

### 5.3 RQ3 — Impacto na Colaboração

| Métrica | COM Política (mediana) | SEM Política (mediana) | Delta |
|---------|:---------------------:|:---------------------:|:-----:|
| PR Merge Rate (%) | 75,27 | 69,61 | +5,66 |
| Ciclo Mediano de PR (h) | 16,93 | 20,45 | −3,52 |
| 1ª Resposta em PRs (h) | 2,68 | 4,04 | −1,36 |
| 1ª Resposta em Issues (h) | 11,62 | 18,57 | −6,95 |
| Avg Reviews até Aprovação | 1,92 | 1,43 | +0,49 |

Projetos COM política de IA apresentam **maior taxa de merge** (+5,66 p.p.), **menor tempo de ciclo de PR** (−3,52 h), **menor tempo de 1ª resposta** tanto em PRs (−1,36 h) quanto em issues (−6,95 h). O único indicador desfavorável é a média de reviews até aprovação, ligeiramente maior (+0,49).

*(Ver: Dashboard, aba **RQ3 — Colaboração** — KPI Cards "Medianas — COM Política vs SEM Política")*

*(Ver: Dashboard, aba **RQ3 — Colaboração** — gráficos "PR Merge Rate por Tipo de Política" e "Tempo Mediano de Ciclo de PR")*

*(Ver: Dashboard, aba **RQ3 — Colaboração** — gráficos "1ª Resposta em PRs", "1ª Resposta em Issues" e "Média de Reviews até Aprovação"; e tabela "Medianas por Tipo de Política")*

O padrão de maior eficiência em projetos COM política reforça a interpretação de que esses repositórios possuem processos de contribuição mais estruturados, com mantenedores mais ativos e diretrizes mais claras — dos quais a política de IA é apenas um elemento.

---

## 6. Discussão das Hipóteses

### 6.1 Confronto com as Hipóteses Iniciais

| RQ | Hipótese inicial | Resultado observado | Alinhado? |
|----|-----------------|---------------------|:---------:|
| RQ1 | Adoção baixa; predominância de *disclosure* sobre proibição | Adoção de 12,5%; Uso Assistivo (51,2%) predomina; Disclosure (24,8%) e Proibição Total (24,0%) empatados | ✓ Parcial |
| RQ2 | COM política → maior volume de contribuições | COM política apresenta mediana de PRs (+88) e issues (+253) significativamente maiores | ✓ |
| RQ3 | COM política → maior eficiência no fluxo | Merge Rate maior, ciclo de PR e tempo de resposta menores em projetos COM política | ✓ |

### 6.2 Análise das Hipóteses

**RQ1 — A adoção é baixa, mas o tipo dominante surpreende.**

A hipótese de adoção baixa se confirmou — apenas 12,5% dos repositórios têm política explícita. No entanto, esperávamos que o tipo *Disclosure* fosse o mais comum. O resultado mostra que **Uso Assistivo Permitido** domina (51,2% dos casos com política), o que indica que a maioria dos projetos que menciona IA o faz de forma informativa, sem impor obrigações ao contribuidor. A distribuição quase igualitária entre *Disclosure* (24,8%) e *Proibição Total* (24,0%) indica uma polarização: projetos que efetivamente regulam o tema tendem a adotar posições opostas.

**RQ2 — Política está associada a maior engajamento, não menor.**

A hipótese era de que projetos com política seriam mais ativos, o que se confirmou com margem expressiva. O delta de +253 issues abertas em mediana é o resultado mais robusto do estudo. Uma interpretação plausível é que projetos suficientemente grandes para sentir a necessidade de regulamentar o uso de IA são justamente os que já possuem alta demanda de contribuição — a política seria efeito, não causa, da maior atividade.

**RQ3 — Política está associada a processos mais eficientes.**

A hipótese se confirmou. Projetos COM política respondem mais rápido (−1,36h em PRs, −6,95h em issues), têm ciclo de PR mais curto e maior taxa de merge. O único indicador contrário — mais reviews até aprovação (+0,49) — pode refletir um processo de revisão mais rigoroso, o que é coerente com projetos que preocupam-se em formalizar diretrizes de contribuição.

### 6.3 Limitações

- A **detecção de políticas por regex** pode gerar falsos positivos (repositórios que mencionam IA sem intenção regulatória) e falsos negativos (repositórios com políticas implícitas não capturadas pelos termos buscados).
- A **classificação em tipos** baseia-se em palavras-chave, não em leitura semântica completa — casos borderline podem ser alocados incorretamente.
- A **amostragem temporal** das métricas de PR e issues introduz uma margem de erro de até 10% (nível de confiança 95%), adequada para análise exploratória mas insuficiente para inferências causais precisas.
- Correlação entre presença de política e métricas de engajamento/colaboração **não implica causalidade**: projetos mais maduros tendem tanto a ter política quanto a ter melhores processos, sendo a maturidade a variável de confusão mais provável.

---

## 7. Conclusão

Este estudo investigou a adoção de políticas de uso de IA em contribuições open source e seu impacto nas dinâmicas de engajamento e colaboração de 1.000 repositórios populares do GitHub, utilizando técnicas de Business Intelligence para exploração e visualização dos dados.

### Principais Achados

- Apenas **12,5% dos repositórios** possuem política explícita de uso de IA, indicando que o tema ainda está em fase inicial de regulamentação na comunidade open source.
- Entre os que adotam política, predomina o **Uso Assistivo Permitido** (51,2%), seguido por Exigência de Disclosure (24,8%) e Proibição Total (24,0%) — revelando uma divisão clara entre projetos que permitem e os que restringem o uso de IA.
- Repositórios COM política apresentam **maior volume de contribuições** (PRs e issues), sugerindo que são projetos com maior movimento e, por consequência, maior necessidade de governança.
- Projetos COM política exibem **processos de contribuição mais eficientes**: maior taxa de merge, menor tempo de ciclo de PR e respostas mais rápidas a PRs e issues.

---

*Maio de 2026 | Laboratório de Experimentação de Software — PUC Minas*
