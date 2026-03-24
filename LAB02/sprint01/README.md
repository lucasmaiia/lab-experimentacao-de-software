# Laboratório de Experimentação de Software
---
## Processo de desenvolvimento

Na primeira sprint, foi realizada a coleta automática dos dados dos repositórios Java mais populares do GitHub, utilizando scripts de automação e integração com a API do GitHub. Além disso, foi executada a extração inicial de métricas de qualidade com apoio de ferramentas de análise estática.

- `repositorios.csv`: contém a lista dos repositórios coletados (top 1000 Java), incluindo informações como nome, estrelas, datas de criação e atualização.
- `script_coleta.py`: responsável por automatizar a coleta dos dados via API do GitHub.
- `script_clone.sh`: script utilizado para realizar o clone automático dos repositórios.
- `ck_output.csv`: arquivo gerado pela ferramenta CK contendo métricas de qualidade do código (como CBO, DIT e LCOM) para um repositório analisado.