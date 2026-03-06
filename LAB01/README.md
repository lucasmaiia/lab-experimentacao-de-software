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

