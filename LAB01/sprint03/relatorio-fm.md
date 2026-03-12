# Análise das Características de Repositórios Populares no GitHub

**Autores**\
Lucas Maia\
Leandro Pacheco

------------------------------------------------------------------------

## Índice

-   Introdução e Hipóteses
-   Questões de Pesquisa (Objetivos)
-   Metodologia
-   Resultados Obtidos
-   Discussão das Hipóteses
-   Tomada de Decisão
-   Conclusão

------------------------------------------------------------------------

## 1. Introdução e Hipóteses

Este trabalho visa analisar os **1.000 repositórios com maior número de
estrelas no GitHub**, compreendendo os padrões de desenvolvimento,
fluxos de contribuição e ciclos de manutenção presentes nos projetos
open-source de maior relevância mundial.

O estudo foi desenvolvido ao longo de três sprints. Nas duas primeiras
etapas, foram realizadas coletas iniciais e uma primeira consolidação
das métricas. Já na Sprint 3, foram aplicadas correções metodológicas
importantes, refinando o processo de filtragem, coleta e interpretação
dos dados. Por isso, este relatório apresenta uma visão geral
consolidada, incorporando a evolução do experimento e considerando a
Sprint 3 como versão final corrigida da análise.

A coleta foi feita por meio da API GraphQL do GitHub, buscando métricas
como:

-   idade do repositório
-   total de pull requests aceitas
-   total de releases
-   tempo desde o último push
-   linguagem primária
-   razão de issues fechadas

Desde o início da análise, observou-se que a amostra dos repositórios
mais estrelados é bastante heterogênea. Entre eles estão não apenas
projetos de software ativo, mas também repositórios de documentação,
listas de recursos, livros, cursos, tutoriais e materiais educacionais.

Esses repositórios frequentemente apresentam poucas ou nenhuma PR de
código, ausência de releases e baixa atividade real de desenvolvimento,
mesmo acumulando milhões de estrelas. Isso cria distorções em métricas
tradicionais, razão pela qual adotamos a **mediana como principal medida
estatística**.

### Hipóteses

**H1:** Projetos massivamente populares tendem a ser antigos, visto que
acumular reconhecimento contínuo da comunidade leva vários anos.
Esperamos uma idade mediana superior a 5 anos.

**H2:** A adoção de contribuições externas (Pull Requests) deve ser
altíssima, porém assimétrica.

**H3:** A maior parte dos repositórios lança releases frequentemente.

**H4:** O ecossistema open-source do topo do ranking é aquecido.

**H5:** Python, TypeScript e JavaScript devem dominar o ranking.

**H6:** A taxa de issues resolvidas deve ser elevada, ultrapassando a
margem de 80%.

------------------------------------------------------------------------

## 2. Questões de Pesquisa (Objetivos)

O presente experimento se destina a responder matematicamente e
visualmente às seguintes indagações:

-   **RQ01:** Sistemas populares são maduros ou antigos? (Idade do
    repositório)\
-   **RQ02:** Sistemas populares recebem muita contribuição externa?
    (Total de Pull Requests aceitas)\
-   **RQ03:** Sistemas populares lançam releases com frequência? (Total
    de releases)\
-   **RQ04:** Sistemas populares são atualizados com frequência? (Tempo
    em dias até a última atualização)\
-   **RQ05:** Sistemas populares são escritos nas linguagens mais
    populares? (Linguagem primária)\
-   **RQ06:** Sistemas populares possuem um alto percentual de issues
    fechadas? (Razão de issues resolvidas)\
-   **RQ07 (Bônus):** Sistemas escritos nas linguagens mais populares
    geram mais PRs, releases e atualizações?

------------------------------------------------------------------------

## 3. Metodologia

Os dados foram minerados automaticamente utilizando um script Python
chamado **coleta.py**, responsável por realizar requisições diretas à
**API GraphQL do GitHub** com autenticação por token.

**Autenticação utilizada:**

    Authorization: Bearer <token>

O consumo da API foi construído utilizando apenas bibliotecas padrão do
Python, principalmente:

-   `urllib.request`
-   `json`

### 3.1 Campos coletados por repositório

    nameWithOwner
    stargazerCount
    createdAt
    pushedAt
    primaryLanguage { name }
    pullRequests(states: MERGED) { totalCount }
    releases { totalCount }
    issues(states: OPEN) { totalCount }
    issues(states: CLOSED) { totalCount }

### 3.2 Evolução metodológica

Durante as Sprints 1 e 2, o experimento revelou limitações metodológicas
que precisaram ser corrigidas.

Na **Sprint 1**, a métrica de atualização utilizava `updatedAt`, que
também muda quando ocorre star ou issue.

Na **Sprint 2**, a métrica foi corrigida para `pushedAt`, que representa
o último push real.

Na **Sprint 3**, foi aplicada uma filtragem mais rigorosa da base.

### 3.3 Filtros aplicados na Sprint 3

Foram removidos repositórios que:

-   fossem forks
-   tivessem menos de 100 KB
-   estivessem arquivados
-   não possuíssem linguagem primária definida

### 3.4 Estratégia de paginação

-   Uso de cursor GraphQL\
-   Intervalo de **0,5s** entre requisições\
-   `PAGE_SIZE = 10`

### 3.5 Métricas derivadas

| Métrica              | Cálculo                                   |
|----------------------|-------------------------------------------|
| age_years            | (data_hoje - createdAt).days / 365.25    |
| days_since_update    | (data_hoje - pushedAt).days (mínimo 0)   |
| issues_closed_ratio  | closed / (open + closed)                 |
### 3.6 Análise e visualização

O script **gerarHTML.py** calcula estatísticas descritivas utilizando o
módulo `statistics` e gera um dashboard com **Chart.js**.

### 3.7 Limitações

-   A amostra inclui apenas repositórios mais estrelados
-   Alguns repositórios de conteúdo podem permanecer na base
-   A coleta depende das limitações da API do GitHub

------------------------------------------------------------------------

## 4. Resultados Obtidos

### 4.1 Sprint 1 - coleta inicial (100 repositórios)

| Métrica                 | N   | Mediana | Média  | Min  | Max   |
|-------------------------|-----|---------|--------|------|-------|
| Idade (anos)            | 100 | 9,18    | 8,58   | 0,24 | 16,48 |
| PRs mergeadas           | 100 | 1.703   | 7.227  | 0    | 69.274|
| Releases                | 100 | 15,5    | 140,52 | 0    | 1.000 |
| Dias sem update         | 100 | 0       | 0      | 0    | 0     |
| Razão issues fechadas   | 100 | 0,91    | 0,77   | 0,0  | 1,0   |

### Top linguagens

| Linguagem        | Repositórios |
|------------------|--------------|
| Python           | 19           |
| TypeScript       | 17           |
| N/A              | 14           |
| JavaScript       | 11           |
| C++              | 6            |
| Go               | 5            |
| HTML             | 4            |
| Rust             | 4            |
| Shell            | 3            |
| Java             | 3            |

------------------------------------------------------------------------

### 4.2 Sprint 2 - expansão para 1.000 repositórios

| Métrica                 | N     | Mediana | Média  | Min  | Max    |
|-------------------------|-------|---------|--------|------|--------|
| Idade (anos)            | 1.000 | 8,38    | 8,19   | 0,13 | 17,9   |
| PRs mergeadas           | 1.000 | 739     | 3.955  | 0    | 94.643 |
| Releases                | 1.000 | 40,5    | 120,64 | 0    | 1.000  |
| Dias sem update         | 1.000 | 2       | 111,99 | 0    | 2.284  |
| Razão issues fechadas   | 1.000 | 0,87    | 0,77   | 0,0  | 1,0    |

### Top linguagens

| Linguagem           | Repositórios |
|---------------------|--------------|
| Python              | 200          |
| TypeScript          | 160          |
| JavaScript          | 115          |
| N/A                 | 95           |
| Go                  | 77           |
| Rust                | 54           |
| Java                | 47           |
| C++                 | 46           |
| C                   | 25           |
| Jupyter Notebook    | 23           |
------------------------------------------------------------------------

### 4.3 Sprint 3 - versão final corrigida

| Métrica estudada                 | Respondentes (N) | Mediana | Min  | Max     |
|----------------------------------|------------------|--------|------|---------|
| Idade em anos                    | 1.000            | 8,35   | 0,14 | 16,94   |
| Total de Pull Requests aceitas   | 1.000            | 884    | 0    | 114.397 |
| Lançamentos (Releases)           | 1.000            | 50,5   | 0    | 1.000   |
| Dias sem atualização (Push)      | 1.000            | 1,15   | 0    | 2.227   |
| Razão de issues resolvidas       | 1.000            | 0,88   | 0,0  | 1,00    |

### Linguagens dominantes

| Linguagem   | Repositórios | Mediana PRs | Mediana Releases | Mediana dias sem update |
|-------------|--------------|-------------|------------------|--------------------------|
| Python      | 185          | 860         | 33               | 1,76                     |
| JavaScript  | 158          | 808         | 51,5             | 3,52                     |
| TypeScript  | 148          | 2.594       | 158              | 0,50                     |
| C++         | 118          | 971         | 38,5             | 1,39                     |
| Go          | 98           | 1.854       | 134              | 0,49                     |
  --------------------------------------------------------------------------


### 4.4 Comparação entre sprints

| Métrica                     | Sprint 1 | Sprint 2 | Sprint 3 |
|-----------------------------|----------|----------|----------|
| Idade mediana (anos)        | 9,18     | 8,38     | 8,35     |
| PRs medianas                | 1.703    | 739      | 884      |
| Releases medianas           | 15,5     | 40,5     | 50,5     |
| Dias sem update             | 0*       | 2        | 1,15     |
| Razão de issues fechadas    | 0,91     | 0,87     | 0,88     |

------------------------------------------------------------------------

## 5. Discussão das Hipóteses

**H1 --- Repositórios populares são maduros?**\
Confirmada.

**H2 --- Contribuições externas são altas?**\
Confirmada parcialmente.

**H3 --- Repositórios populares lançam releases com frequência?**\
Confirmada.

**H4 --- Repositórios populares são frequentemente atualizados?**\
Confirmada vigorosamente.

**H5 --- Linguagens populares dominam a base?**\
Confirmada.

**H6 --- A taxa de issues fechadas é alta?**\
Confirmada.

------------------------------------------------------------------------

## 6. Tomada de Decisão

Decisões metodológicas importantes:

-   substituição de `updatedAt` por `pushedAt`
-   uso da **mediana** como métrica principal
-   redução do `PAGE_SIZE` para 10
-   uso de `sleep` entre requisições
-   aplicação de filtros mais rigorosos na Sprint 3

Observou-se também que linguagens como **TypeScript e Go** apresentam
altos níveis de PRs e releases.

------------------------------------------------------------------------

## 7. Conclusão

Este laboratório confirmou que a popularidade no ecossistema moderno de
software não é um fenômeno casual.

Os repositórios mais populares do GitHub:

-   tendem a ser antigos
-   recebem grande quantidade de contribuições externas
-   são atualizados frequentemente
-   apresentam elevada taxa de resolução de issues
-   concentram-se em linguagens amplamente difundidas

Também ficou evidente que **número de estrelas não representa
necessariamente atividade real de desenvolvimento**.

A Sprint 3 foi essencial para corrigir limitações das etapas anteriores
e produzir uma análise metodologicamente mais robusta.
