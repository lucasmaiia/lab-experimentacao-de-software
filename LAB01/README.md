# 🧪 LAB 01: Características de Repositórios Populares

Este laboratório faz parte da disciplina de **Laboratório de Experimentação de Software** e foca no estudo empírico de sistemas open-source de alta relevância.

O objetivo central é analisar o comportamento de desenvolvimento e manutenção dos **1.000 repositórios com maior número de estrelas no GitHub**.

---

## 📋 Questões de Pesquisa (RQs)

Para conduzir a análise, foram definidas seis questões fundamentais e uma questão bônus:

### 🔎 RQ 01: Sistemas populares são maduros/antigos?
- **Métrica:** Idade do repositório (calculada a partir da data de criação).

### 🔎 RQ 02: Sistemas populares recebem muita contribuição externa?
- **Métrica:** Total de Pull Requests aceitas.

### 🔎 RQ 03: Sistemas populares lançam releases com frequência?
- **Métrica:** Total de releases.

### 🔎 RQ 04: Sistemas populares são atualizados com frequência?
- **Métrica:** Tempo decorrido desde a última atualização.

### 🔎 RQ 05: Sistemas populares são escritos nas linguagens mais populares?
- **Métrica:** Linguagem primária de cada repositório.

### 🔎 RQ 06: Sistemas populares possuem um alto percentual de issues fechadas?
- **Métrica:** Razão entre o número de issues fechadas pelo total de issues.

### ⭐ RQ 07 (Bônus): Impacto da Linguagem
- **Análise:** Verifica se sistemas em linguagens populares recebem mais contribuições, lançam mais releases e são atualizados com maior frequência.

---

## 🛠️ Metodologia e Restrições

O desenvolvimento foi pautado por exigências técnicas específicas para garantir o controle sobre a coleta de dados:

- **GraphQL API v4:** Uso obrigatório da linguagem de consulta do GitHub para otimização da coleta de dados.
- **Consumo Nativo:** Proibição do uso de bibliotecas de terceiros para abstração da API. O consumo é realizado via script próprio (`coleta.py`).
- **Paginação:** Implementação de lógica para coletar **1.000 registros** (10 páginas de 100 repositórios cada).
- **Persistência:** Exportação dos dados brutos para formato `.csv` para posterior análise estatística.

---

## 📊 Saída Esperada

Os dados coletados são armazenados em arquivo `.csv`, permitindo:

- Análises estatísticas
- Construção de gráficos
- Comparações entre métricas
- Avaliação quantitativa das RQs

---

## 🏁 Histórico e entregas por Sprint

### Sprint 01 — Coleta inicial (amostra = 100)
- Objetivo: validar a pipeline de coleta e gerar um primeiro conjunto de dados representativo dos repositórios mais estrelados.
- O que foi implementado:
	- `coleta.py` criado para executar queries GraphQL diretamente contra `https://api.github.com/graphql` usando `urllib.request`.
	- Parâmetros iniciais definidos no script: `TARGET_REPOS = 100`, `PAGE_SIZE = 10`, `OUTPUT_CSV = "coleta_100repos.csv"`.
	- Cálculo de métricas derivadas por repositório: `age_days`, `age_years`, `days_since_update`, `issues_total`, `issues_closed_ratio`.
	- Persistência em CSV via `csv.DictWriter`.
- Artefatos gerados:
	- `LAB01/sprint01/coleta_100repos.csv` (dados brutos)
	- `LAB01/sprint01/gerarHTML.py` (gera `dashboard.html` a partir do CSV)
	- `LAB01/sprint01/dashboard.html` (dashboard interativo)
- Principais observações/achados na Sprint 01:
	- Amostra mostrou medianas de PRs e releases bastante influenciadas por outliers (projetos com atividade muito alta).
	- Linguagens mais frequentes na amostra inicial: Python, TypeScript, JavaScript.

### Sprint 02 — Expansão da amostra (amostra = 1000)
- Objetivo: avaliar sensibilidade das métricas ao tamanho da amostra e reduzir viés causado por poucos projetos extremamente populares.
- O que foi alterado/implementado:
	- Atualização de `TARGET_REPOS = 1000` e execução do mesmo fluxo de coleta (mesma query e lógica de paginação).
	- Geração do CSV maior: `LAB01/sprint02/coleta_1000repos.csv`.
	- Reuso de `gerarHTML.py` (ajustado se necessário para apontar ao CSV maior) e geração de dashboard em `LAB01/sprint02/`.
- Artefatos gerados:
	- `LAB01/sprint02/coleta_1000repos.csv`
	- `LAB01/sprint02/gerarHTML.py` (separado por sprint para conveniência)
	- `LAB01/sprint02/dashboard.html`
- Principais observações/achados na Sprint 02:
	- A mediana de PRs caiu ao ampliar a amostra (1703 → 739), confirmando que a amostra menor estava mais sujeita a outliers.
	- A mediana de releases aumentou (15.5 → 40.5), mostrando que incluir mais repositórios alterou a distribuição para essa métrica.
	- `days_since_update` e medidas de variabilidade revelaram maior dispersão na amostra maior.

## ⚙️ Como reproduzir (passo a passo)
1. Prepare um token GitHub com permissões de leitura pública e defina `GITHUB_TOKEN` em `.env` ou na sessão:
```powershell
$env:GITHUB_TOKEN = 'ghp_xxxSEU_TOKEN'
```
2. (Opcional) Instale dependências usadas para documentação/extras:
```powershell
py -m pip install --user python-dotenv PyPDF2
```
3. Rodar coleta (ajuste `TARGET_REPOS` no `coleta.py` para 100 ou 1000 conforme desejado):
```powershell
cd LAB01
py coleta.py
```
4. Gerar dashboard a partir do CSV produzido:
```powershell
py sprint01\gerarHTML.py   # para a amostra de 100
py sprint02\gerarHTML.py   # para a amostra de 1000
```

---

