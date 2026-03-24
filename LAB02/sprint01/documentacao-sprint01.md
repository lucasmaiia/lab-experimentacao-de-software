# Sprint 01 - Documentacao Completa

## Objetivo da Sprint

O objetivo da Sprint 01 do `LAB02` foi montar a base inicial do experimento com repositórios Java do GitHub, automatizando:

- a coleta dos 1000 repositórios Java mais populares
- o clone desses repositórios para o ambiente local
- a execução da ferramenta CK em pelo menos 1 repositório
- a geração de arquivos `.csv` com os dados coletados e as métricas de qualidade

Essa sprint atende ao requisito:

> Lista dos 1.000 repositórios Java + Script de Automação de clone e Coleta de Métricas + Arquivo `.csv` com o resultado das medições de 1 repositório

---

## 1. Coleta dos 1000 Repositorios Java

### Arquivo

- `LAB02/sprint01/script_coleta.py`

### O que o script faz

Esse script consulta a API REST do GitHub para buscar os 1000 repositórios Java mais populares, utilizando:

- `language:java`
- `sort=stars`
- `order=desc`
- `per_page=100`
- `page=1` ate `page=10`

### Tecnologias utilizadas

- Python
- biblioteca `requests`
- API REST do GitHub

### Recursos implementados

- uso opcional de token via variavel de ambiente `GITHUB_TOKEN`
- tratamento de erros de rede
- retentativas em caso de falhas temporarias
- tratamento de rate limit
- logs de progresso no terminal
- enriquecimento dos dados com metricas de processo

### Dados coletados

Para cada repositorio, foram coletados os seguintes campos:

- `id`
- `name`
- `full_name`
- `owner_login`
- `html_url`
- `description`
- `language`
- `stargazers_count`
- `forks_count`
- `open_issues_count`
- `size_kb`
- `releases_count`
- `created_at`
- `updated_at`
- `pushed_at`
- `age_days`
- `age_years`
- `clone_url`

### Metricas de processo cobertas

As metricas de processo consideradas nesta sprint foram:

- Popularidade: `stargazers_count`
- Tamanho: `size_kb`
- Atividade: `releases_count`
- Maturidade: `age_days` e `age_years`

### Arquivo gerado

- `LAB02/sprint01/repositorios_java_top1000.csv`

Esse arquivo contem a lista dos 1000 repositórios que servem de base para os scripts seguintes.

### Uso da biblioteca requests

Na Sprint 01 do `LAB02`, a biblioteca `requests` foi utilizada no `script_coleta.py` para realizar as chamadas HTTP para a API REST do GitHub.

Ela foi usada para:

- buscar as paginas de resultados dos 1000 repositorios
- consultar informacoes adicionais de cada repositorio
- enviar cabecalhos HTTP como `Authorization`, `Accept` e `User-Agent`
- tratar timeouts, erros de rede e respostas HTTP com mais simplicidade
- ler respostas em JSON de forma direta

### Diferenca em relacao ao LAB01

No `LAB01`, a implementacao principal de coleta usava `urllib.request`, da biblioteca padrao do Python, para acessar a API do GitHub.

Ja no `LAB02`, foi adotado `requests` porque:

- era um requisito da atividade
- o codigo fica mais simples de ler e manter
- o tratamento de erros HTTP e JSON fica mais direto
- a configuracao de cabecalhos e autenticacao fica mais organizada

Em resumo:

- `LAB01`: uso de `urllib.request`
- `LAB02`: uso de `requests`

---

## 2. Clone Automatico dos Repositorios

### Arquivo

- `LAB02/sprint01/script_clone.py`

### O que o script faz

Esse script le o arquivo `repositorios_java_top1000.csv`, extrai o `clone_url` de cada repositorio e realiza o clone local automaticamente.

### Pasta de destino

- `LAB02/sprint01/repos_clonados/`

Os repositórios são organizados em subpastas no formato:

- `repos_clonados/owner/repo`

### Recursos implementados

- leitura automatica do CSV da coleta
- validacao da presenca do `git`
- clone raso por padrao com `--depth 1`
- suporte a multiplos clones em paralelo
- arquivo de status incremental
- retomada de execucao sem reclonar o que ja foi concluido
- logs de progresso no terminal

### Arquivo de status

- `LAB02/sprint01/clone_status.csv`

Esse arquivo registra, para cada repositorio:

- nome
- URL de clone
- pasta local
- status
- mensagem de retorno

### Resultado obtido

Os repositórios foram clonados com sucesso para a pasta `repos_clonados`, e o status foi salvo no arquivo `clone_status.csv`.

---

## 3. Execucao da Ferramenta CK em 1 Repositorio

### Arquivo

- `LAB02/sprint01/script_ck.py`

### Objetivo

Executar a ferramenta CK em um repositório Java local para gerar métricas de qualidade estrutural do código.

### Comando usado pela ferramenta

O script executa o comando:

```powershell
java -jar ck-0.7.0-jar-with-dependencies.jar <repositorio> true 0 false
```

### Validacoes implementadas

- verifica se o `ck.jar` existe
- verifica se o diretório do repositório existe
- verifica se o Java está disponível no `PATH`
- valida se os CSVs da CK foram gerados

### Logs e saida

O script envia os logs da execução diretamente para o terminal e salva os arquivos gerados em:

- `LAB02/sprint01/ck_output/`

### Repositorio utilizado na execucao

Foi utilizado o repositório:

- `macrozheng/mall`

Caminho local:

- `C:\Users\maial\Documents\GitHub\lab-experimentacao-de-software\LAB02\sprint01\repos_clonados\macrozheng\mall`

### Problema encontrado

Inicialmente a execução da CK falhou porque o terminal estava usando Java 8:

- `java version "1.8.0_481"`

O `ck.jar` utilizado foi compilado para uma versão mais recente do Java, então foi necessário usar o Java 17 já instalado na máquina apenas na sessão atual do PowerShell.

### Ajuste realizado no PowerShell

Para usar temporariamente o Java 17 sem substituir o Java 8 do sistema, foram executados os comandos:

```powershell
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17.0.18.8-hotspot"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
java -version
```

Depois disso, o script da CK foi executado com:

```powershell
py LAB02\sprint01\script_ck.py "C:\Users\maial\Documents\GitHub\lab-experimentacao-de-software\LAB02\sprint01\repos_clonados\macrozheng\mall"
```

---

## 4. Resultados da Execucao da CK

### Arquivos gerados com sucesso

Na execução da CK para o repositório `macrozheng/mall`, foram gerados:

- `LAB02/sprint01/ck_output/class.csv`
- `LAB02/sprint01/ck_output/method.csv`
- `LAB02/sprint01/ck_output/ck_metrics_summary.csv`

### Avisos observados

Durante a execução apareceram avisos de `log4j`, mas eles não impediram o processamento:

- a ferramenta CK foi executada com sucesso
- as métricas principais foram extraídas normalmente

Tambem houve aviso sobre a ausencia de:

- `field.csv`
- `variable.csv`

Isso não impediu a entrega da Sprint 01, pois os arquivos necessários para comprovar a extração das métricas foram gerados.

---

## 5. Metricas de Qualidade Cobertas

O script `script_ck.py` foi preparado para ler o `class.csv` gerado pela CK e produzir um resumo por repositório em `ck_metrics_summary.csv`.

As métricas de qualidade consideradas foram:

- `CBO`
- `DIT`
- `LCOM`

Para cada uma delas, o resumo calcula:

- media
- mediana
- desvio padrao
- valor minimo
- valor maximo

Isso permitiu transformar a saída bruta da CK em um arquivo consolidado mais fácil de analisar.

---

## 6. Situacao Final da Sprint 01

Ao final da Sprint 01, os seguintes itens estavam concluídos:

- coleta automatica dos 1000 repositorios Java
- geração do CSV com os repositórios coletados
- script de clone automatizado
- clone local dos repositórios
- script para execução individual da CK
- execução da CK em 1 repositório clonado
- geração de CSV com as medições de 1 repositório

Assim, os requisitos da Sprint 01 foram atendidos.

---

## 7. Comandos Principais Utilizados

### Coleta

```powershell
$env:GITHUB_TOKEN="SEU_TOKEN"
py LAB02\sprint01\script_coleta.py
```

### Clone

```powershell
py LAB02\sprint01\script_clone.py
```

### Ajuste temporario do Java 17

```powershell
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17.0.18.8-hotspot"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
java -version
```

### Execucao da CK em 1 repositorio

```powershell
py LAB02\sprint01\script_ck.py "C:\Users\maial\Documents\GitHub\lab-experimentacao-de-software\LAB02\sprint01\repos_clonados\macrozheng\mall"
```

---

## 8. Observacoes Importantes

- o script de coleta atual utiliza `size_kb` como aproximacao de tamanho do repositório
- a medição exata de LOC nao foi calculada nesta sprint
- o Java 17 foi usado apenas na sessão atual do terminal para evitar impacto em outros projetos que ainda dependem de Java 8
- a execução em lote da CK foi preparada posteriormente para apoiar as próximas sprints, mas para a Sprint 01 bastava a medição de 1 repositório

---

## Conclusao

A Sprint 01 estabeleceu toda a infraestrutura inicial do laboratório: base de dados dos repositórios, automação de clone e execução de métricas de qualidade. Com isso, o ambiente ficou pronto para as próximas etapas de análise em maior escala nas sprints seguintes.
