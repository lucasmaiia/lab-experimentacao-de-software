# Estudo das Características de Qualidade de Sistemas Java

Laboratório de Experimentação de Software — Lab02\
**Alunos:** Leandro Pacheco, Lucas Maia\
**Professor:** Danilo de Quadros Maia Filho

---

## Índice

1. Introdução e Hipóteses
2. Questões de Pesquisa
3. Metodologia
4. Resultados Obtidos
5. Discussão das Hipóteses
6. Conclusão

---

## 1. Introdução e Hipóteses

Este trabalho investiga as **características de qualidade** de sistemas desenvolvidos em Java, analisando os **1.000 repositórios Java** mais populares do GitHub (por número de estrelas). O objetivo é verificar se existe correlação entre atributos de processo — popularidade, maturidade, atividade e tamanho — e a qualidade interna do código, medida por métricas estruturais extraídas com a ferramenta de análise estática **CK** (Chidamber & Kemerer).

A análise foi conduzida em duas sprints. Na **Sprint 01**, desenvolvemos os scripts de coleta via API do GitHub, o processo de clonagem e a execução da ferramenta CK sobre um repositório piloto (`macrozheng/mall`). Na **Sprint 02**, escalamos a análise para toda a base de 1.000 repositórios, extraímos as métricas de qualidade e realizamos a análise estatística.

### Hipóteses

**H1 — Popularidade implica qualidade?**\
Repositórios com mais estrelas tendem a ter código com menor acoplamento (CBO baixo) e maior coesão (LCOM baixo), dado que a visibilidade atrai mais scrutínio e contribuições de correção.

**H2 — Maturidade implica qualidade?**\
Repositórios mais antigos acumulam mais refatorações ao longo dos anos, resultando em métricas de qualidade melhores.

**H3 — Atividade e qualidade estão correlacionadas?**\
Repositórios com mais releases tendem a ter melhor qualidade, pois ciclos frequentes de entrega incentivam manutenção contínua.

**H4 — Repositórios maiores têm pior qualidade?**\
Conforme o código cresce em linhas de código (LOC), a complexidade estrutural tende a aumentar (CBO e LCOM mais altos), pois fica mais difícil manter a modularidade.

---

## 2. Questões de Pesquisa

| RQ | Pergunta | Variável de processo | Variável de qualidade |
|:---|:---------|:---------------------|:---------------------|
| RQ01 | Qual a relação entre popularidade e qualidade? | Estrelas (stars) | CBO, DIT, LCOM |
| RQ02 | Qual a relação entre maturidade e qualidade? | Idade (anos) | CBO, DIT, LCOM |
| RQ03 | Qual a relação entre atividade e qualidade? | Releases | CBO, DIT, LCOM |
| RQ04 | Qual a relação entre tamanho e qualidade? | LOC Total | CBO, DIT, LCOM |

---

## 3. Metodologia

### 3.1 Seleção dos repositórios

Coletamos os **1.000 repositórios Java mais populares** do GitHub via API REST, ordenados por número de estrelas. O script `coleta_repos.py` (Sprint 01) extraiu para cada repositório:

- `stargazers_count` — número de estrelas (popularidade)
- `age_years` — idade do repositório em anos (maturidade)
- `releases_count` — total de releases publicados (atividade)
- `size_kb` — tamanho em KB
- `clone_url` — URL para clonagem

### 3.2 Métricas de qualidade (CK)

As métricas de qualidade foram extraídas com a **ferramenta CK v0.7.0**, que analisa estaticamente arquivos `.java` e gera medições por classe:

| Métrica | Nome Completo | O que mede |
|:--------|:-------------|:-----------|
| **CBO** | Coupling Between Objects | Acoplamento: quantas outras classes uma classe referencia. Valores altos indicam dependência excessiva. |
| **DIT** | Depth of Inheritance Tree | Profundidade da herança: quantos níveis de superclasses existem. Valores altos dificultam a manutenção. |
| **LCOM** | Lack of Cohesion of Methods | Falta de coesão: quanto os métodos de uma classe compartilham atributos. Valores altos sugerem que a classe deveria ser dividida. |
| **LOC** | Lines of Code | Linhas de código por classe. Usado como métrica de tamanho. |

Para cada repositório, calculamos a **mediana** de cada métrica sobre todas as classes Java analisadas. A mediana foi escolhida ao invés da média por ser resistente a outliers — classes geradas automaticamente (mappers, DTOs) frequentemente distorcem a média.

### 3.3 Pipeline de execução em lote

O processamento dos 1.000 repositórios foi realizado pelo script `script_ck_batch.py` (Sprint 02), que implementa um pipeline automatizado:

```
Para cada repositório:
  1. git clone --depth 1 (shallow clone — somente último commit)
  2. java -jar ck.jar (análise estática das classes Java)
  3. Extração de CBO, DIT, LCOM, LOC do class.csv gerado
  4. Inclusão no ck_batch_summary.csv consolidado
  5. Remoção automática do clone (tempfile)
```

**Otimizações implementadas:**

| Técnica | Benefício |
|:--------|:----------|
| **Shallow clone** (`--depth 1 --single-branch --no-tags`) | Clone ~10x mais rápido, sem histórico git |
| **3 workers paralelos** (`ThreadPoolExecutor`) | 3 repositórios analisados simultaneamente |
| **Diretório temporário** (`tempfile.TemporaryDirectory`) | Disco ocupado: ~2-5 GB (vs ~100 GB se clonasse todos antes) |
| **Retomável** | Progresso salvo incrementalmente; se interrompido, retoma de onde parou |
| **Timeout por repo** | Clone: 180s, CK: 600s — evita que repos gigantes travem o pipeline |

Com essas otimizações, o processamento dos 1.000 repositórios foi concluído em **1 hora e 17 minutos**, contra uma estimativa inicial de 4 horas para execução serial.

### 3.4 Dados resultantes

| Item | Quantidade |
|:-----|:-----------|
| Repositórios na lista original | 1.000 |
| Repos com CK executado com sucesso | 963 |
| Repos com ≥ 5 classes Java (amostra válida) | **938** |
| Repos que falharam (sem Java real, timeout, etc.) | 37 |

Os 37 repos que falharam incluem documentação, listas awesome, e tutoriais que estão marcados como "Java" no GitHub mas não contêm código-fonte Java significativo.

### 3.5 Análise estatística

Para cada RQ, calculamos o **coeficiente de correlação de Spearman (ρ)**, que mede a correlação monotônica entre duas variáveis ordinais. A escala de interpretação usada foi:

| |ρ| | Interpretação |
|:-----|:-------------|
| < 0.20 | Correlação fraca |
| 0.20 – 0.39 | Correlação moderada |
| 0.40 – 0.69 | Correlação substancial |
| ≥ 0.70 | Correlação forte |

---

## 4. Resultados Obtidos

### 4.1 Visão geral das métricas de qualidade (N = 938)

| Métrica | Mediana | Média | Desvio Padrão | Min | Max |
|:--------|:--------|:------|:--------------|:----|:----|
| CBO (mediana/repo) | 3.00 | 3.59 | 1.69 | 0 | 30 |
| DIT (mediana/repo) | 1.00 | 1.09 | 0.30 | 1 | 3 |
| LCOM (mediana/repo) | 0.00 | 1.01 | 7.11 | 0 | 190 |
| LOC Total | 15.820 | 89.643 | 223.671 | 78 | 2.265.956 |
| Nº de Classes | 359 | 1.598 | 3.625 | 5 | 44.600 |

**Observações iniciais:**
- O **CBO mediano de 3.0** indica baixo acoplamento típico: cada classe referencia apenas 3 outras em mediana.
- O **DIT mediano de 1.0** revela hierarquias de herança rasas — a maioria das classes herda diretamente de `Object`.
- O **LCOM mediano de 0.0** sugere boa coesão (métodos que compartilham atributos), mas o desvio altíssimo (7.11) revela outliers extremos.
- A diferença entre mediana (15.8k) e média (89.6k) do LOC evidencia distribuição fortemente assimétrica.

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Distribuição do CBO (histograma azul) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Distribuição do DIT (histograma verde) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Distribuição do LCOM (histograma roxo) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Distribuição do LOC Total (histograma laranja) ]*

---

### 4.2 Correlações de Spearman

| Variável de Processo | × CBO | × DIT | × LCOM |
|:---------------------|:------|:------|:-------|
| ⭐ Popularidade (Stars) | ρ = 0.08 (fraca) | ρ = 0.37 (moderada) | ρ = 0.14 (fraca) |
| 📅 Maturidade (Idade) | ρ = 0.03 (fraca) | ρ = 0.44 (substancial) | ρ = 0.19 (fraca) |
| 🚀 Atividade (Releases) | ρ = 0.30 (moderada) | ρ = 0.37 (moderada) | ρ = 0.23 (moderada) |
| 📏 Tamanho (LOC) | ρ = 0.30 (moderada) | ρ = 0.37 (moderada) | ρ = 0.25 (moderada) |

*[ → INSERIR AQUI O PRINT DA TABELA DE CORRELAÇÕES DO DASHBOARD ]*

---

### 4.3 RQ01 — Popularidade × Qualidade

**Resultado:** Correlação **fraca** entre estrelas e CBO (ρ = 0.08) e LCOM (ρ = 0.14). Correlação **moderada** com DIT (ρ = 0.37).

A análise por quartis de popularidade confirma:

| Quartil | Stars (faixa) | CBO mediano | LCOM mediano |
|:--------|:-------------|:------------|:-------------|
| Q1 (menos popular) | 3.474 – 4.700 | 3.00 | 0.00 |
| Q2 | 4.700 – 5.739 | 3.00 | 0.00 |
| Q3 | 5.739 – 8.600 | 3.00 | 0.00 |
| Q4 (mais popular) | 8.600 – 123.816 | 4.00 | 0.00 |

A popularidade não garante qualidade. Repos extremamente populares (Q4) apresentam CBO ligeiramente maior, sugerindo que projetos maiores e mais usados tendem a ter mais dependências entre classes.

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Stars × CBO (dispersão azul) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Stars × LCOM (dispersão roxa) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: CBO por Quartil de Stars (barras) ]*

---

### 4.4 RQ02 — Maturidade × Qualidade

**Resultado:** Correlação **fraca** entre idade e CBO (ρ = 0.03). Correlação **substancial** com DIT (ρ = 0.44).

Repositórios mais antigos tendem a ter hierarquias de herança mais profundas (DIT maior), provavelmente porque foram construídos em épocas onde herança era o padrão predominante de extensão no Java. No entanto, a maturidade não impacta significativamente o acoplamento (CBO) ou a coesão (LCOM).

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Idade × CBO (dispersão verde) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Idade × LCOM (dispersão laranja) ]*

---

### 4.5 RQ03 — Atividade × Qualidade

**Resultado:** Correlação **moderada** entre releases e CBO (ρ = 0.30) e DIT (ρ = 0.37).

Repositórios com mais releases tendem a ter acoplamento ligeiramente maior. Uma possível explicação é que projetos com muitos releases são sistemas complexos e ativamente mantidos (frameworks, bibliotecas enterprise), onde o acoplamento é uma consequência natural da riqueza funcional.

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Releases × CBO (dispersão azul) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: Releases × LCOM (dispersão roxa) ]*

---

### 4.6 RQ04 — Tamanho × Qualidade

**Resultado:** Correlação **moderada** entre LOC e CBO (ρ = 0.30) e LCOM (ρ = 0.25).

Projetos maiores em linhas de código apresentam acoplamento e falta de coesão moderadamente maiores. Esse é o resultado mais intuitivo: conforme o sistema cresce, manter a modularidade perfeita fica mais difícil, e as interdependências entre classes se acumulam.

*[ → INSERIR AQUI O PRINT DO GRÁFICO: LOC × CBO (dispersão verde) ]*

*[ → INSERIR AQUI O PRINT DO GRÁFICO: LOC × LCOM (dispersão laranja) ]*

---

## 5. Discussão das Hipóteses

**H1 — Popularidade implica qualidade?**\
**Refutada.** A correlação entre estrelas e métricas de qualidade é fraca (ρ < 0.15 para CBO e LCOM). Popularidade no GitHub é impulsionada por utilidade, documentação e marketing da comunidade, e não reflete diretamente a qualidade estrutural do código. Repos extremamente populares até apresentam CBO ligeiramente maior (Q4 vs Q1).

**H2 — Maturidade implica qualidade?**\
**Refutada parcialmente.** A idade não correlaciona com CBO ou LCOM, mas apresenta correlação substancial com DIT (ρ = 0.44). Repos mais antigos possuem hierarquias de herança mais profundas, um padrão arquitetural mais comum no Java antes da adoção de composição sobre herança.

**H3 — Atividade correlaciona com qualidade?**\
**Confirmada parcialmente.** Correlação moderada (ρ ≈ 0.30) entre releases e CBO/DIT. Porém, a relação é inversa ao esperado: mais releases correlaciona com **mais** acoplamento, não menos. Projetos ativamente mantidos são sistemas funcionalmente complexos, e a complexidade estrutural é uma consequência natural.

**H4 — Repos maiores têm pior qualidade?**\
**Confirmada parcialmente.** Correlação moderada (ρ = 0.30 para CBO, 0.25 para LCOM). Conforme o código cresce, a modularidade tende a degradar, mas o efeito é moderado — indicando que os mantenedores de projetos populares fazem um trabalho razoável de controlar a complexidade mesmo em bases de código grandes.

---

## 6. Conclusão

A análise de 938 repositórios Java populares revelou que **a qualidade estrutural do código**, medida por CBO, DIT e LCOM, apresenta **correlação fraca a moderada** com as métricas de processo analisadas. Os principais achados são:

1. **Popularidade não é sinônimo de qualidade.** O número de estrelas de um repositório não prediz a qualidade do seu código. Repos com 100k+ stars não têm métricas CK significativamente melhores que repos com 5k stars.

2. **Maturidade afeta a arquitetura.** Repos mais antigos usam mais herança (DIT maior), refletindo padrões de design de épocas anteriores do Java.

3. **Tamanho é o melhor preditor.** A métrica de processo que mais correlaciona com a qualidade é o tamanho do código (LOC), confirmando que sistemas maiores têm mais dificuldade em manter modularidade.

4. **A qualidade geral é razoável.** Com CBO mediano de 3 e LCOM mediano de 0, os repositórios Java mais populares do GitHub apresentam, na maioria, boas práticas de encapsulamento e coesão.

5. **Nenhuma correlação forte (ρ ≥ 0.70) foi encontrada**, indicando que a qualidade do código depende de fatores não capturados pelas métricas de processo (práticas de revisão de código, CI/CD, cultura do time, etc.).

### Limitações

- A amostra se limita a repositórios populares, que representam uma fração do ecossistema Java.
- 37 repos (3.7%) falharam na análise por não conterem código Java significativo.
- A ferramenta CK não fornece métricas de comentários; essa análise exigiria ferramentas complementares como `cloc`.
- O shallow clone (`--depth 1`) não captura o histórico de evolução da qualidade ao longo do tempo.

---
