# Lab 05 — GraphQL vs REST: Um Experimento Controlado
## Sprint 01 — Desenho e Preparação do Experimento

**Disciplina:** Laboratório de Experimentação de Software  
**Curso:** Engenharia de Software — PUC Minas  
**Data:** Junho de 2026

---

## Índice

1. [Desenho do Experimento](#1-desenho-do-experimento)
   - [A. Hipóteses Nula e Alternativa](#a-hipóteses-nula-e-alternativa)
   - [B. Variáveis Dependentes](#b-variáveis-dependentes)
   - [C. Variáveis Independentes](#c-variáveis-independentes)
   - [D. Tratamentos](#d-tratamentos)
   - [E. Objetos Experimentais](#e-objetos-experimentais)
   - [F. Tipo de Projeto Experimental](#f-tipo-de-projeto-experimental)
   - [G. Quantidade de Medições](#g-quantidade-de-medições)
   - [H. Ameaças à Validade](#h-ameaças-à-validade)
2. [Preparação do Experimento](#2-preparação-do-experimento)
   - [Cenário Experimental](#cenário-experimental)
   - [Consultas Equivalentes](#consultas-equivalentes)
   - [Como Executar](#como-executar)

---

## 1. Desenho do Experimento

### A. Hipóteses Nula e Alternativa

O experimento aborda duas perguntas de pesquisa independentes, cada uma com seu par de hipóteses.

#### RQ1 — Tempo de Resposta

> **H₀¹:** O tempo de resposta mediano de consultas GraphQL é igual ao tempo de resposta mediano de consultas REST.  
> `mediana(T_GraphQL) = mediana(T_REST)`
>
> **H₁¹:** O tempo de resposta mediano de consultas GraphQL é diferente do tempo de resposta mediano de consultas REST.  
> `mediana(T_GraphQL) ≠ mediana(T_REST)`

A hipótese alternativa é bicaudal porque o efeito do tipo de API sobre o tempo não é trivialmente previsível: consultas GraphQL retornam menos dados (menor transferência) mas exigem parsing de query no servidor (maior overhead de processamento).

#### RQ2 — Tamanho da Resposta

> **H₀²:** O tamanho mediano das respostas GraphQL é igual ao tamanho mediano das respostas REST.  
> `mediana(S_GraphQL) = mediana(S_REST)`
>
> **H₁²:** O tamanho mediano das respostas GraphQL é menor que o tamanho mediano das respostas REST.  
> `mediana(S_GraphQL) < mediana(S_REST)`

A hipótese alternativa é unicaudal (menor) porque o GraphQL permite selecionar exatamente os campos desejados, eliminando o *over-fetching* estrutural das APIs REST que retornam objetos completos independentemente do que o cliente precisa.

---

### B. Variáveis Dependentes

| # | Variável | Tipo | Unidade | Forma de Medição |
|---|----------|------|---------|-----------------|
| VD1 | Tempo de resposta | Contínua | Segundos | `time.perf_counter()` antes e após o recebimento completo da resposta HTTP |
| VD2 | Tamanho da resposta | Contínua | Bytes | `len(response.content)` — tamanho do corpo da resposta antes de qualquer descompressão cliente |

**Decisão sobre tamanho:** O tamanho é medido no corpo bruto da resposta (`Content-Length` efetivo), não no payload comprimido pelo transport. Isso é representativo do dado semanticamente transferido.

---

### C. Variáveis Independentes

| # | Variável | Tipo | Níveis | Papel |
|---|----------|------|--------|-------|
| VI1 | Tipo de API | Categórica | REST, GraphQL | Variável de tratamento (fator principal) |
| VI2 | Tipo de consulta | Categórica | repo_info, issues, pull_requests, commits | Fator de bloco — permite análise por tipo |
| VI3 | Repositório alvo | Categórica | 20 repos | Fator de bloco — controla variância entre objetos |

---

### D. Tratamentos

O experimento aplica **dois tratamentos** sobre o mesmo conjunto de objetos:

| Tratamento | Descrição | Endpoint |
|-----------|-----------|---------|
| **T₁ — REST** | Consulta via API REST do GitHub (v3), que retorna objetos completos com todos os campos disponíveis | `https://api.github.com/*` (GET) |
| **T₂ — GraphQL** | Consulta equivalente via API GraphQL do GitHub (v4), solicitando **apenas os campos semanticamente equivalentes** aos usados da resposta REST | `https://api.github.com/graphql` (POST) |

**Critério de equivalência:** Para cada tipo de consulta, a query GraphQL solicita exatamente as informações que um cliente típico extrairia da resposta REST. Isso modela o cenário real de uso e evidencia o *over-fetching* da abordagem REST.

---

### E. Objetos Experimentais

**Plataforma:** API pública do GitHub, que disponibiliza simultaneamente REST (v3) e GraphQL (v4) sobre os mesmos dados, garantindo comparabilidade.

**Repositórios alvo** (20 repositórios populares, diversificados por linguagem e domínio):

| # | Repositório | Linguagem principal |
|---|-------------|-------------------|
| 1 | facebook/react | JavaScript |
| 2 | vuejs/vue | JavaScript |
| 3 | angular/angular | TypeScript |
| 4 | tensorflow/tensorflow | Python/C++ |
| 5 | microsoft/vscode | TypeScript |
| 6 | flutter/flutter | Dart |
| 7 | kubernetes/kubernetes | Go |
| 8 | golang/go | Go |
| 9 | django/django | Python |
| 10 | rails/rails | Ruby |
| 11 | nodejs/node | JavaScript |
| 12 | rust-lang/rust | Rust |
| 13 | expressjs/express | JavaScript |
| 14 | pallets/flask | Python |
| 15 | tiangolo/fastapi | Python |
| 16 | spring-projects/spring-boot | Java |
| 17 | laravel/laravel | PHP |
| 18 | pytorch/pytorch | Python |
| 19 | scikit-learn/scikit-learn | Python |
| 20 | hashicorp/terraform | Go |

**Tipos de consulta** (4 tipos, todos com equivalência REST ↔ GraphQL):

| Tipo | REST endpoint | Dado retornado |
|------|--------------|---------------|
| `repo_info` | `GET /repos/{owner}/{repo}` | Metadados do repositório |
| `issues` | `GET /repos/{owner}/{repo}/issues?per_page=20&state=open` | 20 issues abertas |
| `pull_requests` | `GET /repos/{owner}/{repo}/pulls?per_page=20&state=open` | 20 PRs abertos |
| `commits` | `GET /repos/{owner}/{repo}/commits?per_page=20` | 20 commits recentes |

---

### F. Tipo de Projeto Experimental

**Projeto:** Experimento controlado com medidas repetidas (*within-subjects*), com dois fatores de bloco (tipo de consulta e repositório).

**Justificativa:**
- *Within-subjects*: os mesmos repositórios são submetidos a ambos os tratamentos (REST e GraphQL). Isso elimina a variância inter-objeto como fonte de confusão, aumentando o poder estatístico.
- **Comparação pareada:** para cada par `(repositório, tipo_de_consulta)`, cada repetição gera um par `(REST_time, GraphQL_time)` e `(REST_size, GraphQL_size)`. A análise estatística usa o **teste de Wilcoxon pareado** (não paramétrico), adequado para dados de tempo de resposta que costumam ter distribuição assimétrica.
- **Randomização da ordem:** em cada repetição, a ordem de execução REST → GraphQL vs GraphQL → REST é sorteada aleatoriamente para controlar efeitos de aprendizagem/cache do servidor.
- **Warm-up:** as primeiras `WARMUP_REPS` medições de cada par são descartadas para eliminar efeitos de cold-start (conexão TCP, JIT do servidor, etc.).

---

### G. Quantidade de Medições

| Dimensão | Valor |
|----------|-------|
| Repositórios | 20 |
| Tipos de consulta | 4 |
| Pares experimentais `(repo, tipo)` | 80 |
| Repetições por par por tratamento | 30 |
| Total de medições válidas esperadas | 80 × 30 × 2 = **4.800** |
| Medições de warm-up (descartadas) | 80 × 2 × 2 = 320 |
| Total de requisições | 5.120 |

**Justificativa das 30 repetições:** Com n=30 por par, o intervalo de confiança 95% para a mediana tem boa precisão e o teste de Wilcoxon tem poder estatístico ≥ 0,80 para efeitos médios (d ≈ 0,5). Além disso, ao agregar os 20 repositórios por tipo de consulta, obtemos 600 pares por tipo — suficiente para detectar diferenças pequenas.

**Estimativa de duração:** ~45 minutos (5.120 requisições × 0,5s de intervalo entre requisições + tempo de resposta).

---

### H. Ameaças à Validade

#### Validade Interna

| Ameaça | Descrição | Controle adotado |
|--------|-----------|-----------------|
| Variação de latência de rede | A latência entre cliente e servidor GitHub pode variar entre requisições | Medições pareadas e interleaved dentro de cada repetição minimizam o impacto de tendências temporais |
| Cache do servidor | O GitHub pode retornar respostas em cache para consultas repetidas, subestimando o tempo de processamento | Header `Cache-Control: no-cache, no-store` em todas as requisições |
| Rate limiting | A API do GitHub limita a 5.000 req/h (REST) e 5.000 pontos/h (GraphQL) | O script detecta `403/429` e aguarda o reset antes de continuar |
| Efeito de ordenação | Executar sempre REST antes de GraphQL (ou vice-versa) introduziria viés sistemático | A ordem é sorteada aleatoriamente em cada repetição |
| Cold-start | As primeiras medições podem ser mais lentas por ausência de conexão TCP estabelecida | Warm-up de 2 repetições descartadas por par |

#### Validade Externa

| Ameaça | Descrição |
|--------|-----------|
| Especificidade de plataforma | Os resultados são válidos para a API do GitHub; outras implementações de GraphQL/REST podem ter características diferentes (ex.: implementações próprias são mais leves que a infraestrutura do GitHub) |
| Seleção de repositórios | Os 20 repos são populares e com alta atividade; repositórios menores ou com menos issues/PRs podem apresentar comportamento diferente |
| Tipo de consulta | Foram selecionados 4 tipos de leitura simples; consultas de escrita (mutations), paginação profunda ou queries complexas com múltiplos níveis de relacionamento podem apresentar diferenças mais pronunciadas |

#### Validade de Construto

| Ameaça | Descrição |
|--------|-----------|
| Compressão HTTP | O `Content-Encoding: gzip` pode estar habilitado, fazendo com que o tamanho medido pelo cliente reflita o payload comprimido, não o dado semântico bruto; o GraphQL perderia parte de sua vantagem de tamanho nesse caso | 
| Tempo de resposta vs. throughput | O tempo de resposta mede a latência de uma única requisição; o impacto real em sistemas com alta concorrência pode ser diferente |
| Equivalência das queries | A decisão de quais campos solicitar no GraphQL afeta diretamente o tamanho da resposta; a seleção de campos foi feita para representar o que um cliente típico usaria |

#### Validade de Conclusão Estatística

| Ameaça | Descrição | Controle adotado |
|--------|-----------|-----------------|
| Não normalidade | Tempos de resposta tendem a ter distribuição assimétrica com cauda longa | Uso de mediana (em vez de média) e teste de Wilcoxon pareado (não paramétrico) |
| Múltiplos testes | Testamos 4 tipos de consulta × 2 métricas = 8 comparações | Reportar os p-valores individuais e aplicar correção de Bonferroni quando necessário |

---

## 2. Preparação do Experimento

### Cenário Experimental

```
GitHub API (mesma base de dados)
        │
        ├── REST v3 (GET)    ──────────────────────┐
        │   Retorna objeto completo (~50+ campos)  │
        │                                           │
        └── GraphQL v4 (POST) ────────────────────┐│
            Query com campos selecionados (~12 campos) ││
                                                   ││
                             ┌─────────────────────┘│
                             │     collector.py      │
                             │ ┌───────────────────┐ │
                             │ │ Para cada par      │ │
                             │ │ (repo, query_type):│ │
                             │ │  - 2 warm-up (skip)│ │
                             │ │  - 30 reps paired  │ │
                             │ │  - aleatoriza ordem│ │
                             │ └───────────────────┘ │
                             └───────────────────────┘
                                         │
                                    results.csv
                             (4.800 linhas × 8 colunas)
```

### Consultas Equivalentes

Para cada tipo de consulta, a tabela abaixo mostra o que o REST retorna vs. o que o GraphQL solicita:

#### `repo_info`

| API | Campos retornados | Tamanho típico |
|-----|------------------|----------------|
| REST | ~60 campos (id, node_id, name, full_name, private, owner{}, html_url, description, fork, url, forks_url, keys_url, collaborators_url, ... watchers_count, default_branch, permissions, network_count, subscribers_count, ...) | ~3–5 KB |
| GraphQL | 13 campos (name, nameWithOwner, description, stargazerCount, forkCount, openIssues, primaryLanguage, updatedAt, createdAt, watchers, defaultBranchRef, licenseInfo, diskUsage) | ~500–800 B |

#### `issues`

| API | Campos por item | Itens |
|-----|----------------|-------|
| REST | ~35 campos por issue (incluindo url, repository_url, html_url, events_url, labels_url, ...) | 20 |
| GraphQL | 8 campos por issue (number, title, state, createdAt, updatedAt, author.login, labels, comments.totalCount) | 20 |

#### `pull_requests`

| API | Campos por item | Itens |
|-----|----------------|-------|
| REST | ~40 campos por PR (incluindo diff_url, patch_url, issue_url, commits_url, ...) | 20 |
| GraphQL | 8 campos por PR (number, title, state, createdAt, updatedAt, author.login, reviewRequests, commits.totalCount) | 20 |

#### `commits`

| API | Campos por item | Itens |
|-----|----------------|-------|
| REST | ~20 campos por commit (sha, node_id, commit{}, url, html_url, comments_url, author{}, committer{}, parents[]) | 20 |
| GraphQL | 6 campos por commit (oid, messageHeadline, committedDate, author.name, author.email, additions, deletions) | 20 |

### Como Executar

#### Pré-requisitos

```bash
cd LAB05/sprint01/scripts
pip install -r requirements.txt
```

#### Configurar token

```bash
cp ../.env.example ../.env
# Editar .env e adicionar o token GitHub
```

O token precisa apenas do escopo `public_repo` (ou sem escopo para acesso somente-leitura a repos públicos).  
Gere em: https://github.com/settings/tokens

#### Executar coleta

```bash
python collector.py
```

O script salva `results.csv` em `LAB05/sprint01/scripts/` com as colunas:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `query_type` | string | Tipo de consulta (`repo_info`, `issues`, `pull_requests`, `commits`) |
| `object` | string | Repositório no formato `owner/repo` |
| `repetition` | int | Número da repetição (1–30) |
| `api_type` | string | `REST` ou `GraphQL` |
| `response_time_s` | float | Tempo de resposta em segundos |
| `response_size_bytes` | int | Tamanho da resposta em bytes |
| `status_code` | int | Código HTTP da resposta |
| `timestamp` | string | ISO 8601 — momento da medição |

#### Verificar saúde dos dados

```bash
python -c "
import pandas as pd
df = pd.read_csv('results.csv')
print(df.groupby(['query_type','api_type'])['response_time_s'].describe().round(4))
print(df.groupby(['query_type','api_type'])['response_size_bytes'].median().round(0))
"
```

---

*Junho de 2026 | Laboratório de Experimentação de Software — PUC Minas*
