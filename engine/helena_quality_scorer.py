"""Helena 6-dimension quality scorer for forecast reports.

Importado de C:\\Users\\IgorPC\\.claude\\skills\\helena (SKILL.md § Critérios
de Qualidade — AutoResearch score 94.2/100). Toda entrega Helena passa por
6 dimensões. Adaptado para outputs de helena_report (forecast):

1. Dados antes de opinião — evidencia populada, n suficiente
2. Red Team explícito — contra-hipóteses listadas (ou declaração de ausência)
3. Calibração de confiança — label + justificativa
4. Acionabilidade — recomendação com verbo de ação concreto
5. Profundidade — mecanismo cita Murphy decomp, cenários têm 3 níveis
6. Protocolo Sem Muro — achado direto (não bajulação), declara incerteza
   quando CI cobre baseline em vez de mascarar

Determinístico, sem LLM. Retorna score 0-100 + breakdown por dimensão.
Útil em CI/regression: rodar score após cada change pra detectar regressão.
"""

from __future__ import annotations

import re

ACTION_VERBS = (
    "promover", "recalibrar", "coletar", "investigar", "aumentar",
    "revisar", "reduzir", "ajustar", "treinar", "validar",
)

WEASEL_WORDS = ("talvez", "pode ser que", "possivelmente", "quem sabe",
                "eventualmente", "se calhar")


def _check_dados(report: dict) -> tuple[int, str]:
    ev = report.get("evidencia", {})
    n = ev.get("n_eventos", 0)
    murphy = ev.get("murphy") or {}
    has_ci = bool(ev.get("bootstrap_ci95"))
    # Murphy decomp completo exige reliability + resolution + uncertainty.
    # Antes aceitava bool(murphy) — dict parcial passava.
    murphy_keys_required = {"reliability", "resolution", "uncertainty"}
    has_full_murphy = isinstance(murphy, dict) and murphy_keys_required.issubset(murphy.keys())
    if n >= 20 and has_full_murphy and has_ci:
        return 1, f"OK (n={n}, murphy completo+CI presentes)"
    parts = []
    if n < 20:
        parts.append(f"n={n} insuficiente")
    if not has_full_murphy:
        missing = murphy_keys_required - set(murphy.keys() if isinstance(murphy, dict) else [])
        parts.append(f"Murphy incompleto (falta: {sorted(missing)})" if missing else "sem Murphy decomp")
    if not has_ci:
        parts.append("sem bootstrap CI")
    return 0, "; ".join(parts)


def _check_red_team(report: dict) -> tuple[int, str]:
    rt = report.get("red_team", [])
    if not rt:
        return 0, "red_team vazio"
    if any("nenhuma" in x.lower() for x in rt):
        return 1, "OK (declara ausência explícita)"
    if any(len(x) > 30 for x in rt):
        return 1, f"OK ({len(rt)} contra-hipótese(s) concretas)"
    return 0, "red_team trivial"


def _check_calibracao(report: dict) -> tuple[int, str]:
    cc = report.get("calibracao_confianca", {})
    label = cc.get("label", "")
    why = cc.get("justificativa", "")
    if label in ("alta", "média", "baixa") and len(why) > 10:
        return 1, f"OK ({label}: {why[:50]}...)"
    return 0, f"label='{label}' justificativa={len(why)} chars"


def _check_acionabilidade(report: dict) -> tuple[int, str]:
    rec = report.get("recomendacao", "").lower()
    if not rec:
        return 0, "recomendação vazia"
    for verb in ACTION_VERBS:
        # Word-boundary: 'promover' não pode passar dentro de 'compromover' nem
        # disparar para substring acidental. \b cobre Unicode em re padrão py3.
        match = re.search(rf"\b{re.escape(verb)}\b", rec)
        if not match:
            continue
        # Detectar negação imediata: "não promover", "sem validar", "evitar X"
        # invertem a polaridade da ação. Olhamos os ~25 chars antes do verbo.
        prefix = rec[max(0, match.start() - 25): match.start()]
        if re.search(r"\b(não|nao|sem|evitar|jamais|nunca)\b\s*\S*\s*$", prefix):
            return 0, f"verbo '{verb}' negado em '...{prefix.strip()} {verb}...'"
        return 1, f"OK (verbo='{verb}')"
    return 0, f"sem verbo de ação ({rec[:40]}...)"


def _check_profundidade(report: dict) -> tuple[int, str]:
    mec = report.get("mecanismo", "")
    mec_low = mec.lower()
    cen = report.get("cenarios", {})
    # Doc da skill promete "Murphy decomp citado" — passamos a exigir o
    # literal "murphy" no mecanismo, não só os componentes da decomp.
    has_murphy_citation = "murphy" in mec_low
    has_murphy_terms = all(t in mec_low for t in ("reliability", "resolution"))
    has_3_scenarios = set(cen.keys()) == {"otimista", "base", "pessimista"}
    if has_murphy_citation and has_murphy_terms and has_3_scenarios:
        return 1, "OK (Murphy citado + decomp + 3 cenários)"
    parts = []
    if not has_murphy_citation:
        parts.append("mecanismo não cita Murphy")
    if not has_murphy_terms:
        parts.append("sem reliability+resolution")
    if not has_3_scenarios:
        parts.append("cenários incompletos")
    return 0, "; ".join(parts)


def _check_sem_muro(report: dict) -> tuple[int, str]:
    achado = report.get("achado", "").lower()
    if not achado:
        return 0, "achado vazio"
    weasels = [w for w in WEASEL_WORDS if w in achado]
    if weasels:
        return 0, f"weasel words: {weasels}"
    declares_uncertainty = any(t in achado for t in
                                ("incerto", "não bate", "ruído", "skill real", "cobre baseline"))
    if declares_uncertainty:
        return 1, "OK (declara estado claramente)"
    if len(achado) < 20:
        return 0, "achado muito curto"
    return 1, "OK (afirmação direta)"


CHECKS = (
    ("dados_antes_opiniao", _check_dados),
    ("red_team_explicito", _check_red_team),
    ("calibracao_confianca", _check_calibracao),
    ("acionabilidade", _check_acionabilidade),
    ("profundidade", _check_profundidade),
    ("protocolo_sem_muro", _check_sem_muro),
)


def score_helena_report(report: dict) -> dict:
    """Aplica 6-dim quality check num helena_report dict.

    Returns dict com 'score' (0-100), 'passed' (count), 'total' (6) e
    'breakdown' (dict por dimensão com {passed: bool, justificativa: str}).
    """
    breakdown: dict[str, dict] = {}
    passed = 0
    for name, fn in CHECKS:
        ok, msg = fn(report)
        breakdown[name] = {"passed": bool(ok), "justificativa": msg}
        passed += ok
    score = round(passed / len(CHECKS) * 100, 1)
    return {
        "score": score,
        "passed": passed,
        "total": len(CHECKS),
        "breakdown": breakdown,
    }


def render_scorecard(scored: dict) -> str:
    """Renderiza scorecard como markdown."""
    lines = [
        f"### Helena Quality Score: **{scored['score']}/100** "
        f"({scored['passed']}/{scored['total']} dimensões)",
        "",
        "| Dimensão | Status | Justificativa |",
        "|---|:-:|---|",
    ]
    for name, info in scored["breakdown"].items():
        mark = "✓" if info["passed"] else "✗"
        lines.append(f"| {name.replace('_', ' ')} | {mark} | {info['justificativa']} |")
    return "\n".join(lines)
