"""Helena report adapter — wraps a ForecastResult in the canonical 8-block format.

Aprendizado importado de C:\\Users\\IgorPC\\.claude\\skills\\helena (SKILL.md):
todo output substancial segue Status / Achado / Mecanismo / Red Team /
Cenários / Recomendação / Calibração de confiança / Curiosidade residual.

Determinístico: sem LLM, sem rede. Toma um ForecastResult (ou dict equivalente
produzido por combined_pipeline.combined_report) e devolve um dict com os
8 blocos prontos pra renderização (markdown, JSON, frontend).
"""

from __future__ import annotations

from typing import Any

from engine.forecast_result import ForecastResult


def _as_dict(result: ForecastResult | dict) -> dict:
    if isinstance(result, ForecastResult):
        return result.as_dict()
    return result


def _selective_coverage(d: dict, threshold: float) -> Any:
    """Lookup robusto para selective.coverage — chave pode ser float ou string
    (JSON roundtrip converte float keys em str). Tenta ambas as formas."""
    sel = d.get("selective", {}) or {}
    candidates = (threshold, str(threshold), f"{threshold:.1f}", f"{threshold:.2f}")
    for k in candidates:
        if k in sel:
            v = sel[k]
            if isinstance(v, dict):
                return v.get("coverage", "n/a")
            return v
    return "n/a"


def _confidence_label(n: int, ci_width: float, reliability: float) -> tuple[str, str]:
    """alta / média / baixa + justificativa one-liner."""
    if n < 20:
        return "baixa", f"n={n} insuficiente (<20) — poder estatístico crítico"
    if n < 50 or ci_width > 0.08 or reliability > 0.05:
        why = []
        if n < 50:
            why.append(f"n={n} modesto (<50)")
        if ci_width > 0.08:
            why.append(f"CI95 largo ({ci_width:.3f})")
        if reliability > 0.05:
            why.append(f"reliability alta ({reliability:.3f}) — descalibrado")
        return "média", "; ".join(why)
    return "alta", f"n={n}, CI95={ci_width:.3f}, reliability={reliability:.3f}"


def _scenarios(brier: float, ci: tuple[float, float], baseline: float) -> dict:
    lo, hi = ci
    return {
        "otimista": {"brier": lo, "delta_vs_baseline": round(lo - baseline, 4)},
        "base": {"brier": brier, "delta_vs_baseline": round(brier - baseline, 4)},
        "pessimista": {"brier": hi, "delta_vs_baseline": round(hi - baseline, 4)},
    }


def _red_team(brier: float, ci: tuple[float, float], baseline: float,
              murphy: dict, cv: dict) -> list[str]:
    """Contra-hipóteses estruturadas — o que provaria a predição errada."""
    out: list[str] = []
    lo, hi = ci
    if hi >= baseline:
        out.append(
            f"CI95 superior ({hi:.4f}) >= baseline uncertainty ({baseline:.4f}) — "
            "skill pode ser ruído amostral"
        )
    if murphy.get("reliability", 0) > 0.05:
        out.append(
            f"Reliability {murphy['reliability']:.4f} > 0.05 — modelo descalibrado, "
            "probabilidades não correspondem à frequência observada"
        )
    if murphy.get("resolution", 0) < 0.02:
        out.append(
            f"Resolution {murphy['resolution']:.4f} < 0.02 — modelo quase não "
            "diferencia eventos, perto de prever a base-rate"
        )
    cv_std = cv.get("std_brier")
    cv_mean = cv.get("mean_brier")
    if cv_std is not None and cv_mean and cv_std > 0.5 * cv_mean:
        out.append(
            f"CV std_brier ({cv_std:.4f}) > 50% do mean ({cv_mean:.4f}) — "
            "performance instável entre folds"
        )
    if not out:
        out.append("nenhuma contra-hipótese forte ativada pelos diagnósticos")
    return out


def _recommendation(conf_label: str, brier: float, baseline: float,
                    murphy: dict, n: int) -> str:
    if conf_label == "baixa" and n < 20:
        return f"Coletar holdout maior (alvo n>=50) antes de qualquer claim"
    if murphy.get("reliability", 0) > 0.05:
        return "Recalibrar (Platt/isotonic) — engine.calibration ou empirical_bayes"
    if brier >= baseline:
        return "Modelo não bate base-rate — investigar features e priors antes de produção"
    if murphy.get("resolution", 0) < 0.02:
        return "Aumentar discriminação: revisar feature engineering ou ensemble"
    return f"Promover para produção monitorada com gate brier <= {baseline:.3f}"


def _achado(brier: float, baseline: float, ci: tuple[float, float]) -> str:
    delta = brier - baseline
    lo, hi = ci
    if delta < 0 and hi < baseline:
        return (f"Bate baseline em {abs(delta):.4f} ({abs(delta)/baseline*100:.1f}%) "
                f"com CI95=[{lo:.4f}, {hi:.4f}] inteiramente abaixo — skill real")
    if delta < 0:
        return (f"Aparenta bater baseline em {abs(delta):.4f} mas CI95 superior "
                f"({hi:.4f}) cobre baseline ({baseline:.4f}) — skill incerto")
    return (f"Não bate baseline (delta=+{delta:.4f}) — predições não agregam "
            "valor sobre prever a frequência marginal")


def helena_report(result: ForecastResult | dict, *, dataset_name: str = "n/a") -> dict:
    """Envolve um ForecastResult no formato canônico Helena (8 blocos).

    Args:
        result: ForecastResult ou dict equivalente (combined_report output).
        dataset_name: nome do dataset, vai pro bloco status.

    Returns:
        dict com chaves: status, achado, evidencia, mecanismo, red_team,
        cenarios, recomendacao, calibracao_confianca, curiosidade_residual.
    """
    d = _as_dict(result)
    n = d["n"]
    brier = d["base_brier"]
    ci = tuple(d["bootstrap_brier_ci"])
    murphy = d.get("murphy", {})
    cv = d.get("time_series_cv", {})
    baseline = murphy.get("uncertainty", 0.25)
    ci_width = ci[1] - ci[0]
    rel = murphy.get("reliability", 0.0)

    conf_label, conf_why = _confidence_label(n, ci_width, rel)

    return {
        "status": (f"Dataset={dataset_name} n={n} brier={brier:.4f} "
                   f"baseline_unc={baseline:.4f} acc={d['base_acc']:.3f}"),
        "achado": _achado(brier, baseline, ci),
        "evidencia": {
            "n_eventos": n,
            "base_brier": brier,
            "bootstrap_ci95": ci,
            "murphy": murphy,
            "time_series_cv": cv,
        },
        "mecanismo": (
            f"Brier {brier:.4f} = reliability {rel:.4f} + uncertainty {baseline:.4f} "
            f"- resolution {murphy.get('resolution', 0):.4f} (Murphy 1973)"
        ),
        "red_team": _red_team(brier, ci, baseline, murphy, cv),
        "cenarios": _scenarios(brier, ci, baseline),
        "recomendacao": _recommendation(conf_label, brier, baseline, murphy, n),
        "calibracao_confianca": {"label": conf_label, "justificativa": conf_why},
        "curiosidade_residual": (
            f"Selective coverage @0.30: {_selective_coverage(d, 0.30)}, "
            f"conformal width: {d.get('conformal', {}).get('mean_width', 'n/a')}"
        ),
    }


def render_markdown(report: dict) -> str:
    """Renderiza o report no formato Helena 8-blocos como markdown."""
    rt = "\n".join(f"  - {x}" for x in report["red_team"])
    cen = report["cenarios"]
    cen_md = (
        f"  - Otimista: brier={cen['otimista']['brier']:.4f} "
        f"(Δbase={cen['otimista']['delta_vs_baseline']:+.4f})\n"
        f"  - Base: brier={cen['base']['brier']:.4f} "
        f"(Δbase={cen['base']['delta_vs_baseline']:+.4f})\n"
        f"  - Pessimista: brier={cen['pessimista']['brier']:.4f} "
        f"(Δbase={cen['pessimista']['delta_vs_baseline']:+.4f})"
    )
    cc = report["calibracao_confianca"]
    return (
        f"## 1. Status\n{report['status']}\n\n"
        f"## 2. Achado principal\n{report['achado']}\n\n"
        f"## 3. Mecanismo\n{report['mecanismo']}\n\n"
        f"## 4. Red Team (contra-hipóteses)\n{rt}\n\n"
        f"## 5. Cenários\n{cen_md}\n\n"
        f"## 6. Recomendação\n{report['recomendacao']}\n\n"
        f"## 7. Calibração de confiança\n"
        f"**{cc['label'].upper()}** — {cc['justificativa']}\n\n"
        f"## 8. Curiosidade residual\n{report['curiosidade_residual']}\n"
    )
