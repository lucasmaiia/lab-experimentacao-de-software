# Análise das Características de Repositórios Populares no GitHub
Laboratório de Experimentação de Software
**Alunos:** Leandro Pacheco, Lucas Maia

## Índice
1. Introdução e Hipóteses
2. Questões de Pesquisa (Objetivos)
3. Metodologia
4. Resultados Obtidos
5. Discussão das Hipóteses
6. Tomada de Decisão
7. Conclusão

---

## 1. Introdução e Hipóteses
Este trabalho visa analisar os 1.000 repositórios com maior número de estrelas no GitHub, compreendendo os padrões de desenvolvimento, fluxos de contribuição e ciclos de manutenção presentes nos projetos *open-source* de maior relevância mundial.

Antes do início da coleta, elaboramos algumas hipóteses sobre o que esperaríamos encontrar na base de dados:
*   **H1:** Projetos massivamente populares tendem a ser antigos, visto que acumular reconhecimento contínuo da comunidade leva vários anos. Esperamos uma idade mediana superior a 5 anos.
*   **H2:** A adoção de contribuições externas (Pull Requests) deve ser altíssima, porém assimétrica. Repositórios de frameworks e bibliotecas ativas devem receber um grande volume, enquanto aqueles voltados apenas à documentação e educação (listas e livros) devem possuir zero ou poucas contribuições reais de código.
*   **H3:** A maior parte dos repositórios lança *releases* frequentemente. Contudo, esperamos o mesmo forte desvio padrão de H2: projetos de utilidades puras provavelmente não possuem pacotes compilados.
*   **H4:** O ecossistema *open-source* do topo do rank é aquecido. Imaginamos que o tempo desde o último *push* (atualização) para a grande maioria gire na casa de poucos dias.
*   **H5:** Python, TypeScript e JavaScript devem dominar o rank, por serem historicamente as linguagens mais distribuídas e fundamentais na web e em dados.
*   **H6:** A taxa de *issues* resolvidas deve ser imensa em grandes projetos, ultrapassando a margem de 80%, dado o zelo dos mantenedores e das comunidades com softwares de escopo mundial.

## 2. Questões de Pesquisa (Objetivos)
O presente experimento se destina a responder matematicamente e visualmente às seguintes indagações:
*   **RQ 01.** Sistemas populares são maduros/antigos? (Idade do repositório)
*   **RQ 02.** Sistemas populares recebem muita contribuição externa? (Total de Pull Requests aceitas)
*   **RQ 03.** Sistemas populares lançam *releases* com frequência? (Total de *releases*)
*   **RQ 04.** Sistemas populares são atualizados com frequência? (Tempo em dias até a última atualização)
*   **RQ 05.** Sistemas populares são escritos nas linguagens mais populares? (Linguagem primária de cada repositório)
*   **RQ 06.** Sistemas populares possuem um alto percentual de *issues* fechadas? (Razão entre *issues* resolvidas e registradas)
*   **RQ 07 (Bônus).** Sistemas escritos nas linguagens mais populares geram mais PRs, *releases* e recebem atualizações mais recorrentes em relação ao resto da base?

## 3. Metodologia
Os dados foram minerados de forma nativa e automática utilizando um script Python (`coleta.py`), que realiza requisições diretas sob autenticação por token (`Bearer`) à infraestrutura da API GraphQL do GitHub. Não fizemos uso de bibliotecas pre-prontas de terceiros como *Requests* ou *GQL*, respeitando o critério de que o consumo de APIs fosse construído inteiramente pelo aluno consumindo puramente a URL original.

**Filtros Impostos (Purificação)**
Notamos de imediato que muitos dos itens super-ranqueados não eram softwares em si, resultando em métricas nulas e distorção analítica (arquivos *Awesome-Lists*, guias de estudo, PDF's). A dupla instituiu travas analíticas no script para recusar do Dataset qualquer repósitorio que:
1.  Fosse originado de um Fork (`isFork: true`);
2.  Obtivesse menos de 100kb em disco (projetos muito vazios);
3.  Estivesse arquivado;
4.  Não apresentasse `primaryLanguage` explicitamente declarada pelo mantenedor.

**Estratégia de Paginação contra Rate-Limits**
A API do Github impede que um único cursor retorne mais do que os 1.000 primeiros repositórios de qualquer lista ranqueada. Como os nossos filtros de "purificação" descartavam agressivamente cerca de 36% dos resultados da primeira batelada, a coleta sempre encerrava prematuramente atingindo apenas a cota de ~630 projetos validáveis.

Para alcançar a exigência dos exatos **1.000 projetos rigorosos** da Sprint 03, reformulamos o script para capturar a nota de corte gravitacional (quantas `stars` possuía o último projeto lido antes da barreira bater) e disparamos novos laços automatizados de páginas sucessivas usando dinamicamente `stars <= LAST_STAR` como filtro limitador. Esse *bypass* reabasteceu o cursor, preenchendo 100% da cota até a exatidão das 1.000 linhas puras exigidas para os cálculos.

**Métricas e Cálculos de Exceção:**
*   **Update At:** Evitamos utilizar a resposta trivial de `updatedAt` da nuvem do Github. Isso ocorre porque repositórios famosos flutuam e são avaliados o tempo todo com novas estrelas ou *forks* da comunidade por fora, disparando constantemente falsos positivos onde literalmente todos os 1000 repos têm data de atualização no dia de hoje. Em vez disso, medimos de forma conservadora a chave interna `pushedAt` para representar apenas atualizações oriundas de alterações literais da base de código, convertidas depois em Dias e Horas pelo Python.
*   **Tratamento de Outliers:** Optamos por usar amplamente a Mediana ao invés da Média em toda a nossa argumentação estatística na Sprint 03. Projetos extraordinários como o `freeCodeCamp` com suas 27 mil PRs mergeadas tracionariam a curva inteira da API fortemente para cima. A mediana retrata de forma muito mais coesa os valores típicos e absolutos.
*   O processamento estético (Dashboard visualizando dados numéricos) foi executado por um segundo script com integração local HTML/Javascript `Chart.js`, plotando o Dashboard nativo do laboratório.

## 4. Resultados Obtidos
A amostra final para os 1.000 repositórios puros resultou no seguinte cenário geral (Sprint 03):

| Métrica Estudada | Respondentes (N) | Mediana | Min | Max |
| :--- | :---: | :---: | :---: | :---: |
| Idade em Anos | 1.000 | 8.35 | 0.14 | 16.94 |
| Total de Pull Requests Aceitas | 1.000 | 884 | 0 | 114.397 |
| Lançamentos (*Releases*) | 1.000 | 50.5 | 0 | 1.000 |
| Dias Sem Atualização (*Push*) | 1.000 | 1.15 | 0 | 2.227 |
| Razão de Issues Resolvidas | 1.000 | 0.88 (88%) | 0.0 | 1.00 (100%) |

*[ -> AQUI VOCE VAI COLAR O PRIMEIRO PRINT DA DASHBOARD. PRINT AS CARDS (OS QUADRADINHOS) MOSTRANDO AS MEDIANAS ]*

**Corte Secundário: Linguagens de Programação**
Separando e avaliando o ecossistema top-tier mundial através das linguagens declaradas em seus servidores, obtivemos a seguinte malha dominante para a RQ 05 e RQ 07:

| Rank de Linguagens (RQ 05) | Repositórios Encontrados | Medianas em PRs | Medianas em Releases | Med. de Dias s/ Update |
| :--- | :---: | :---: | :---: | :---: |
| **Python** | 185 | 860 | 33 | 1.76 |
| **JavaScript** | 158 | 808 | 51.5 | 3.52 |
| **TypeScript** | 148 | 2.594 | 158 | 0.50 |
| **C++** | 118 | 971 | 38.5 | 1.39 |
| **Go** | 98 | 1.854 | 134 | 0.49 |

*[ -> AQUI VOCE VAI COLAR O SEGUNDO PRINT DO GRÁFICO TIPO PIZZA COM AS ISSUES FECHADAS & TAMBÉM O DE BARRAS DAS LINGUAGENS (RQ 05)]*

## 5. Discussão das Hipóteses
Analisando frente a frente nossos paradigmas informais de planejamento vs a realidade dos dados contidos na base de software de fato:

1.  **H1: Repositórios populares são maduros (Idade)?**
    *   **Confirmada.** A amostra atesta que repousam sob um patamar absoluto de 8,35 anos medianos. Muito poucas empresas e projetos de TI furaram a bolha do *hype* superável nos primeiros meses de vida. Fama durável, em desenvolvimento de software, é estritamente vinculada a consistência de quase uma década.
    *[ -> AQUI VOCE VAI COLAR O PRINT DO GRÁFICO HISTOGRAMA DA DASHBOARD, AQUELE AZULZINHO LISTANDO A IDADE X REPOSITÓRIOS ]*
2.  **H2: Acesso à contribuições da comunidade? (PRs)**
    *   **Confirmada Parcialmente.** O volume foi provado como alto (mediana na casa dos 884 PRs mergeados para desenvolvedores da casa), porém confirmamos a forte disparidade e exclusões das curvas assintóticas: o gráfico de dispersão nos comprovou visualmente que projetos que nasceram há meros meses atrás (ex: LLMs) já bateram cota parecida de PRs de projetos velhos da metade do caminho, pulverizando a constância lógica da relação Idade x PR, revelando o surgimento de picos de contribuição situacional.
    *[ -> AQUI VOCE VAI COLAR O PRINT DO GRÁFICO DE DISPERSÃO (PONTINHOS ESPALHADOS) DA DASHBOARD MOSTRANDO OS PRs. ]*
3.  **H3: Reposições e Lançamentos massivos (Releases)**
    *   **Refutada.** Apesar de gigantes mundiais como VSCode subirem incontáveis versões do app, a Mediana global estagnou em "apenas" 50 Releases cadenciados por repo ao longo de sua vida inteira. Na via em que "PRs" (Códigos brutos) são aceitos aos baldes num funil elástico para o software não colapsar sob defasamento, os "Releases" (A consolidação oficial daquela build final enviada pras prateleira) requerem alta curadoria e raramente batem tetos imensos, atestando uma distribuição em formato funil dos produtos finais vs os protótipos em aprovação.
4.  **H4: Velocidade de Atualização Recorrente?**
    *   **Confirmada vigorosamente.** Com a mediana girando em fantásticos **1.15 Dias**, podemos traçar a certeza irrefutável de que, estatisticamente, repósitorios situados na pirâmide da utilidade humana são empurrados virtualmente do princípio ao final com código produtivo a poucas ou parcas horas de distância diária, atestando a vibração assídua da esteira da colaboração sem paradas, mantida ininterrupta em quase dezena de anos de maturação por braços da comunidade.
5.  **H5: Dominação das Linguagens mainstream**
    *   **Confirmada.** Conforme suposto, **Python, JavaScript e TypeScript** controlam categoricamente quase 49,1% da malha representativa sozinhos, esmagando os demais no topo global devido a sua flexibilidade de stack (backend-frontend, web) e na explosão recente do arcabouço da IA por via natural do Python.
6.  **H6: Sucesso em sanar incidentes da comunidade**
    *   **Confirmada.** Obtivemos expressivos 88% de Mediana para aprovação integral e fechamento de `Issues`, revelando que se o time sobreviveu e popularizou há quase dez anos no ranque global e traciona até agora, o time *precisou* responder com presteza assustadora às dúvidas da comunidade.

## 6. Tomada de Decisão
Os dados evidenciam o comportamento das grandezas (Bônus RQ 07). Linguagens mais acadêmicas e generalistas do eixo da Web como Python e JS recebem sim grande contribuição da comunidade global via volume, no entanto linguagens compiladas voltadas para o cerne corporativo rigoroso de performance (*Go* e *TypeScript*) esmagaram os rankings por mais de **três vezes de lucro de entregáveis** superando a marca de mais de 130 *Releases* por repositório (completamente distópico aos seus irmãos em JS) e medianas gigantes e infláveis muito acima de 2.000 contribuições confirmáveis de Pull Requests, demonstrando as áreas mais quentes e asferas de emprego dos mantenedores sérios.

*[ -> AQUI VOCE VAI COLAR FINALMENTE O GRÁFICO DE DUAS CORES "PRs VS RELEASES POR LINGUAGENS"]*

## 7. Conclusão
Este laboratório confirmou, em essência e cálculo matemático das 6 premissas, a teoria observacional: a popularidade dentro da ecologia social de software moderno não é um evento fortuito ou passageiro, e sim uma obra arquitetônica baseada numa década de maturidade. Esses gigantes combinam uma recepção ininterrupta massiva de ajuda comunitária fragmentada por linguagens de base sólidas, ao passo que fecham incessantemente 9 de cada 10 problemas registrados a diário pelos usuários numa velocidade menor do que um dia de atraso. Os limites observacionais e assímetria das médias (comuns na programação em dados numéricos distantes) foram contornados com a visualização do painel em HTML em conjunto pelo uso apropriado das Medianas relativas, provando um ensaio acadêmico final de alta credibilidade analítca.
