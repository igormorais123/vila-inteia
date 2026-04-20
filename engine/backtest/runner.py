"""
Runner de backtest — compara predição da Vila vs outcome real.

Modo simples: usa prior + ajuste heurístico baseado em keywords do contexto.
Modo LLM (opcional): chama ia_client para estimar probabilidade.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse

from engine.backtest.dataset import carregar_dataset, DatasetBacktest
from engine.backtest.metricas import brier_score, log_loss, accuracy_binaria, calibration_curve


@dataclass
class ResultadoBacktest:
    dataset: str
    n_eventos: int
    brier: float
    log_loss: float
    accuracy: float
    calibration: list[dict]
    predicoes: list[dict]


def predizer_heuristico(contexto: str, prior: float) -> float:
    """
    Predição baseline via keyword heurística + ajuste Bayesiano leve.
    Substituir por chamada LLM em Onda 8 (calibração).
    """
    ctx = contexto.lower()
    boost = 0.0
    keywords_positivas = ["forte", "crescimento", "vitória", "apoio massivo",
                          "rejeitado concorrente", "campanha robusta"]
    keywords_negativas = ["crise", "escândalo", "rejeição", "perda", "fraco",
                          "contestação"]
    for k in keywords_positivas:
        if k in ctx:
            boost += 0.1
    for k in keywords_negativas:
        if k in ctx:
            boost -= 0.1
    prob = max(0.01, min(0.99, prior + boost))
    return prob


def rodar_backtest(
    dataset: str | DatasetBacktest,
    n_sims: int = 1,
    usar_llm: bool = False,
    base_dir: str = "data/backtest",
) -> ResultadoBacktest:
    """
    Roda predição sobre cada evento. Múltiplas sims para reduzir variância
    (média das probs).
    """
    if isinstance(dataset, str):
        ds = carregar_dataset(dataset, base_dir=base_dir)
    else:
        ds = dataset

    predicoes = []
    probs = []
    outcomes = []
    for evento in ds.eventos:
        probs_sim = []
        for _ in range(n_sims):
            if usar_llm:
                probs_sim.append(_predizer_llm(evento.contexto, evento.prior))
            else:
                probs_sim.append(predizer_heuristico(evento.contexto, evento.prior))
        prob_media = sum(probs_sim) / len(probs_sim)
        probs.append(prob_media)
        outcomes.append(evento.outcome_real)
        predicoes.append({
            "evento_id": evento.id,
            "prob_prevista": prob_media,
            "outcome_real": evento.outcome_real,
        })

    return ResultadoBacktest(
        dataset=ds.nome,
        n_eventos=ds.n,
        brier=brier_score(probs, outcomes),
        log_loss=log_loss(probs, outcomes),
        accuracy=accuracy_binaria(probs, outcomes),
        calibration=calibration_curve(probs, outcomes, bins=5),
        predicoes=predicoes,
    )


def _predizer_llm(contexto: str, prior: float) -> float:
    """Stub p/ Onda 8: integração real com ia_client + JSON structured output."""
    try:
        from engine.ia_client import chamar_llm_conversa
        resp = chamar_llm_conversa(
            system_prompt=(
                "Você estima probabilidades calibradas. Responda APENAS com "
                "um número em [0, 1] representando P(outcome=1)."
            ),
            user_prompt=f"Prior: {prior}. Contexto: {contexto}",
            modelo="rapido",
            max_tokens=10,
        )
        # Parse best-effort
        import re
        m = re.search(r"0\.\d+|1\.0|0|1", str(resp))
        if m:
            return max(0.01, min(0.99, float(m.group())))
    except Exception:
        pass
    return prior


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--n-sims", type=int, default=1)
    ap.add_argument("--usar-llm", action="store_true")
    args = ap.parse_args()
    r = rodar_backtest(args.dataset, n_sims=args.n_sims, usar_llm=args.usar_llm)
    print(f"Dataset: {r.dataset}  ({r.n_eventos} eventos)")
    print(f"  Brier score : {r.brier:.4f}  (0 = perfeito, 0.25 = coin)")
    print(f"  Log-loss    : {r.log_loss:.4f}")
    print(f"  Accuracy    : {r.accuracy:.2%}")
    print("  Calibração por bucket:")
    for c in r.calibration:
        print(f"    bin {c['bin']}: prob_média={c['prob_media']:.3f}  outcome_médio={c['outcome_medio']:.3f}  n={c['n']}")


if __name__ == "__main__":
    main()
