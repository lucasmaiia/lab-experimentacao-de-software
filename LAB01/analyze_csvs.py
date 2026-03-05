import csv, json, statistics, collections, os
from pathlib import Path

BASE = Path(__file__).parent
S1 = BASE / 'sprint01' / 'coleta_100repos.csv'
S2 = BASE / 'sprint02' / 'coleta_1000repos.csv'
OUT_MD = BASE / 'sprint01' / 'analysis_results.md'

def to_int(x):
    try:
        return int(x)
    except:
        return None

def to_float(x):
    try:
        return float(x)
    except:
        return None

def stat_pack(arr):
    arr = [x for x in arr if x is not None]
    if not arr:
        return {}
    return {
        'count': len(arr),
        'mean': round(statistics.mean(arr),2),
        'median': round(statistics.median(arr),2),
        'min': round(min(arr),2),
        'max': round(max(arr),2),
    }


def analyze(path):
    rows = []
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            row['stars'] = to_int(row.get('stars'))
            row['age_years'] = to_float(row.get('age_years'))
            row['days_since_update'] = to_int(row.get('days_since_update'))
            row['merged_pull_requests'] = to_int(row.get('merged_pull_requests'))
            row['releases_total'] = to_int(row.get('releases_total'))
            row['issues_closed_ratio'] = to_float(row.get('issues_closed_ratio'))
            row['primary_language'] = row.get('primary_language') or 'N/A'
            rows.append(row)
    # compute
    age = [r['age_years'] for r in rows if r['age_years'] is not None]
    prs = [r['merged_pull_requests'] for r in rows if r['merged_pull_requests'] is not None]
    rels = [r['releases_total'] for r in rows if r['releases_total'] is not None]
    upd = [r['days_since_update'] for r in rows if r['days_since_update'] is not None]
    issues = [r['issues_closed_ratio'] for r in rows if r['issues_closed_ratio'] is not None]

    langs = [r['primary_language'] for r in rows]
    top_langs = collections.Counter(langs).most_common(10)

    rq07 = {}
    for lang, cnt in collections.Counter(langs).most_common(5):
        lang_rows = [r for r in rows if r['primary_language']==lang]
        l_prs = [r['merged_pull_requests'] for r in lang_rows if r['merged_pull_requests'] is not None]
        l_rels = [r['releases_total'] for r in lang_rows if r['releases_total'] is not None]
        l_upd = [r['days_since_update'] for r in lang_rows if r['days_since_update'] is not None]
        rq07[lang] = {
            'count': cnt,
            'median_prs': round(statistics.median(l_prs),2) if l_prs else 0,
            'median_releases': round(statistics.median(l_rels),2) if l_rels else 0,
            'median_days_update': round(statistics.median(l_upd),2) if l_upd else 0,
        }

    stats = {
        'age_years': stat_pack(age),
        'merged_pull_requests': stat_pack(prs),
        'releases_total': stat_pack(rels),
        'days_since_update': stat_pack(upd),
        'issues_closed_ratio': stat_pack(issues),
        'top_languages': top_langs,
        'rq07': rq07,
        'total_rows': len(rows)
    }
    return stats


def mk_table(stat, name):
    if not stat:
        return f"**{name}**: sem dados\n\n"
    return (f"**{name}**\n\n"
            f"- Count: {stat['count']}\n"
            f"- Mean: {stat['mean']}\n"
            f"- Median: {stat['median']}\n"
            f"- Min: {stat['min']}\n"
            f"- Max: {stat['max']}\n\n")


def generate_md(s1_stats, s2_stats):
    lines = []
    lines.append('# Resultados Detalhados — Análise das Coletas (Sprint 01 vs Sprint 02)\n')
    lines.append('> Observação: Sprint 01 coletou 100 repositórios; Sprint 02 coletou 1000 repositórios.\n')

    if s1_stats:
        lines.append('## Sprint 01 — Amostra 100\n')
        lines.append(f"Total repositórios: {s1_stats.get('total_rows',0)}\n\n")
        lines.append(mk_table(s1_stats.get('age_years'), 'Idade (anos)'))
        lines.append(mk_table(s1_stats.get('merged_pull_requests'), 'PRs Mergeados (contagem)'))
        lines.append(mk_table(s1_stats.get('releases_total'), 'Releases (contagem)'))
        lines.append(mk_table(s1_stats.get('days_since_update'), 'Dias desde última atualização'))
        lines.append(mk_table(s1_stats.get('issues_closed_ratio'), 'Razão de issues fechadas'))
        lines.append('### Top 10 linguagens (Sprint 01)\n')
        for l,c in s1_stats.get('top_languages',[]):
            lines.append(f'- {l}: {c}\n')
        lines.append('\n')
        lines.append('### RQ07 — Comparativo por Linguagem (Top 5)\n')
        for lang, vals in s1_stats.get('rq07',{}).items():
            lines.append(f"- {lang}: count={vals['count']}, median_prs={vals['median_prs']}, median_releases={vals['median_releases']}, median_days_update={vals['median_days_update']}\n")
        lines.append('\n')
    else:
        lines.append('## Sprint 01 — sem dados disponíveis\n')

    if s2_stats:
        lines.append('## Sprint 02 — Amostra 1000\n')
        lines.append(f"Total repositórios: {s2_stats.get('total_rows',0)}\n\n")
        lines.append(mk_table(s2_stats.get('age_years'), 'Idade (anos)'))
        lines.append(mk_table(s2_stats.get('merged_pull_requests'), 'PRs Mergeados (contagem)'))
        lines.append(mk_table(s2_stats.get('releases_total'), 'Releases (contagem)'))
        lines.append(mk_table(s2_stats.get('days_since_update'), 'Dias desde última atualização'))
        lines.append(mk_table(s2_stats.get('issues_closed_ratio'), 'Razão de issues fechadas'))
        lines.append('### Top 10 linguagens (Sprint 02)\n')
        for l,c in s2_stats.get('top_languages',[]):
            lines.append(f'- {l}: {c}\n')
        lines.append('\n')
        lines.append('### RQ07 — Comparativo por Linguagem (Top 5)\n')
        for lang, vals in s2_stats.get('rq07',{}).items():
            lines.append(f"- {lang}: count={vals['count']}, median_prs={vals['median_prs']}, median_releases={vals['median_releases']}, median_days_update={vals['median_days_update']}\n")
        lines.append('\n')
    else:
        lines.append('## Sprint 02 — sem dados disponíveis\n')

    # Comparação direta (medianas)
    lines.append('## Comparação entre Sprints (medianas)\n')
    def med(s, k):
        return s.get(k,{}).get('median') if s else None
    keys = [('age_years','Idade (anos)'),('merged_pull_requests','PRs Mergeados'),('releases_total','Releases'),('days_since_update','Dias desde última atualização'),('issues_closed_ratio','Razão issues fechadas')]
    lines.append('| Métrica | Sprint01 (100) | Sprint02 (1000) | Diferença (1000 - 100) |\n')
    lines.append('|---|---:|---:|---:|\n')
    for k, label in keys:
        m1 = med(s1_stats,k)
        m2 = med(s2_stats,k)
        diff = None
        if m1 is not None and m2 is not None:
            diff = round(m2 - m1,3)
        lines.append(f'| {label} | {m1 if m1 is not None else "N/A"} | {m2 if m2 is not None else "N/A"} | {diff if diff is not None else "N/A"} |\n')

    return '\n'.join(lines)


if __name__ == '__main__':
    s1 = analyze(S1)
    s2 = analyze(S2)
    md = generate_md(s1,s2)
    with open(OUT_MD,'w',encoding='utf-8') as f:
        f.write(md)
    print('WROTE', OUT_MD)
