# Lab 05 — GraphQL vs REST: Um Experimento Controlado
## Sprint 02 — Execução, Análise e Relatório Final

**Disciplina:** Laboratório de Experimentação de Software  
**Curso:** Engenharia de Software - PUC Minas  

---

## O que este sprint entrega

| Etapa | Descrição | Artefato |
|-------|-----------|----------|
| **3 — Execução** | Coleta de ~4.800 medições via API do GitHub | `sprint01/scripts/results.csv` |
| **4 — Análise** | Wilcoxon pareado + effect size + validação | saída do `analyze.py` |
| **5 — Relatório** | Documento final auto-contido (HTML) | `sprint02/report.html` |

---

## Pré-requisitos

- Python ≥ 3.10
- Token GitHub com acesso de leitura a repositórios públicos  
  Gere em: <https://github.com/settings/tokens> (nenhum escopo especial necessário)

---

## Passo 1 — Configurar o token

```bash
cp LAB05/sprint01/.env.example LAB05/sprint01/.env
# Abrir .env e substituir: GITHUB_TOKEN=seu_token_aqui
```

---

## Passo 2 — Verificar conectividade (dry-run)

Antes da coleta completa, execute um dry-run com 2 repos e 2 repetições (~2 min):

```bash
cd LAB05/sprint01/scripts
pip install -r requirements.txt
python collector.py --dry-run
```

Verifique a saída, deve mostrar 16 medições sem erros de autenticação.

---

## Passo 3 — Executar a coleta completa

> ⏱ Duração estimada: **~45–60 minutos**  
> 📡 Requisições: ~5.120 (incluindo warm-up)

```bash
cd LAB05/sprint01/scripts
python collector.py
```

O script:
- Exibe barra de progresso (via `tqdm`)
- Salva progressivamente em `results.csv`
- Aguarda automaticamente em caso de rate limiting
- Registra erros em `errors.log`

Ao final, exibe um resumo de medianas por tipo de consulta e API.

---

## Passo 4 — Gerar a análise e o relatório

```bash
cd LAB05/sprint02/scripts
pip install -r requirements.txt
python analyze.py
```

**Saída:** `LAB05/sprint02/report.html` - relatório completo e auto-contido  
(abre diretamente no navegador, sem servidor web necessário).

### Opções do analyze.py

```
python analyze.py --data CAMINHO/results.csv   # CSV customizado
python analyze.py --output CAMINHO/saida.html  # HTML em local diferente
```

---

## Estrutura do experimento (resumo)

| Parâmetro | Valor |
|-----------|-------|
| Repositórios | 20 repos populares do GitHub |
| Tipos de consulta | 4 (repo_info, issues, pull_requests, commits) |
| Repetições por par | 30 |
| Medições válidas esperadas | 4.800 |
| Teste estatístico | Wilcoxon Pareado (não-paramétrico) |
| Correção para múltiplos testes | Bonferroni (α_adj = 0,00625) |
| Tamanho de efeito | Correlação rank-biserial (*r*) |

---

## Estrutura dos arquivos

```
LAB05/
├── sprint01/
│   ├── .env                        ← token GitHub (não commitado)
│   ├── .env.example
│   ├── scripts/
│   │   ├── collector.py            ← coleta de dados (Passo 3)
│   │   ├── config.py
│   │   ├── queries.py
│   │   ├── requirements.txt
│   │   ├── results.csv             ← gerado após coleta
│   │   └── errors.log              ← gerado após coleta
│   └── design.html                 ← desenho do experimento (Sprint 01)
└── sprint02/
    ├── scripts/
    │   ├── analyze.py              ← análise + geração do relatório (Passo 4)
    │   └── requirements.txt
    └── report.html                 ← relatório final gerado (Passo 4)
```

---

*Junho de 2026 | Laboratório de Experimentação de Software — PUC Minas*
