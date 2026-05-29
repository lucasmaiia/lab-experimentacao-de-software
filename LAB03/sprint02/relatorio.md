# Lab 03 - Code Review em Repositórios Open Source
## Relatório - Sprint 02

**Disciplina:** Laboratório de Experimentação de Software  
**Curso:** Engenharia de Software - PUC Minas  
**Autores:** Lucas Maia, Leandro Caldas 

---

## 1. Introdução e Hipóteses Iniciais

A atividade de *code review* é um dos pilares dos processos ágeis modernos. No GitHub, ela se materializa por meio de *Pull Requests* (PRs): um colaborador propõe uma mudança, revisores avaliam e, ao final, o PR é mesclado (`MERGED`) ou rejeitado (`CLOSED`). Compreender quais fatores influenciam esse desfecho ajuda equipes a submeter contribuições com maior chance de aceitação e projetos a ajustar seus fluxos de revisão.

Este trabalho analisa PRs de **200 repositórios populares do GitHub** (os de maior número de estrelas) que possuem pelo menos 100 PRs (MERGED + CLOSED) e passaram por ao menos uma revisão humana (tempo de análise > 1 hora, para excluir bots e CI/CD automático).

### Hipóteses por questão de pesquisa

| RQ | Pergunta resumida | Hipótese |
|----|-------------------|----------|
| RQ01 | Tamanho × status | PRs menores (menos arquivos e linhas) têm maior chance de serem aceitos. Revisores tendem a rejeitar ou ignorar PRs volumosos por serem mais custosos de avaliar. Correlação negativa esperada. |
| RQ02 | Tempo × status | PRs que ficam abertos por muito tempo provavelmente acumulam conflitos ou perdem relevância, levando a rejeição. Correlação negativa esperada (mais tempo → mais chance de CLOSED). |
| RQ03 | Descrição × status | Descrições detalhadas demonstram cuidado do autor e facilitam a revisão, aumentando a chance de aceitação. Correlação positiva esperada. |
| RQ04 | Interações × status | PRs com mais participantes e comentários podem refletir tanto interesse da comunidade (positivo) quanto controvérsia (negativo). Hipótese incerta; leve correlação positiva esperada, pois engajamento costuma indicar relevância. |
| RQ05 | Tamanho × revisões | PRs maiores exigem mais idas e vindas entre autor e revisores. Correlação positiva esperada. |
| RQ06 | Tempo × revisões | Mais ciclos de revisão naturalmente prolongam o tempo de análise. Correlação positiva esperada (revisões causam tempo, não o contrário). |
| RQ07 | Descrição × revisões | Uma descrição mais completa pode reduzir dúvidas e diminuir o número de revisões necessárias. Hipótese de correlação negativa fraca, mas incerta. |
| RQ08 | Interações × revisões | Mais participantes e comentários devem co-ocorrer com mais revisões, pois todos são sinais de engajamento ativo. Correlação positiva forte esperada. |

---

## 2. Metodologia

### 2.1 Criação do Dataset

O dataset foi construído em duas etapas:

1. **Seleção de repositórios** (`coleta_repos.py`): consulta à API GraphQL do GitHub para obter os 200 repositórios com maior número de estrelas que possuam ≥ 100 PRs (MERGED + CLOSED).

2. **Coleta de PRs** (`coleta_prs.py`): para cada repositório, foram coletados até 500 PRs (priorizando MERGED, depois CLOSED) com os seguintes filtros:
   - Status: `MERGED` ou `CLOSED`
   - Pelo menos **1 revisão** (`review.totalCount ≥ 1`)
   - Tempo de análise **> 1 hora** (para excluir respostas automáticas de bots/CI)

### 2.2 Métricas Coletadas

| Dimensão | Métrica | Campo no CSV |
|----------|---------|--------------|
| Tamanho | Arquivos alterados | `files_changed` |
| Tamanho | Linhas adicionadas | `additions` |
| Tamanho | Linhas removidas | `deletions` |
| Tempo | Horas de análise (criação → merge/close) | `analysis_time_hours` |
| Descrição | Caracteres no corpo do PR | `body_char_count` |
| Interações | Número de participantes | `participants_count` |
| Interações | Número de comentários | `comments_count` |
| Variável dependente A | Status do PR | `state` (MERGED / CLOSED) |
| Variável dependente B | Número de revisões | `review_count` |

### 2.3 Análise Estatística

Para responder às questões de pesquisa utilizamos o **coeficiente de correlação de Spearman** (ρ), com o seguinte raciocínio:

- As distribuições de métricas de repositórios open-source são tipicamente **assimétricas e de cauda longa** (e.g., um PR pode ter 1 arquivo alterado ou 500), tornando o teste de Pearson inadequado (pressupõe normalidade).
- Spearman opera sobre **postos (ranks)** e é robusto a outliers, sendo indicado para escalas ordinais e distribuições não-normais.
- Para comparação de grupos (MERGED × CLOSED), complementamos com o teste de **Mann-Whitney U** (equivalente não-paramétrico do t-test), que confirma se a diferença de medianas é estatisticamente significativa.

O nível de significância adotado é **α = 0,05**. Correlações são reportadas com o coeficiente ρ e o p-valor correspondente.

---

## 3. Resultados

> **Instruções:** execute `python analise.py` após rodar `coleta_prs.py` para gerar os valores abaixo automaticamente. Os gráficos são salvos em `figuras/`.

### 3.1 Estatísticas Descritivas

Dataset final: **50.981 PRs de 191 repositórios** (45.213 MERGED e 5.768 CLOSED).

| Métrica | Mediana geral | Mediana MERGED | Mediana CLOSED |
|---------|:-------------:|:--------------:|:--------------:|
| `files_changed` | 2 | 2 | 2 |
| `additions` | 26 | 26 | 22 |
| `deletions` | 5 | 5 | 2 |
| `analysis_time_hours` | 29,87 h | 26,45 h | 115,70 h |
| `body_char_count` | 802 | 795 | 864 |
| `participants_count` | 2 | 2 | 3 |
| `comments_count` | 1 | 1 | 2 |
| `review_count` | 1 | - | - |

PRs MERGED ficam abertos por ~26 horas em mediana, enquanto PRs CLOSED levam ~116 horas (~5 dias). Todos os resultados do teste Mann-Whitney U foram estatisticamente significativos (p < 0,001), indicando que as distribuições de MERGED e CLOSED diferem de forma robusta em todas as métricas.

### 3.2 Dimensão A - Feedback Final (Status do PR)

#### RQ01 - Tamanho × Status

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `files_changed` | +0,0788 | < 0,001 | *** |
| `additions` | +0,0248 | < 0,001 | *** |
| `deletions` | +0,0825 | < 0,001 | *** |

**Interpretação:** Contrário à hipótese inicial, as três métricas de tamanho apresentaram correlação **positiva** (embora fraca) com o status MERGED. PRs com mais arquivos e linhas alteradas têm ligeiramente maior chance de ser aceitos. Nos repositórios mais populares, contribuições substanciais geralmente chegam com maior maturidade e contexto, facilitando a aprovação. Medianas MERGED/CLOSED são iguais para `files_changed` (2/2), mas MERGED tem mais linhas adicionadas (26 vs 22) e removidas (5 vs 2).

---

#### RQ02 - Tempo de Análise × Status

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `analysis_time_hours` | −0,1650 | < 0,001 | *** |

**Interpretação:** Correlação negativa moderada - alinhada com a hipótese. PRs MERGED têm mediana de ~26 horas; PRs CLOSED têm mediana de ~116 horas (~5 dias). PRs rejeitados ficam abertos por mais tempo, acumulando conflitos ou perdendo relevância. O efeito é real mas mais moderado do que sugeriam os dados preliminares (que incluíam PRs abandonados por anos).

---

#### RQ03 - Descrição × Status

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `body_char_count` | −0,0189 | < 0,001 | *** |

**Interpretação:** Correlação **negativa** fraca - contrária à hipótese. No dataset completo, PRs CLOSED têm descrição mediana ligeiramente maior (864 vs 795 caracteres para MERGED). O efeito é pequeno, mas estatisticamente significativo. Uma possível explicação: autores de PRs que serão rejeitados investem mais texto tentando justificar a contribuição, enquanto PRs bem aceitos muitas vezes são auto-explicativos pelo código.

---

#### RQ04 - Interações × Status

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `participants_count` | −0,0846 | < 0,001 | *** |
| `comments_count` | −0,1158 | < 0,001 | *** |

**Interpretação:** Contrário à hipótese, ambas as métricas de interação apresentaram correlação **negativa** com o status MERGED. PRs CLOSED têm mediana de 3 participantes e 2 comentários, enquanto MERGED têm mediana de 2 e 1. Muita discussão pode indicar controvérsia ou resistência, não engajamento positivo. PRs bem direcionados são aceitos com pouca discussão; PRs problemáticos acumulam objeções antes de serem fechados.

---

### 3.3 Dimensão B - Número de Revisões

#### RQ05 - Tamanho × Revisões

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `files_changed` | +0,2538 | < 0,001 | *** |
| `additions` | +0,3362 | < 0,001 | *** |
| `deletions` | +0,1678 | < 0,001 | *** |

**Interpretação:** Correlação positiva moderada a forte - alinhada com a hipótese. PRs maiores recebem mais revisões. O efeito é mais pronunciado em linhas adicionadas (ρ = +0,34), o que faz sentido: adicionar código gera mais dúvidas e sugestões do que remover.

---

#### RQ06 - Tempo × Revisões

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `analysis_time_hours` | +0,1783 | < 0,001 | *** |

**Interpretação:** Correlação positiva fraca - alinhada com a hipótese. PRs com mais revisões ficam abertos por mais tempo, pois cada ciclo de revisão → ajuste → nova revisão consome tempo adicional. O efeito é real mas modesto, sugerindo que outros fatores (complexidade do domínio, disponibilidade dos revisores) também influenciam o tempo.

---

#### RQ07 - Descrição × Revisões

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `body_char_count` | +0,1813 | < 0,001 | *** |

**Interpretação:** Correlação positiva fraca a moderada - **contrária à hipótese** (esperávamos negativa ou nula). PRs com descrições mais longas recebem mais revisões. PRs complexos o suficiente para exigir explicação detalhada também são complexos o suficiente para demandar múltiplos ciclos de revisão. A descrição longa não substitui o processo iterativo.

---

#### RQ08 - Interações × Revisões

| Métrica | ρ (Spearman) | p-valor | Significância |
|---------|:------------:|:-------:|:-------------:|
| `participants_count` | +0,3779 | < 0,001 | *** |
| `comments_count` | +0,2673 | < 0,001 | *** |

**Interpretação:** Correlação positiva moderada a forte - alinhada com a hipótese. Mais participantes e comentários co-ocorrem fortemente com mais revisões. São manifestações do mesmo fenômeno: PRs que atraem atenção da comunidade geram mais engajamento em todas as dimensões. Este é o resultado com maior magnitude para a dimensão B.

---

## 4. Discussão

### 4.1 Confronto com as Hipóteses

| RQ | Hipótese | Resultado | Alinhado? |
|----|----------|-----------|:---------:|
| RQ01 | Correlação negativa (PRs menores → mais aceitos) | Positiva fraca (+0,03 a +0,08) | ✗ |
| RQ02 | Correlação negativa (mais tempo → mais rejeitados) | Negativa moderada (−0,17) | ✓ |
| RQ03 | Correlação positiva fraca (mais descrição → mais aceitos) | Negativa fraca (−0,02) | ✗ |
| RQ04 | Leve positiva (mais interações → mais aceitos) | Negativa (−0,08 e −0,12) | ✗ |
| RQ05 | Positiva (PRs maiores → mais revisões) | Positiva moderada (+0,17 a +0,34) | ✓ |
| RQ06 | Positiva (mais revisões → mais tempo) | Positiva fraca (+0,18) | ✓ |
| RQ07 | Negativa fraca (mais descrição → menos revisões) | Positiva fraca (+0,18) | ✗ |
| RQ08 | Positiva forte (mais interações → mais revisões) | Positiva forte (+0,27 e +0,38) | ✓ |

**Principais surpresas:**

- **RQ01:** Esperávamos que PRs menores fossem mais aceitos. O resultado positivo (embora fraco) pode refletir um viés de seleção nos 200 repositórios mais populares: projetos maduros tendem a aceitar contribuições substanciais e rejeitar patches triviais ou mal encaixados.

- **RQ03:** No dataset completo, PRs CLOSED têm descrições ligeiramente maiores (864 vs 795 chars), invertendo o que os dados preliminares sugeriam. Autores de PRs que serão rejeitados podem investir mais texto tentando justificar a contribuição.

- **RQ04:** Mais participantes e comentários estão associados a PRs **rejeitados**, não aceitos. Controvérsia gera discussão. PRs simples e bem direcionados são aceitos com poucos comentários; PRs problemáticos acumulam objeções antes de serem fechados.

- **RQ07:** Descrições mais longas estão associadas a **mais** revisões (ρ = +0,18), ao contrário do esperado. PRs complexos que precisam de explicação detalhada também exigem mais ciclos de revisão.

### 4.2 Limitações

- A amostra cobre **191 dos 200 repositórios** selecionados (9 não puderam ser coletados por erros de API) e é restrita aos **mais populares** (maior número de estrelas), o que pode não representar projetos open-source menos conhecidos.
- Projetos com fluxos de CI/CD muito automatizados podem ter distorcido o filtro de "revisão humana" mesmo com o corte de 1 hora.
- `body_char_count` mede quantidade de texto, não qualidade da descrição.
- Correlação não implica causalidade: a relação entre, por exemplo, número de comentários e status pode ser mediada por fatores não capturados (complexidade do domínio, política do projeto, etc.).

---
