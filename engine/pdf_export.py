"""
Onda 105: PDF export para forecast-narrativo + recomendacao via WeasyPrint.

Se weasyprint não instalado, retorna HTML string (caller decide).
"""

from __future__ import annotations

import time
from typing import Any


_CSS_BASE = """
@page { size: A4; margin: 18mm; }
html { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; color: #111; }
body { margin: 0; }
h1 { color: #d69e2e; font-size: 20pt; margin: 0 0 4pt 0; }
.subtitle { color: #666; font-size: 10pt; margin-bottom: 14pt; }
h2 { color: #222; font-size: 12pt; text-transform: uppercase; letter-spacing: 0.5pt;
     margin-top: 12pt; border-bottom: 1pt solid #d69e2e; padding-bottom: 2pt; }
h3 { color: #555; font-size: 10pt; margin-top: 10pt; }
.kpi-row { display: flex; gap: 18pt; margin: 6pt 0 12pt 0; }
.kpi { flex: 1; background: #f8f8f8; padding: 6pt; border-left: 2pt solid #d69e2e; }
.kpi-v { font-weight: 700; font-size: 14pt; color: #d69e2e; }
.kpi-l { font-size: 8pt; color: #888; text-transform: uppercase; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 4pt 0; }
th { border-bottom: 1pt solid #333; padding: 3pt 5pt; text-align: left; background: #f4f4f4; }
td { border-bottom: 0.5pt solid #ddd; padding: 3pt 5pt; }
.bar { background: #d69e2e; height: 10pt; display: inline-block; vertical-align: middle; }
.narrativa { background: #f8f8f8; padding: 10pt; border-left: 3pt solid #d69e2e;
             font-size: 9.5pt; line-height: 1.5; white-space: pre-wrap; }
.footer { margin-top: 18pt; padding-top: 4pt; border-top: 0.5pt dashed #999;
          font-size: 7.5pt; color: #888; }
"""


def _pct(v, nd=1):
    if v is None: return "—"
    return f"{v*100:.{nd}f}%"


def html_forecast(payload: dict) -> str:
    """Gera HTML do forecast-narrativo payload."""
    top = payload.get("top_estados_horizonte", [])
    evidencias = payload.get("evidencias_llm", [])
    cal = payload.get("calibracao")
    narr = payload.get("narrativa", "")

    max_prob = max((t.get("prob", 0) for t in top), default=1) or 1

    linhas = [
        "<!DOCTYPE html><html><head><meta charset='UTF-8'>",
        f"<title>Vila INTEIA — Forecast</title><style>{_CSS_BASE}</style></head><body>",
        "<h1>Vila INTEIA — Forecast Narrativo</h1>",
        f"<div class='subtitle'>Markov psico-histórico + LLM · gerado {time.strftime('%Y-%m-%d %H:%M')}</div>",
        "<div class='kpi-row'>",
        f"<div class='kpi'><div class='kpi-l'>Estado atual</div><div class='kpi-v'>{payload.get('estado_atual', '—')}</div></div>",
        f"<div class='kpi'><div class='kpi-l'>Horizonte</div><div class='kpi-v'>{payload.get('horizonte', '—')} steps</div></div>",
        f"<div class='kpi'><div class='kpi-l'>Mules</div><div class='kpi-v'>{payload.get('n_mules_recentes', 0)}</div></div>",
        f"<div class='kpi'><div class='kpi-l'>Entropia</div><div class='kpi-v'>{payload.get('entropia_inicial', 0):.2f} → {payload.get('entropia_final', 0):.2f}</div></div>",
        "</div>",
    ]

    if cal and cal.get("ativa"):
        linhas.append(
            f"<div style='background:#eff6ff;padding:6pt;font-size:9pt;margin-bottom:10pt'>"
            f"<b>Calibração Platt ativa:</b> a={cal.get('a', 0):.3f}, b={cal.get('b', 0):.3f}, "
            f"n={cal.get('n_amostras', 0)}</div>"
        )

    linhas.extend([
        "<h2>Top estados no horizonte</h2>",
        "<table><thead><tr><th>Estado</th><th>Probabilidade</th><th style='width:40%'>Barra</th></tr></thead><tbody>",
    ])
    for t in top[:5]:
        pct = t.get("prob", 0) * 100
        w = (t.get("prob", 0) / max_prob) * 100
        linhas.append(
            f"<tr><td>{t.get('estado', '—')}</td><td>{pct:.1f}%</td>"
            f"<td><span class='bar' style='width:{w*0.4:.1f}pt'></span></td></tr>"
        )
    linhas.append("</tbody></table>")

    if narr:
        linhas.extend(["<h2>Narrativa LLM</h2>", f"<div class='narrativa'>{narr}</div>"])

    if evidencias:
        linhas.append("<h2>Evidências LLM (conversas recentes)</h2>")
        for e in evidencias:
            linhas.append(
                f"<div style='margin:6pt 0;padding:6pt;background:#fafafa;border-left:2pt solid #888'>"
                f"<b>{e.get('parceiro', '—')}</b> · {e.get('tema', '—')} · {e.get('n_turnos', 0)}t<br>"
                f"<span style='font-size:8.5pt;color:#555'>{e.get('primeiro_turno', '')[:300]}</span>"
                f"</div>"
            )

    linhas.append(
        "<div class='footer'>Vila INTEIA · github.com/igormorais123/vila-inteia · "
        f"payload exportado {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}</div>"
        "</body></html>"
    )
    return "\n".join(linhas)


def html_recomendacao(payload: dict) -> str:
    """Gera HTML do recomendacao-intervencao payload."""
    ranking = payload.get("ranking", [])
    melhor = payload.get("melhor_intervencao", {})
    rec = payload.get("recomendacao_llm", "")

    max_prob = max((r.get("prob_outcome", 0) for r in ranking), default=1) or 1

    linhas = [
        "<!DOCTYPE html><html><head><meta charset='UTF-8'>",
        f"<title>Vila INTEIA — Recomendação</title><style>{_CSS_BASE}</style></head><body>",
        "<h1>Vila INTEIA — Recomendação Helena/Efesto</h1>",
        f"<div class='subtitle'>Multi-counterfactual sweep · gerado {time.strftime('%Y-%m-%d %H:%M')}</div>",
        "<div class='kpi-row'>",
        f"<div class='kpi'><div class='kpi-l'>Estado atual</div><div class='kpi-v'>{payload.get('estado_atual', '—')}</div></div>",
        f"<div class='kpi'><div class='kpi-l'>Outcome</div><div class='kpi-v'>{payload.get('outcome_desejado', '—')}</div></div>",
        f"<div class='kpi'><div class='kpi-l'>Horizonte</div><div class='kpi-v'>{payload.get('horizonte', '—')}</div></div>",
        "</div>",
        f"<h2>Melhor intervenção</h2>"
        f"<div style='background:#fef3c7;padding:10pt;font-size:12pt'>"
        f"<b>Forçar: {melhor.get('estado', '—')}</b> → P({payload.get('outcome_desejado', '?')}) = "
        f"{melhor.get('prob_outcome', 0)*100:.1f}%</div>",
        "<h2>Ranking top-5</h2>",
        "<table><thead><tr><th>Estado</th><th>P(outcome)</th><th>Estado mais provável</th><th>Barra</th></tr></thead><tbody>",
    ]
    for r in ranking[:5]:
        pct = r.get("prob_outcome", 0) * 100
        w = (r.get("prob_outcome", 0) / max_prob) * 100
        linhas.append(
            f"<tr><td>{r.get('estado', '—')}</td><td>{pct:.1f}%</td>"
            f"<td>{r.get('estado_mais_provavel', '—')}</td>"
            f"<td><span class='bar' style='width:{w*0.4:.1f}pt'></span></td></tr>"
        )
    linhas.append("</tbody></table>")

    if rec:
        linhas.extend(["<h2>Recomendação LLM</h2>", f"<div class='narrativa'>{rec}</div>"])

    linhas.append(
        "<div class='footer'>Vila INTEIA · Pearl do-calculus + LLM · "
        f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}</div>"
        "</body></html>"
    )
    return "\n".join(linhas)


def render_pdf(html_str: str) -> bytes | None:
    """Converte HTML → PDF bytes via WeasyPrint. None se não instalado."""
    try:
        from weasyprint import HTML
        return HTML(string=html_str).write_pdf()
    except ImportError:
        return None
    except Exception:
        return None
