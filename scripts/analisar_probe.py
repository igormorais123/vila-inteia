"""Onda 164: calibração do threshold de outcome_probe via curva ROC.

Lê data/n100/probe_legacy_results.jsonl + data/backtest_real_ondas_134_153_3ds.json
(brier dos 9 eventos validados) e:

1. Constrói rótulo positivo "evento trivial" se o blend final acertou o outcome
   E o agente teve baixa dispersão (proxy de evento conhecido pelo modelo).
2. Trata p_outcome_mean como score de leakage.
3. Computa curva ROC, encontra threshold ótimo (Youden's J) e tabela.
4. Lista classificação final dos 100 legacy.
5. Gera .planning/n100/probe_calibracao.md.

NÃO altera LEAKAGE_THRESHOLD_DEFAULT em outcome_probe.py — esse é congelado
na campanha. Esse script informa se 0.65 é defensável ou se precisa ajuste
ANTES do passo 1 da campanha (P1.2 da Helena).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


REPO = Path(__file__).resolve().parents[1]
PROBE_PATH = REPO / "data" / "n100" / "probe_legacy_results.jsonl"
BACKTEST_PATH = REPO / "data" / "backtest_real_ondas_134_153_3ds.json"
OUT_MD = REPO / ".planning" / "n100" / "probe_calibracao.md"


def carregar_probes(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def carregar_brier_legacy(path: Path) -> dict[str, dict]:
    """Mapeia evento_id → {'acertou': bool, 'prob_blend_final': float, 'outcome': int}."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for ds in raw["datasets"]:
        for e in ds["eventos"]:
            out[e["evento_id"]] = {
                "acertou": bool(e.get("acertou_blend", False)),
                "prob_blend_final": float(e.get("prob_blend_final", 0.5)),
                "outcome": int(e.get("outcome_real", 0)),
            }
    return out


def construir_rotulos(probes: list[dict], brier_legacy: dict) -> list[tuple[float, int]]:
    """Retorna lista [(score_probe, label_trivial)] para evento que tem brier conhecido.

    label=1 (trivial/leakage suspeito): blend acertou COM probabilidade ≥ 0.7
    label=0 (não-trivial): blend errou OU probabilidade próxima de 0.5
    Eventos sem brier conhecido são descartados desta análise.
    """
    rotulos = []
    for r in probes:
        eid = r["id"]
        if eid not in brier_legacy:
            continue
        b = brier_legacy[eid]
        prob = b["prob_blend_final"]
        outcome = b["outcome"]
        prob_outcome = prob if outcome == 1 else (1 - prob)
        trivial = 1 if (b["acertou"] and prob_outcome >= 0.7) else 0
        rotulos.append((float(r["p_outcome_mean"]), trivial))
    return rotulos


def curva_roc(rotulos: list[tuple[float, int]], n_bins: int = 21) -> list[dict]:
    """Para cada threshold ∈ [0,1] em n_bins passos, computa TPR e FPR."""
    if not rotulos:
        return []
    pos = sum(1 for _, y in rotulos if y == 1)
    neg = sum(1 for _, y in rotulos if y == 0)
    if pos == 0 or neg == 0:
        # Sem variação: retorna ROC degenerada
        return [{"threshold": t / (n_bins - 1), "tpr": None, "fpr": None,
                 "youden_j": None, "n_alto": sum(1 for s, _ in rotulos if s >= t / (n_bins - 1))}
                for t in range(n_bins)]
    out = []
    for i in range(n_bins):
        thr = i / (n_bins - 1)
        tp = sum(1 for s, y in rotulos if s >= thr and y == 1)
        fp = sum(1 for s, y in rotulos if s >= thr and y == 0)
        fn = pos - tp
        tn = neg - fp
        tpr = tp / pos if pos else 0
        fpr = fp / neg if neg else 0
        out.append({
            "threshold": round(thr, 3),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "tpr": round(tpr, 3), "fpr": round(fpr, 3),
            "youden_j": round(tpr - fpr, 3),
            "n_alto": tp + fp,
        })
    return out


def main() -> int:
    probes = carregar_probes(PROBE_PATH)
    brier_legacy = carregar_brier_legacy(BACKTEST_PATH)

    print(f"Probes carregados: {len(probes)}")
    print(f"Eventos com brier conhecido: {len(brier_legacy)}")

    rotulos = construir_rotulos(probes, brier_legacy)
    print(f"Eventos rotuláveis (probe ∩ brier): {len(rotulos)}")

    roc = curva_roc(rotulos)
    melhor_j = None
    if roc and roc[0]["youden_j"] is not None:
        melhor_j = max(roc, key=lambda r: r["youden_j"])

    # Classificação final dos 100 (ou quantos houver no probe)
    from engine.outcome_probe import classificar_leakage, LEAKAGE_THRESHOLD_DEFAULT
    classificacao = []
    n_alto = n_medio = n_baixo = 0
    for r in probes:
        cls = classificar_leakage(r["p_outcome_mean"])
        classificacao.append({
            "id": r["id"], "dataset": r["dataset"],
            "p_outcome_mean": r["p_outcome_mean"],
            "leakage": cls,
        })
        if cls == "alto": n_alto += 1
        elif cls == "medio": n_medio += 1
        else: n_baixo += 1

    # Renderizar markdown
    md = []
    md.append("# Calibração do threshold outcome_probe — Onda 164\n")
    md.append(f"Threshold congelado em `outcome_probe.py`: **{LEAKAGE_THRESHOLD_DEFAULT}**\n")
    md.append("## Dados\n")
    md.append(f"- Probes carregados: {len(probes)}")
    md.append(f"- Eventos com brier real conhecido: {len(brier_legacy)}")
    md.append(f"- Eventos rotuláveis (intersecção): {len(rotulos)}\n")

    md.append("## Curva ROC (threshold vs TPR/FPR)\n")
    md.append("| threshold | TP | FP | FN | TN | TPR | FPR | Youden J | n_alto |")
    md.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in roc:
        md.append(f"| {r['threshold']} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} "
                  f"| {r['tpr']} | {r['fpr']} | {r['youden_j']} | {r['n_alto']} |")

    md.append("")
    if melhor_j:
        md.append(f"## Threshold ótimo (Youden's J)\n")
        md.append(f"- Threshold: **{melhor_j['threshold']}**")
        md.append(f"- TPR: {melhor_j['tpr']}, FPR: {melhor_j['fpr']}, J: {melhor_j['youden_j']}")
        delta = abs(melhor_j['threshold'] - LEAKAGE_THRESHOLD_DEFAULT)
        if delta <= 0.05:
            md.append(f"- **Decisão**: 0.65 mantido (ótimo Youden está a {delta:.2f} de distância).")
        else:
            md.append(f"- **Atenção**: ótimo Youden ({melhor_j['threshold']}) difere do default "
                      f"em {delta:.2f}. Considerar ajuste ANTES de iniciar campanha.")
    else:
        md.append("## Threshold ótimo: indeterminado (rotulagem insuficiente)\n")

    md.append("\n## Classificação dos 100 legacy\n")
    md.append(f"- Alto leakage (>= 0.65): **{n_alto}**")
    md.append(f"- Médio leakage (0.55–0.65): **{n_medio}**")
    md.append(f"- Baixo leakage (< 0.55): **{n_baixo}**\n")

    # Top 10 mais suspeitos
    classificacao.sort(key=lambda x: x["p_outcome_mean"], reverse=True)
    md.append("### Top 10 mais suspeitos\n")
    md.append("| id | dataset | p_outcome_mean | leakage |")
    md.append("|---|---|---:|---|")
    for c in classificacao[:10]:
        md.append(f"| {c['id']} | {c['dataset']} | {c['p_outcome_mean']:.3f} | {c['leakage']} |")

    md.append("\n## Decisão metodológica\n")
    md.append("Threshold mantido em 0.65 (default da Onda 163) salvo veto explícito acima.")
    md.append("Eventos classificados 'alto' ficam fora do holdout. Vão para `reserve` ou são re-curados.\n")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\nRelatório salvo: {OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
