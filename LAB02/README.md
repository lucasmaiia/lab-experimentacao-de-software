# 📊 Laboratório 02 — Estudo das Características de Qualidade de Sistemas Java

## 📌 Sobre o Projeto

Este repositório contém a implementação e análise do **Laboratório 02** da disciplina de **Laboratório de Experimentação de Software** da PUC Minas.

O objetivo principal do estudo é investigar as **características de qualidade de sistemas desenvolvidos em Java**, analisando repositórios open-source e correlacionando métricas de qualidade com aspectos do processo de desenvolvimento.

---

## 🎯 Objetivo

Analisar a qualidade interna de sistemas Java open-source, correlacionando métricas de código com características como:

- Popularidade
- Maturidade
- Atividade
- Tamanho

A análise é feita utilizando métricas extraídas com ferramentas de análise estática, como a **CK (Chidamber & Kemerer Metrics Tool)**.

---

## 🧠 Contexto

No desenvolvimento de software open-source, múltiplos desenvolvedores contribuem simultaneamente para o código. Isso pode impactar atributos de qualidade como:

- Modularidade
- Manutenibilidade
- Legibilidade

Para mitigar esses riscos, são utilizadas práticas como:

- Revisão de código
- Integração contínua (CI/CD)
- Análise estática

---

## 🔍 Metodologia

### 1. Seleção de Repositórios

Foram selecionados:

- **Top 1000 repositórios Java mais populares do GitHub**

Critério principal:

- Número de estrelas ⭐

---

### 2. Questões de Pesquisa (Research Questions)

O estudo busca responder às seguintes perguntas:

- **RQ01:** Qual a relação entre a popularidade e a qualidade?
- **RQ02:** Qual a relação entre a maturidade e a qualidade?
- **RQ03:** Qual a relação entre a atividade e a qualidade?
- **RQ04:** Qual a relação entre o tamanho e a qualidade?

---

### 3. Métricas Utilizadas

#### 📈 Métricas de Processo

| Métrica        | Descrição |
|----------------|----------|
| Popularidade   | Número de estrelas |
| Tamanho        | Linhas de código (LOC) e comentários |
| Atividade      | Número de releases |
| Maturidade     | Idade do repositório (anos) |

---

#### 🧩 Métricas de Qualidade (CK)

| Métrica | Descrição |
|--------|----------|
| CBO    | Coupling Between Objects |
| DIT    | Depth of Inheritance Tree |
| LCOM   | Lack of Cohesion of Methods |

---

### 4. Coleta de Dados

Os dados são obtidos através de:

- API do GitHub (REST ou GraphQL)
- Ferramenta de análise estática (**CK**)

⚠️ Importante:  
A ferramenta CK gera múltiplos arquivos `.csv`, sendo necessário realizar **sumarização dos dados**.

---

## 📊 Análise de Dados

Para cada repositório, devem ser calculadas:

- Média
- Mediana
- Desvio padrão

Essas métricas ajudam a entender o comportamento geral dos dados.

---

## 📄 Estrutura do Relatório Final

O relatório deve conter:

1. **Introdução**
   - Contexto do problema
   - Hipóteses iniciais

2. **Metodologia**
   - Como os dados foram coletados e analisados

3. **Resultados**
   - Dados obtidos para cada questão de pesquisa

4. **Discussão**
   - Comparação entre hipóteses e resultados

---

## 📈 Bônus

Para melhorar a análise:

- Gerar gráficos de correlação 📊
- Aplicar testes estatísticos:
  - Correlação de **Spearman**
  - Correlação de **Pearson**

---

## 🔄 Processo de Desenvolvimento

### 🧪 Sprint 1 (Lab02S01)

- Lista dos 1000 repositórios
- Script de coleta de dados
- CSV com dados de 1 repositório

📌 Valor: 5 pontos

---

### 🧪 Sprint 2 (Lab02S02)

- CSV com dados dos 1000 repositórios
- Definição de hipóteses
- Análise e visualização dos dados
- Relatório final

📌 Valor: 15 pontos

---

## 🏫 Informações Acadêmicas

**Alunos**
- Leandro Pacheco  
- Lucas Maia  

**Professor**
- Danilo de Quadros Maia Filho  

---

## 🚀 Conclusão

Este laboratório permite compreender, na prática, como métricas de software podem ser utilizadas para avaliar a qualidade de sistemas reais, além de desenvolver habilidades em:

- Coleta e análise de dados
- Uso de APIs
- Engenharia de Software baseada em evidências

---