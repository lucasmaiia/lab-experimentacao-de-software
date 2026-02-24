# Laboratório de Experimentação de Software
---
## Processo de desenvolvimento
Foi realizada uma coleta automática via GraphQL para 100 repositórios do GitHub. Os resultados e o dashboard gerado estão nessa pasta.

- `coleta_100repos.csv`: cada linha corresponde a um repositório e inclui metadados e métricas usadas nas RQs — por exemplo: nome, proprietário, linguagem dominante, datas (criação/atualização), contadores (estrelas, forks, issues, pull requests), contagem de contribuintes e topics.
- `gerarHTML.py` → `dashboard.html`: o script lê o CSV e gera um HTML de visualização com uma tabela-resumo e gráficos para explorar as métricas; abra `dashboard.html` no navegador para visualizar o dashboard.

