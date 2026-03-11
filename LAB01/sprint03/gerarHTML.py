import csv, json, math, statistics, collections, os
from datetime import datetime

# Caminho absoluto em relação ao script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_IN = os.path.join(BASE_DIR, "coleta_1000repos.csv")
HTML_OUT = os.path.join(BASE_DIR, "dashboard.html")

def to_float(x):
    try: return float(x)
    except: return None

def to_int(x):
    try: return int(x)
    except: return None

rows = []
with open(CSV_IN, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        row["stars"] = to_int(row.get("stars"))
        row["age_years"] = to_float(row.get("age_years"))
        row["days_since_update"] = to_float(row.get("days_since_update"))
        row["merged_pull_requests"] = to_int(row.get("merged_pull_requests"))
        row["releases_total"] = to_int(row.get("releases_total"))
        row["issues_open"] = to_int(row.get("issues_open"))
        row["issues_closed"] = to_int(row.get("issues_closed"))
        row["issues_total"] = to_int(row.get("issues_total"))
        row["issues_closed_ratio"] = to_float(row.get("issues_closed_ratio"))
        rows.append(row)

# ==========================================
# Preparar dados para as questões de pesquisa
# ==========================================

def stat_pack(arr):
    if not arr: return {}
    return {
        "count": len(arr),
        "mean": round(statistics.mean(arr), 2),
        "median": round(statistics.median(arr), 2),
        "min": round(min(arr), 2),
        "max": round(max(arr), 2),
    }

age_years = [x["age_years"] for x in rows if x["age_years"] is not None]
prs = [x["merged_pull_requests"] for x in rows if x["merged_pull_requests"] is not None]
releases = [x["releases_total"] for x in rows if x["releases_total"] is not None]
days_update = [x["days_since_update"] for x in rows if x["days_since_update"] is not None]
issues_ratio = [x["issues_closed_ratio"] for x in rows if x["issues_closed_ratio"] is not None]

# Agregado geral para gráfico de issues (Doughnut)
total_issues_open_global = sum([x["issues_open"] for x in rows if x["issues_open"] is not None])
total_issues_closed_global = sum([x["issues_closed"] for x in rows if x["issues_closed"] is not None])

langs = [x.get("primary_language") or "N/A" for x in rows]
top_langs_counter = collections.Counter(langs).most_common(5) # Top 5 para a RQ 07

# RQ 07: Correlacionar linguagem X com PRs, Releases, e Atualizações frequentes
rq07_stats = {}
for lang, count in top_langs_counter:
    lang_rows = [x for x in rows if (x.get("primary_language") or "N/A") == lang]
    l_prs = [x["merged_pull_requests"] for x in lang_rows if x["merged_pull_requests"] is not None]
    l_rels = [x["releases_total"] for x in lang_rows if x["releases_total"] is not None]
    l_upds = [x["days_since_update"] for x in lang_rows if x["days_since_update"] is not None]
    
    rq07_stats[lang] = {
        "count": count,
        "median_prs": statistics.median(l_prs) if l_prs else 0,
        "median_releases": statistics.median(l_rels) if l_rels else 0,
        "median_days_update": statistics.median(l_upds) if l_upds else 0,
    }

stats = {
    "age_years": stat_pack(age_years),
    "merged_pull_requests": stat_pack(prs),
    "releases_total": stat_pack(releases),
    "days_since_update": stat_pack(days_update),
    "issues_closed_ratio": stat_pack(issues_ratio),
    "top_languages": collections.Counter(langs).most_common(10),
    "rq07": rq07_stats,
    "global_issues_open": total_issues_open_global,
    "global_issues_closed": total_issues_closed_global
}

# we'll build the HTML string
html_template = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Dashboard Lab01 Sprint 03 - Avaliação das RQs</title>
  <!-- Chart.js para gráficos premium -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- Google Fonts para tipografia moderna -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #f8fafc;
      color: #0f172a;
      margin: 0;
      padding: 40px 20px;
    }
    .container { max-width: 1400px; margin: 0 auto; }
    h1, h2, h3 { color: #1e293b; margin-top: 0; }
    .header { margin-bottom: 40px; text-align: center; }
    .header h1 { font-size: 32px; font-weight: 700; margin-bottom: 8px;}
    .header p { color: #64748b; font-size: 16px; margin: 0; }
    
    .grid { display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
    .card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
      transition: transform 0.2s;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .card-title { font-size: 13px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
    .stat-value { font-size: 32px; font-weight: 700; color: #0f172a; }
    .stat-sub { font-size: 13px; color: #94a3b8; margin-top: 6px; display: flex; justify-content: space-between; }
    
    .charts-grid { display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); margin-top: 20px;}
    .charts-grid-3 { display: grid; gap: 20px; grid-template-columns: repeat(3, 1fr); margin-top: 20px;}
    canvas { max-width: 100%; }
    
    @media (max-width: 1024px) {
        .charts-grid-3 { grid-template-columns: 1fr; }
    }

    .table-container {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow-x: auto;
      margin-top: 20px;
      padding: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .search-wrapper { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
    input[type="text"] {
      padding: 12px 16px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      width: 100%;
      max-width: 450px;
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      transition: all 0.2s;
    }
    input[type="text"]:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #f1f5f9; padding: 14px 12px; text-align: left; font-size: 14px; }
    th {
      background: #f8fafc;
      font-weight: 600;
      color: #334155;
      cursor: pointer;
      user-select: none;
      transition: background 0.2s;
    }
    th:hover { background: #e2e8f0; }
    .right { text-align: right; }
    .sort-icon { font-size: 12px; margin-left: 6px; display: inline-block; width: 14px; color: #3b82f6; }
    
    .badge {
      display: inline-block; padding: 4px 8px; border-radius: 4px;
      font-size: 12px; font-weight: 600; background: #e0f2fe; color: #0284c7;
    }
    
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Dashboard Analítico de Repositórios GitHub</h1>
    <p>Avaliação final da amostra extraída para o Laboratório 01 - Sprint 03 com 1.000 respositórios avaliados.</p>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-title">RQ 01. Idade Média</div>
      <div class="stat-value" id="s_age">--</div>
      <div class="stat-sub"><span id="s_age_sub"></span><span>Anos</span></div>
    </div>
    <div class="card">
      <div class="card-title">RQ 02. PRs Aceitos (Mediana)*</div>
      <div class="stat-value" id="s_prs">--</div>
      <div class="stat-sub"><span id="s_prs_sub"></span><span>Contribuições</span></div>
    </div>
    <div class="card">
      <div class="card-title">RQ 03. Releases (Mediana)*</div>
      <div class="stat-value" id="s_rels">--</div>
      <div class="stat-sub"><span id="s_rels_sub"></span><span>Lançamentos</span></div>
    </div>
    <div class="card">
      <div class="card-title">RQ 04. Dias s/ Update</div>
      <div class="stat-value" id="s_upd">--</div>
      <div class="stat-sub"><span id="s_upd_sub"></span><span>Dias (Mediana)</span></div>
    </div>
    <div class="card">
      <div class="card-title">RQ 06. Issues Fechadas</div>
      <div class="stat-value" id="s_iss">--</div>
      <div class="stat-sub"><span id="s_iss_sub"></span><span>Razão Fechadas/Total</span></div>
    </div>
  </div>
  <p style="font-size:12px; color:#94a3b8; margin-top:8px;">* Usamos a mediana para PRs e Releases para evitar que repositórios com números astronômicos (outliers) distorçam a realidade geral.</p>

  <div class="charts-grid-3">
    <div class="card">
      <h3>RQ 01. Histograma de Idades</h3>
      <p style="font-size:13px; color:#64748b; margin-top:-6px; margin-bottom:12px;">Sistemas populares são antigos/maduros?</p>
      <canvas id="ageChart" height="250"></canvas>
    </div>
    <div class="card">
      <h3>RQ 02. Idade x Contribuições (Scatter)</h3>
      <p style="font-size:13px; color:#64748b; margin-top:-6px; margin-bottom:12px;">Repositórios antigas acumulam mais PRs?</p>
      <canvas id="scatterChart" height="250"></canvas>
    </div>
    <div class="card">
      <h3>RQ 06. Status Geral das Issues (Pizza)</h3>
      <p style="font-size:13px; color:#64748b; margin-top:-6px; margin-bottom:12px;">Desempenho somado dos 1000 repositórios</p>
      <div style="width: 100%; height: 250px; display: flex; justify-content: center;">
         <canvas id="issueDoughnutChart"></canvas>
      </div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="card">
      <h3>RQ 05. Linguagens mais populares</h3>
      <p style="font-size:13px; color:#64748b; margin-top:-6px; margin-bottom:12px;">Distribuição entre as linguagens globais encontradas.</p>
      <canvas id="langChart" height="220"></canvas>
    </div>
    <div class="card">
      <h3>RQ 07. Atividade pelo Top 5 Linguagens</h3>
      <p style="font-size:13px; color:#64748b; margin-top:-6px; margin-bottom:12px;">A linguagem dita os PRs ou Releases? (Medianas) <br/>  </p>
      <canvas id="doubleBarChart" height="220"></canvas>
    </div>
  </div>


  <div class="table-container">
    <div class="search-wrapper">
      <input id="q" type="text" placeholder="Buscar por repo (ex: react) ou linguagem (ex: python)..." />
      <span style="font-size: 14px; color:#64748b; font-weight: 500;" id="filtered"></span>
    </div>
    <table id="t">
      <thead>
        <tr>
          <th data-k="name_with_owner">Repo<span class="sort-icon"></span></th>
          <th data-k="stars" class="right">Stars<span class="sort-icon"></span></th>
          <th data-k="age_years" class="right">Idade<span class="sort-icon"></span></th>
          <th data-k="days_since_update" class="right">Dias s/ update<span class="sort-icon"></span></th>
          <th data-k="primary_language">Linguagem<span class="sort-icon"></span></th>
          <th data-k="merged_pull_requests" class="right">PRs merge<span class="sort-icon"></span></th>
          <th data-k="releases_total" class="right">Releases<span class="sort-icon"></span></th>
          <th data-k="issues_closed_ratio" class="right">% issues fechadas<span class="sort-icon"></span></th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</div>

  <script>
    const DATA = __DATA_PLACEHOLDER__;
    const STATS = __STATS_PLACEHOLDER__;

    // Utilitários de Formatação
    function fmt(n) { return typeof n === 'number' ? n.toLocaleString('pt-BR') : n; }
    function fmtPct(x) { return typeof x === 'number' ? (x*100).toFixed(1)+'%' : ''; }
    
    // Preenchendo os Cards Superiores
    document.getElementById("s_age").innerText = STATS.age_years.median.toFixed(1);
    document.getElementById("s_age_sub").innerText = "Média: " + STATS.age_years.mean.toFixed(1);
    
    document.getElementById("s_prs").innerText = fmt(STATS.merged_pull_requests.median);
    document.getElementById("s_prs_sub").innerText = "Média: " + fmt(STATS.merged_pull_requests.mean);
    
    document.getElementById("s_rels").innerText = fmt(STATS.releases_total.median);
    document.getElementById("s_rels_sub").innerText = "Média: " + fmt(STATS.releases_total.mean);

    document.getElementById("s_upd").innerText = STATS.days_since_update.median;
    document.getElementById("s_upd_sub").innerText = "Média: " + STATS.days_since_update.mean;

    document.getElementById("s_iss").innerText = fmtPct(STATS.issues_closed_ratio.median);
    document.getElementById("s_iss_sub").innerText = "Média: " + fmtPct(STATS.issues_closed_ratio.mean);

    // -------------------------------------------------------------
    // Gráfico 1 Chart.js: Histograma de Idades (RQ01)
    // -------------------------------------------------------------
    const ages = DATA.map(d => d.age_years).filter(x => x !== null);
    const bins = 8;
    const minAge = Math.floor(Math.min(...ages));
    const maxAge = Math.ceil(Math.max(...ages));
    const binSize = (maxAge - minAge) / bins;
    const ageCounts = Array(bins).fill(0);
    const ageLabels = [];
    
    for(let i=0; i<bins; i++) {
        let bMin = minAge + i * binSize;
        let bMax = bMin + binSize;
        ageLabels.push(`${bMin.toFixed(0)} - ${bMax.toFixed(0)} Anos`);
        ages.forEach(a => {
            if(a >= bMin && (i === bins - 1 ? a <= bMax : a < bMax)) {
                ageCounts[i]++;
            }
        });
    }

    new Chart(document.getElementById('ageChart'), {
      type: 'bar',
      data: {
        labels: ageLabels,
        datasets: [{
          label: 'Qtd. de Repositórios',
          data: ageCounts,
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { title: { display: true, text: 'Intervalo de Idade'}, grid: {display: false} },
          y: { title: { display: true, text: 'Nº de Repositórios'}, beginAtZero: true }
        }
      }
    });

    // -------------------------------------------------------------
    // Gráfico 2 Chart.js: Dispersão Idade x PRs (Esquerda) (RQ02 nova)
    // -------------------------------------------------------------
    const scatterData = DATA.filter(d => d.age_years != null && d.merged_pull_requests != null)
                            .map(d => ({ x: d.age_years, y: d.merged_pull_requests }));

    new Chart(document.getElementById('scatterChart'), {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Repos (Idade vs PRs)',
          data: scatterData,
          backgroundColor: 'rgba(236, 72, 153, 0.6)', /* Pink color */
          pointBorderColor: 'rgba(236, 72, 153, 1)',
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { 
            title: { display: true, text: 'Idade (Anos)' },
            grid: { display: false }
          },
          y: { 
            title: { display: true, text: 'PRs Mergeados (Log scale)' },
            type: 'logarithmic', // Escala Logaritmica vital devido aos outliers massivos aqui
            ticks: {
                 callback: function (value, index, values) {
                     return Number(value.toString());
                 }
            }
          }
        }
      }
    });

    // -------------------------------------------------------------
    // Gráfico 3 Chart.js: Percentual Global de Problemas (Pizza) (RQ06)
    // -------------------------------------------------------------
    new Chart(document.getElementById('issueDoughnutChart'), {
      type: 'doughnut',
      data: {
        labels: ['Issues Fechadas', 'Issues Abertas'],
        datasets: [{
          data: [STATS.global_issues_closed, STATS.global_issues_open],
          backgroundColor: [
            'rgba(16, 185, 129, 0.8)', /* Verde p/ Fechado */
            'rgba(244, 63, 94, 0.8)'   /* Vermelho p/ Aberto */
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });

    // -------------------------------------------------------------
    // Gráfico 4 Chart.js: Linguagens (RQ05)
    // -------------------------------------------------------------
    new Chart(document.getElementById('langChart'), {
      type: 'bar',
      data: {
        labels: STATS.top_languages.map(x => x[0]),
        datasets: [{
          label: 'Qtd de Repositórios',
          data: STATS.top_languages.map(x => x[1]),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: {
          x: { title: { display: true, text: 'Nº de Repositórios'}, beginAtZero: true },
          y: { title: { display: false}, grid: {display: false} }
        }
      }
    });

    // -------------------------------------------------------------
    // Gráfico 5 Chart.js: Barra Dupla Top 5 Linguagens (RQ07)
    // -------------------------------------------------------------
    const topLangsKeys = Object.keys(STATS.rq07);
    const prsMedians = topLangsKeys.map(k => STATS.rq07[k].median_prs);
    const relsMedians = topLangsKeys.map(k => STATS.rq07[k].median_releases);

    new Chart(document.getElementById('doubleBarChart'), {
      type: 'bar',
      data: {
        labels: topLangsKeys,
        datasets: [
          {
            label: 'Mediana de PRs',
            data: prsMedians,
            backgroundColor: 'rgba(168, 85, 247, 0.8)', /* Roxo */
            yAxisID: 'y'
          },
          {
            label: 'Mediana de Releases',
            data: relsMedians,
            backgroundColor: 'rgba(234, 179, 8, 0.8)', /* Amarelo */
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            position: 'top',
          }
        },
        scales: {
          x: {
              title: { display: false },
              grid: { display:false }
          },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: { display: true, text: 'PRs' }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            grid: { drawOnChartArea: false }, // only want the grid lines for one axis to show up
            title: { display: true, text: 'Releases' }
          },
        }
      }
    });


    // -------------------------------------------------------------
    // Tabela Principal Interativa
    // -------------------------------------------------------------
    let sortKey = "stars";
    let sortAsc = false;
    let filtered = DATA.slice();
    
    function compare(a,b,k) {
      const va = a[k]; const vb = b[k];
      if (va === vb) return 0;
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (typeof va === "number" && typeof vb === "number") return va - vb;
      return String(va).localeCompare(String(vb));
    }

    function renderTable() {
      const tbody = document.querySelector("#t tbody");
      tbody.innerHTML = "";
      
      const arr = filtered.slice().sort((a,b) => {
        const c = compare(a,b,sortKey);
        return sortAsc ? c : -c;
      });

      arr.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${r.name_with_owner || ""}</strong></td>
          <td class="right">${fmt(r.stars)}</td>
          <td class="right">${r.age_years ? r.age_years.toFixed(1) : ""}</td>
          <td class="right">${fmt(r.days_since_update)}</td>
          <td><span class="badge" style="background:#f1f5f9; color:#475569;">${r.primary_language || "-"}</span></td>
          <td class="right">${fmt(r.merged_pull_requests)}</td>
          <td class="right">${fmt(r.releases_total)}</td>
          <td class="right">${fmtPct(r.issues_closed_ratio)}</td>
        `;
        tbody.appendChild(tr);
      });
      
      document.getElementById("filtered").innerText = `Mostrando ${arr.length} de ${DATA.length}`;

      // Atualiza os ícones de setas da coluna
      document.querySelectorAll("th[data-k]").forEach(th => {
        const icon = th.querySelector('.sort-icon');
        icon.innerText = '';
        if (th.getAttribute('data-k') === sortKey) {
          icon.innerText = sortAsc ? ' ▲' : ' ▼';
        }
      });
    }

    document.querySelectorAll("th[data-k]").forEach(th => {
      th.addEventListener("click", () => {
        const k = th.getAttribute("data-k");
        if (k === sortKey) sortAsc = !sortAsc;
        else { sortKey = k; sortAsc = false; }
        renderTable();
      });
    });

    document.getElementById("q").addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) { filtered = DATA.slice(); }
      else {
        filtered = DATA.filter(r => 
          (r.name_with_owner || "").toLowerCase().includes(q) || 
          (r.primary_language || "").toLowerCase().includes(q)
        );
      }
      renderTable();
    });

    renderTable(); // Inicializa
  </script>
</body>
</html>
"""

html_final = html_template.replace("__DATA_PLACEHOLDER__", json.dumps(rows, ensure_ascii=False))
html_final = html_final.replace("__STATS_PLACEHOLDER__", json.dumps(stats, ensure_ascii=False))

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html_final)

print(f"Gerado: {HTML_OUT}")