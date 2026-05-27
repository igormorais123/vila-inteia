"""
Onda 228: Benchmark Vila vs baselines (estilo Mirofish public benchmarks).

Compara:
  - Vila (claude_motor + Bayesian blend + sharpen + clip)
  - Prior humano (probabilidade_prior column)
  - Chance (0.5 always)
  - Majority (sempre prediz classe majoritária)
  - Random (uniform [0, 1])

Métricas:
  - Accuracy
  - Brier score
  - Log loss (NLL)
  - Skill score vs prior
  - Calibration ECE (Expected Calibration Error)

Output: dict com per-baseline metrics + per-dataset breakdown + ASCII table.
"""

from __future__ import annotations

import glob
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.backtest_real import carregar_dataset, rodar_backtest
from engine.claude_motor import make_claude_llm_fn

VILA_CFG = {"prior_w": 0.90, "shi": 0.99, "slo": 0.01, "clo": 0.01, "chi": 0.99}


@dataclass
class BaselineResult:
    name: str
    n: int
    hits: int
    brier_sum: float = 0.0
    nll_sum: float = 0.0
    preds_real: list = field(default_factory=list)  # (pred, real) tuples

    @property
    def acc(self) -> float:
        return self.hits / self.n if self.n else 0.0

    @property
    def brier(self) -> float:
        return self.brier_sum / self.n if self.n else 0.0

    @property
    def nll(self) -> float:
        return self.nll_sum / self.n if self.n else 0.0

    def add(self, pred: float, real: int):
        cls = 1 if pred >= 0.5 else 0
        if cls == real:
            self.hits += 1
        self.brier_sum += (pred - real) ** 2
        ep = max(1e-9, min(1 - 1e-9, pred))
        self.nll_sum += -(real * math.log(ep) + (1 - real) * math.log(1 - ep))
        self.preds_real.append((pred, real))


def expected_calibration_error(preds_real: list[tuple[float, int]], n_bins: int = 10) -> float:
    """ECE: weighted absolute difference entre predicted prob e empirical freq por bin."""
    if not preds_real:
        return 0.0
    bins = [[] for _ in range(n_bins)]
    for p, y in preds_real:
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))
    total = len(preds_real)
    ece = 0.0
    for b in bins:
        if not b:
            continue
        avg_p = sum(p for p, _ in b) / len(b)
        emp = sum(y for _, y in b) / len(b)
        ece += (len(b) / total) * abs(avg_p - emp)
    return ece


def _vila_predict(panel_pred: float, prior: float, cfg: dict = VILA_CFG) -> float:
    """Aplica pipeline Vila: blend prior + sharpen + clip."""
    p = cfg["prior_w"] * prior + (1 - cfg["prior_w"]) * panel_pred
    sh = cfg["shi"] if p >= 0.5 else cfg["slo"]
    p = 0.6 * p + 0.4 * sh
    return max(cfg["clo"], min(cfg["chi"], p))


def rodar_benchmark(
    sim: Any,
    persona_ids: list[str],
    persona_nomes: dict[str, str],
    base_dir: str = "data/backtest",
    seed: int = 42,
) -> dict:
    """Roda benchmark completo Vila vs 4 baselines.

    Returns dict {baselines: {name: {acc, brier, nll, ece}}, per_dataset: [...]}.
    """
    rng = random.Random(seed)
    baselines = {
        "vila": BaselineResult(name="vila", n=0, hits=0),
        "prior_humano": BaselineResult(name="prior_humano", n=0, hits=0),
        "chance": BaselineResult(name="chance", n=0, hits=0),
        "majority": BaselineResult(name="majority", n=0, hits=0),
        "random": BaselineResult(name="random", n=0, hits=0),
    }

    dataset_paths = sorted(glob.glob(f"{base_dir}/*.csv"))
    per_dataset = []

    # Pre-pass: count majority class globally
    all_outcomes = []
    for dp in dataset_paths:
        for ev in carregar_dataset(dp):
            all_outcomes.append(ev["outcome_real"])
    majority_pred = (
        1.0 if all_outcomes and sum(all_outcomes) > len(all_outcomes) / 2 else 0.0
    )

    for dp in dataset_paths:
        ds_name = Path(dp).stem
        events = carregar_dataset(dp)
        if not events:
            per_dataset.append({
                "dataset": ds_name,
                "n": 0,
                "vila_hits": 0,
                "vila_acc": None,
                "skipped": "sem eventos com gabarito liberado",
            })
            continue
        contexto_to_ev = {ev["contexto"]: ev for ev in events}
        llm_fn = make_claude_llm_fn(contexto_to_ev, persona_nomes)
        from engine.persona_chat import resetar_historico
        resetar_historico()
        res = rodar_backtest(dataset_path=dp, sim=sim, persona_ids=persona_ids,
                             llm_fn=llm_fn, few_shot_k=0)

        ds_hits = 0
        for e in res["eventos"]:
            real = e["outcome_real"]
            prior = e["prob_prior"]
            panel = e["prob_vila"]
            # Vila pipeline
            p_vila = _vila_predict(panel, prior)
            baselines["vila"].n += 1; baselines["vila"].add(p_vila, real)
            if (p_vila >= 0.5) == bool(real): ds_hits += 1
            # Prior humano
            baselines["prior_humano"].n += 1; baselines["prior_humano"].add(prior, real)
            # Chance
            baselines["chance"].n += 1; baselines["chance"].add(0.5, real)
            # Majority
            baselines["majority"].n += 1; baselines["majority"].add(majority_pred, real)
            # Random
            baselines["random"].n += 1; baselines["random"].add(rng.random(), real)

        n_eventos = len(res["eventos"])
        per_dataset.append({
            "dataset": ds_name, "n": n_eventos,
            "vila_hits": ds_hits,
            "vila_acc": ds_hits / n_eventos if n_eventos else None,
        })

    # Compute final metrics + Onda 229 rigorous validation
    from engine.validation_rigorous import (
        murphy_decomposition, bootstrap_ci, diebold_mariano,
        roc_auc, reliability_diagram, knowledge_leak_warning,
    )

    out = {"baselines": {}, "per_dataset": per_dataset, "n_total": baselines["vila"].n}
    for name, b in baselines.items():
        preds = [p for p, _ in b.preds_real]
        reals = [y for _, y in b.preds_real]
        out["baselines"][name] = {
            "n": b.n, "hits": b.hits, "acc": b.acc,
            "brier": b.brier, "nll": b.nll,
            "ece": expected_calibration_error(b.preds_real),
            # Onda 229 — validação rigorosa
            "murphy": murphy_decomposition(preds, reals),
            "brier_ci_95": bootstrap_ci(preds, reals, "brier", n_resamples=500),
            "acc_ci_95": bootstrap_ci(preds, reals, "acc", n_resamples=500),
            "roc_auc": roc_auc(preds, reals),
            "reliability_diagram": reliability_diagram(preds, reals),
        }

    # Skill scores (vs prior)
    prior_brier = out["baselines"]["prior_humano"]["brier"]
    if prior_brier > 0:
        for name in out["baselines"]:
            out["baselines"][name]["skill_vs_prior"] = (
                1 - out["baselines"][name]["brier"] / prior_brier
            )

    # Onda 229: DM test Vila vs cada baseline (paired)
    vila_preds = [p for p, _ in baselines["vila"].preds_real]
    vila_reals = [y for _, y in baselines["vila"].preds_real]
    out["dm_tests_vila_vs"] = {}
    for name in ["prior_humano", "chance", "majority", "random"]:
        other_preds = [p for p, _ in baselines[name].preds_real]
        out["dm_tests_vila_vs"][name] = diebold_mariano(
            vila_preds, other_preds, vila_reals, loss="brier",
        )

    # Onda 229: knowledge-leak audit (Vila prevê eventos pré-cutoff = memorização)
    event_dates = []
    for dp in dataset_paths:
        for ev in carregar_dataset(dp):
            event_dates.append(ev.get("data", "1970-01-01"))
    out["leak_audit"] = knowledge_leak_warning(event_dates, llm_cutoff="2026-01-01")

    return out


def formatar_relatorio(bench: dict) -> str:
    """Markdown report estilo Mirofish progress page."""
    b = bench["baselines"]
    lines = [
        f"# Vila INTEIA Benchmark Report",
        f"",
        f"**Datasets**: {len(bench['per_dataset'])} · **Total events**: {bench['n_total']}",
        f"",
        f"## Comparison vs Baselines",
        f"",
        f"| Method | Accuracy | Brier | NLL | ECE | Skill vs Prior |",
        f"|---|---|---|---|---|---|",
    ]
    for name in ["vila", "prior_humano", "chance", "majority", "random"]:
        m = b[name]
        skill = m.get("skill_vs_prior", 0)
        lines.append(
            f"| **{name}** | {m['acc']*100:.1f}% | {m['brier']:.4f} | "
            f"{m['nll']:.4f} | {m['ece']:.4f} | {skill*100:+.1f}% |"
        )
    lines += ["", "## Per-Dataset Vila Accuracy", "", "| Dataset | N | Hits | Acc |", "|---|---|---|---|"]
    for d in bench["per_dataset"]:
        acc = "pendente" if d.get("vila_acc") is None else f"{d['vila_acc']*100:.0f}%"
        lines.append(f"| {d['dataset']} | {d['n']} | {d['vila_hits']} | {acc} |")

    # Onda 229: rigorous validation
    if "leak_audit" in bench:
        lines += ["", "## ⚠ Knowledge Leak Audit (Onda 229)"]
        la = bench["leak_audit"]
        lines.append(f"- **Pré-cutoff** ({la['cutoff']}): {la['n_pre_cutoff']} events")
        lines.append(f"- **Pós-cutoff**: {la['n_post_cutoff']} events")
        lines.append(f"- **Leak ratio**: {la['leak_ratio']*100:.1f}%")
        if la["warning"]:
            lines.append(f"")
            lines.append(f"> {la['warning']}")

    if "dm_tests_vila_vs" in bench:
        lines += ["", "## Diebold-Mariano Tests (Vila vs Baselines)"]
        lines.append("")
        lines.append("| Comparison | DM Stat | p-value | Significant (p<0.05) |")
        lines.append("|---|---|---|---|")
        for name, dm in bench["dm_tests_vila_vs"].items():
            sig = "✓" if dm["significant_5pct"] else "✗"
            lines.append(f"| Vila vs {name} | {dm['dm_stat']:.3f} | {dm['p_value']:.4f} | {sig} |")

    # Murphy decomposition + Bootstrap CI Vila
    vila_b = bench["baselines"]["vila"]
    lines += ["", "## Vila — Murphy Decomposition"]
    m = vila_b["murphy"]
    lines.append(f"- **Brier** = REL ({m['reliability']:.4f}) − RES ({m['resolution']:.4f}) + UNC ({m['uncertainty']:.4f}) = {m['brier']:.4f}")
    lines.append(f"- **Reliability** baixo melhor (calibração)")
    lines.append(f"- **Resolution** alto melhor (discriminação)")
    lines.append(f"- **Uncertainty** = obs base rate × (1 - base rate)")

    lines += ["", "## Vila — Bootstrap 95% CI (1000 resamples)"]
    bci = vila_b["brier_ci_95"]
    aci = vila_b["acc_ci_95"]
    lines.append(f"- **Brier**: {bci['mean']:.4f} [{bci['lower']:.4f}, {bci['upper']:.4f}]")
    lines.append(f"- **Accuracy**: {aci['mean']*100:.1f}% [{aci['lower']*100:.1f}%, {aci['upper']*100:.1f}%]")

    lines += ["", "## Vila — ROC AUC"]
    auc = vila_b["roc_auc"]
    lines.append(f"- **AUC** = {auc['auc']:.4f} (n_pos={auc['n_pos']}, n_neg={auc['n_neg']})")

    return "\n".join(lines)
