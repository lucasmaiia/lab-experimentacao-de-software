# LAB03 — Sprint 01

Seleção de repositórios e criação dos scripts de coleta de PRs e métricas para análise de code review.

## Pré-requisitos

- Python 3.10+
- Biblioteca `python-dotenv` (`pip install python-dotenv`)
- Token GitHub configurado em `LAB01/.env`:
  ```
  GITHUB_TOKEN=ghp_xxxxx
  ```

## Estrutura

| Arquivo | Descrição |
|---|---|
| `coleta_repos.py` | Seleciona os 200 repositórios mais populares com ≥100 PRs (MERGED+CLOSED) |
| `coleta_prs.py` | Coleta PRs e métricas de cada repositório selecionado |
| `repositorios.csv` | Lista dos repositórios selecionados (gerado) |
| `pull_requests.csv` | Dataset de PRs com métricas (gerado) |

## Como executar

### 1. Coleta de repositórios

```bash
cd LAB03/sprint01
python coleta_repos.py
```

Gera `repositorios.csv` com os 200 repositórios mais populares do GitHub que possuem pelo menos 100 PRs (MERGED + CLOSED).

### 2. Coleta de Pull Requests

```bash
python coleta_prs.py
```

Para cada repositório em `repositorios.csv`, coleta até 500 PRs elegíveis e salva em `pull_requests.csv`.

**Filtros aplicados:**
- Status: MERGED ou CLOSED
- Pelo menos 1 review
- Tempo de análise > 1 hora (criação → merge/close)

**Suporte a retomada:** Se o script for interrompido, basta executá-lo novamente — ele pula repositórios já coletados.

## Métricas coletadas

| Métrica | Coluna no CSV | Descrição |
|---|---|---|
| Tamanho | `files_changed`, `additions`, `deletions` | Arquivos alterados, linhas adicionadas/removidas |
| Tempo de análise | `analysis_time_hours` | Intervalo criação → merge/close em horas |
| Descrição | `body_char_count` | Caracteres do corpo do PR (markdown) |
| Interações | `participants_count`, `comments_count` | Participantes e comentários |
| Revisões | `review_count` | Total de revisões realizadas |
| Status | `state` | MERGED ou CLOSED |

## Critérios de seleção

### Repositórios
- Top 200 por estrelas no GitHub
- ≥100 PRs com status MERGED ou CLOSED

### Pull Requests
- Status MERGED ou CLOSED
- ≥1 review
- Tempo de análise > 1 hora (exclui revisões automatizadas por bots/CI)
