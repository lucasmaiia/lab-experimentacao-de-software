# Roteiro de Apresentação — Lab03 Sprint 03
**Tempo total: ~5 minutos**

---

## [0:00 – 0:40] Introdução

- O trabalho analisa **o que influencia o resultado de um Pull Request** no GitHub.
- Dataset: **50.981 PRs de 191 repositórios populares**, todos com ao menos 1 revisão humana.
- Duas perguntas centrais: o que leva um PR a ser **aceito ou rejeitado**? E o que determina **quantas revisões** ele recebe?

---

## [0:40 – 1:10] Metodologia (rápido)

- Coleta via **API GraphQL do GitHub** → filtros: ≥ 1 revisão, tempo de análise > 1h (exclui bots).
- Teste escolhido: **Correlação de Spearman** — adequado para dados assimétricos de cauda longa, que é o padrão em métricas de repositórios open source.

---

## [1:10 – 2:30] Resultados — Dimensão A: Status do PR

> O fator mais importante é o **tempo**.

- **RQ02 — Tempo × Status** (ρ = −0,165): PRs rejeitados ficam abertos **~116 horas** vs **~26 horas** dos aceitos. Quanto mais tempo aberto, maior a chance de rejeição.
- **RQ04 — Interações × Status** (ρ = −0,116): **surpresa** — mais comentários e participantes estão associados à *rejeição*, não à aceitação. Muita discussão sinaliza controvérsia.
- **RQ01 — Tamanho × Status** (ρ = +0,08): **surpresa** — PRs ligeiramente maiores têm marginalmente mais chance de serem aceitos. Em projetos maduros, contribuições substanciais chegam mais preparadas.
- **RQ03 — Descrição × Status** (ρ = −0,019): descrição não impacta o desfecho na prática.

---

## [2:30 – 3:30] Resultados — Dimensão B: Número de Revisões

> O engajamento da comunidade é o maior preditor.

- **RQ08 — Interações × Revisões** (ρ = +0,378): **maior correlação do estudo** — participantes e comentários co-ocorrem fortemente com mais ciclos de revisão.
- **RQ05 — Tamanho × Revisões** (ρ = +0,336): PRs maiores recebem mais revisões — especialmente os com mais linhas adicionadas.
- **RQ07 — Descrição × Revisões** (ρ = +0,181): descrições longas indicam complexidade, que por sua vez gera mais revisões — o oposto do que esperávamos.

---

## [3:30 – 4:20] Discussão

- **4 de 8 hipóteses foram refutadas** — o processo de code review é mais complexo do que o senso comum sugere.
- O principal insight: **velocidade e alinhamento prévio** importam mais do que tamanho ou descrição.
- PRs que geram debate são sinais de desalinhamento, não de interesse positivo.

---

## [4:20 – 5:00] Tomada de Decisão

Para **desenvolvedores**:
- Mantenha PRs focados e resolva-os rapidamente — PRs parados acumulam rejeição.
- Alinhe com os mantenedores via issues *antes* de abrir o PR.

Para **mantenedores**:
- Resposta rápida aumenta a taxa de aceitação — estabeleça SLA de primeira resposta.
- PRs com muitos comentários precisam de intervenção precoce para definir se há chance de merge.
