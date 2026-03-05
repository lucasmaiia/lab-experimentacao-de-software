# Laboratório 01 — Características de Repositórios Populares no GitHub

## 1. Introdução e Hipóteses Informais

Este trabalho analisa os **1.000 repositórios com maior número de estrelas** no GitHub, com o objetivo de entender padrões de desenvolvimento, contribuição e manutenção em projetos open-source populares.

A coleta foi feita via API GraphQL do GitHub, buscando métricas como idade do repositório, pull requests aceitas, releases, dias desde o último push, linguagem primária e razão de issues fechadas.

### Hipóteses informais (antes de ver os dados)

| # | Hipótese |
|---|---|
| H1 | Repositórios populares tendem a ser antigos — acumular estrelas leva tempo. Esperamos medianas acima de 5 anos provavelmente. |
| H2 | A contribuição externa (PRs) deve ser alta, mas desigual — projetos de código ativo recebem muito mais que repositórios de utilidades/livros/listas/documentação. |
| H3 | A maioria dos repositórios lança releases com frequência, mas esperamos grande variação: projetos de lista e recursos não têm releases. |
| H4 | Repositórios populares são frequentemente atualizados — espera-se mediana de poucos dias sem push. |
| H5 | Python deve dominar — é a linguagem mais popular globalmente. |
| H6 | A taxa de issues fechadas deve ser alta (>80%) — projetos ativos tendem a resolver issues. |

> **Observação sobre outliers:** A amostra é heterogênea. Entre os 1.000 repositórios mais estrelados há não apenas projetos de software ativo, mas também repositórios de **documentação** (*awesome-lists*, guias), **livros** (*free-programming-books*), **cursos** e **tutoriais**. Esses repositórios têm zero ou poucas PRs de código, nenhuma release e podem nunca receber atualizações de código mesmo com milhões de estrelas. Isso distorce métricas como PRs aceitas e total de releases, razão pela qual usamos **mediana** como medida principal.

---

## 2. Metodologia

### 2.1 Coleta de datos

Os dados foram coletados automaticamente pelo script `coleta.py`, que realiza requisições à API GraphQL do GitHub (`https://api.github.com/graphql`) usando autenticação via token (`Authorization: Bearer <token>` no cabeçalho HTTP). Nenhuma biblioteca de terceiros foi usada para consumir a API — apenas `urllib.request` e `json` da biblioteca padrão do Python.

**Query GraphQL utilizada** (campos coletados por repositório):

```
nameWithOwner | stargazerCount | createdAt | pushedAt
primaryLanguage { name }
pullRequests(states: MERGED) { totalCount }
releases { totalCount }
issues(states: OPEN) { totalCount }
issues(states: CLOSED) { totalCount }
```

**Sobre `pushedAt` vs `updatedAt`:** O campo `updatedAt` do GitHub é atualizado a cada novo *fork*, *star* ou *issue* — o que o tornaria sempre "agora" para repositórios populares. Por isso, usamos `pushedAt`, que registra o último *push* de código de fato.

**Paginação:** O cursor da API GraphQL é usado para navegar pelas páginas. Um intervalo de `0,5s` entre requisições foi inserido para respeitar os limites da API. O `PAGE_SIZE` foi definido como 10 por página para evitar erros `502 Bad Gateway` da API ao consultar campos de alta complexidade (como contagem de PRs e issues simultâneas).

### 2.2 Métricas derivadas calculadas no script

| Métrica | Cálculo |
|---|---|
| `age_years` | `(data_hoje - createdAt).days / 365.25` |
| `days_since_update` | `(data_hoje - pushedAt).days` (mínimo 0) |
| `issues_closed_ratio` | `closed / (open + closed)` |

### 2.3 Análise

O script `gerarHTML.py` lê o CSV gerado, calcula estatísticas descritivas (`mean`, `median`, `min`, `max`) via `statistics` da biblioteca padrão e com a ajuda de IA geramos um dashboard HTML interativo usando Chart.js. A mediana é usada como métrica principal para métricas com distribuição assimétrica (PRs, releases).

### 2.4 Limitações

- **Viés de popularidade:** a amostra reflete apenas os repositórios mais estrelados, que não são representativos do GitHub como um todo.
- **Repositórios não-software:** listas, livros e cursos estão entre os mais estrelados e distorcem métricas de código (PRs, releases, atualização).
- **Rate limit:** a coleta completa dos 1.000 repositórios leva alguns minutos por causa do `sleep` entre páginas.

---

## 3. Resultados

### Sprint 01 — 100 repositórios

**Tabela 1 — Estatísticas gerais (Sprint 01)**

| Métrica | N | Mediana | Média | Min | Max |
|---|---|---|---|---|---|
| Idade (anos) | 100 | 9,18 | 8,58 | 0,24 | 16,48 |
| PRs mergeadas | 100 | 1.703 | 7.227 | 0 | 69.274 |
| Releases | 100 | 15,5 | 140,52 | 0 | 1.000 |
| Dias s/ update | 100 | 0 | — | 0 | — |
| Razão issues fechadas | 100 | 0,91 | 0,77 | 0,0 | 1,0 |

> **Nota sobre "Dias s/ update" na Sprint 01:** Nessa coleta ainda era usado o campo `updatedAt` da API, que é atualizado a qualquer evento (estrela, fork, issue). Por isso o resultado foi zero para todos. A métrica foi corrigida na Sprint 02 para usar `pushedAt`.

**Tabela 2 — Top 10 linguagens (Sprint 01)**

| Linguagem | Repositórios |
|---|---|
| Python | 19 |
| TypeScript | 17 |
| N/A | 14 |
| JavaScript | 11 |
| C++ | 6 |
| Go | 5 |
| HTML | 4 |
| Rust | 4 |
| Shell | 3 |
| Java | 3 |

---

### Sprint 02 — 1.000 repositórios

**Tabela 3 — Estatísticas gerais (Sprint 02)**

| Métrica | N | Mediana | Média | Min | Max |
|---|---|---|---|---|---|
| Idade (anos) | 1.000 | 8,38 | 8,19 | 0,13 | 17,9 |
| PRs mergeadas | 1.000 | 739 | 3.955 | 0 | 94.643 |
| Releases | 1.000 | 40,5 | 120,64 | 0 | 1.000 |
| Dias s/ update | 1.000 | 2 | 111,99 | 0 | 2.284 |
| Razão issues fechadas | 1.000 | 0,87 | 0,77 | 0,0 | 1,0 |

> **Sobre a média vs mediana em PRs:** A média de 3.955 PRs contra mediana de 739 evidencia forte assimetria. Projetos como `freeCodeCamp` (27.000+ PRs) ou grandes frameworks inflam a média consideravelmente. A mediana de 739 representa melhor o repositório "típico" nessa amostra.

> **Sobre releases:** mediana 40,5 mas max 1.000 (limitado pela API). Projetos como VS Code, Node.js ou pacotes npm têm centenas de releases. Repositórios de documentação têm zero.

> **Sobre dias s/ update:** mediana de 2 dias, mas máximo de 2.284 (mais de 6 anos). Os extremos são repositórios abandonados que ainda acumulam estrelas por referência histórica.

**Tabela 4 — Top 10 linguagens (Sprint 02)**

| Linguagem | Repositórios |
|---|---|
| Python | 200 |
| TypeScript | 160 |
| JavaScript | 115 |
| N/A | 95 |
| Go | 77 |
| Rust | 54 |
| Java | 47 |
| C++ | 46 |
| C | 25 |
| Jupyter Notebook | 23 |

> **Sobre N/A (95 repositórios):** Repositórios sem linguagem identificada são, em sua maioria, *awesome-lists*, livros e tutoriais — como `sindresorhus/awesome`, `EbookFoundation/free-programming-books`, `jwasham/coding-interview-university`. Esses projetos distorcem métricas de código.

---

### RQ 07 (Bônus) — Comparativo por linguagem (Sprint 02)

**Tabela 5 — Medianas por linguagem**

| Linguagem | Repos | Mediana PRs | Mediana Releases | Mediana dias s/ update |
|---|---|---|---|---|
| Python | 200 | 631 | 23,5 | 3 |
| TypeScript | 160 | 2.582,5 | 158 | 0 |
| JavaScript | 115 | 576 | 40 | 5 |
| N/A | 95 | 129 | 0 | 129 |
| Go | 77 | 1.690 | 132 | 0 |

> TypeScript e Go se destacam com altíssima atividade em PRs e releases. O grupo N/A confirma a hipótese: sem linguagem de programação definida, a atividade de código é mínima (mediana de 0 releases e 129 dias sem push).

---

### Comparativo entre sprints

**Tabela 6 — Sprint 01 vs Sprint 02 (medianas)**

| Métrica | Sprint 01 (100) | Sprint 02 (1.000) | Δ |
|---|---|---|---|
| Idade (anos) | 9,18 | 8,38 | −0,80 |
| PRs mergeadas | 1.703 | 739 | −964 |
| Releases | 15,5 | 40,5 | +25 |
| Razão issues fechadas | 0,91 | 0,87 | −0,04 |

A queda na mediana de PRs ao expandir para 1.000 repositórios indica que os top 100 concentram os projetos com atividade mais intensa. O aumento na mediana de releases provavelmente reflete a inclusão de projetos de ferramentas e bibliotecas (que fazem muitas releases pequenas) que entram quando a amostra cresce.

---

## 4. Discussão das Hipóteses

| Hipótese | Resultado | Conclusão |
|---|---|---|
| H1 — Repositórios populares são antigos | Mediana ≈ 8–9 anos | **Confirmada.** A grande maioria tem mais de 5 anos. |
| H2 — Alta contribuição externa, mas desigual | Mediana 739 PRs, mas desvio enorme (máx. 94.643) | **Confirmada parcialmente.** A contribuição existe, mas a distribuição é muito assimétrica. Repositórios de lista/documentação têm zero PRs. |
| H3 — Releases frequentes, mas com variação | Mediana 40,5, máx. 1.000 (limitado pela API), 0 para repositórios de lista | **Confirmada.** Grande variação. Projetos de software ativo lançam muitas releases; projetos de conteúdo, nenhuma. |
| H4 — Atualizações frequentes | Mediana 2 dias, mas máx. 2.284 dias | **Confirmada para a maioria.** Há repositórios abandonados (outliers) que distorcem a média (111 dias). |
| H5 — Python, JS e TS dominam | Python 200, TS 160, JS 115 | **Confirmada.** As três respondem por 47,5% dos repositórios. |
| H6 — Alta taxa de issues fechadas (>80%) | Mediana 0,87 (87%) | **Confirmada.** A maioria dos projetos resolve a maior parte das issues abertas. |
