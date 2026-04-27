"""Onda 163: roda outcome_probe nos 100 eventos legacy de data/backtest/*.csv.

Saída: data/n100/probe_legacy_results.jsonl (append-only).
Custo estimado: 100 eventos × (1 paráfrase + 3 probes) = ~400 chamadas LLM.

Uso:
    python scripts/rodar_probe_legacy.py [--limit N] [--dry-run]
    --limit N: testar com primeiros N eventos
    --dry-run: não chama LLM, salva resultado mockado para teste de pipeline
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.eventos_v1 import from_csv_legado
from engine.outcome_probe import probar_evento, classificar_leakage


REPO = Path(__file__).resolve().parents[1]
DIR_BACKTEST = REPO / "data" / "backtest"
OUT = REPO / "data" / "n100" / "probe_legacy_results.jsonl"


def _mock_llm(mensagens, modelo="rapido", max_tokens=300,
              temperatura=0.8, system_prompt="", bypass_step_cap=False):
    """Mock determinístico para --dry-run."""
    content = mensagens[0]["content"]
    if "Reescreva" in content or "variações" in content:
        return "1. Variação A\n2. Variação B\n3. Variação C"
    return "PROBABILIDADE FINAL: 0.55"


def _resolver_chamar_llm(dry_run: bool):
    if dry_run:
        return _mock_llm
    from engine.ia_client import chamar_llm
    return chamar_llm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--modelo", default="rapido")
    ap.add_argument("--n-parafrases", type=int, default=3)
    args = ap.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    chamar_llm = _resolver_chamar_llm(args.dry_run)

    csvs = sorted(DIR_BACKTEST.glob("*.csv"))
    if not csvs:
        print(f"Nenhum CSV em {DIR_BACKTEST}", file=sys.stderr)
        return 1

    eventos: list = []
    for csv in csvs:
        eventos.extend(from_csv_legado(csv))
    if args.limit:
        eventos = eventos[: args.limit]

    print(f"Probando {len(eventos)} eventos com modelo={args.modelo} "
          f"dry_run={args.dry_run}")

    n_alto = n_medio = n_baixo = n_falhou = 0
    t0 = time.time()
    with OUT.open("w", encoding="utf-8") as f:
        for i, ev in enumerate(eventos, 1):
            r = probar_evento(
                ev, modelo=args.modelo,
                n_parafrases=args.n_parafrases,
                chamar_llm=chamar_llm,
            )
            classificacao = classificar_leakage(r.p_outcome_mean)
            row = {
                "id": ev.id,
                "dataset": ev.dataset,
                "outcome_binario": ev.outcome_binario,
                "p_outcome_mean": r.p_outcome_mean,
                "p_outcome_std": r.p_outcome_std,
                "n_validas": r.n_validas,
                "leakage_classificado": classificacao,
                "is_leakage_alto": r.is_leakage(),
                "erro": r.erro,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if r.n_validas == 0:
                n_falhou += 1
            elif classificacao == "alto":
                n_alto += 1
            elif classificacao == "medio":
                n_medio += 1
            else:
                n_baixo += 1
            if i % 10 == 0:
                print(f"  {i}/{len(eventos)} ({time.time()-t0:.1f}s) "
                      f"alto={n_alto} medio={n_medio} baixo={n_baixo} falhou={n_falhou}")

    print(f"\nResumo: alto={n_alto} medio={n_medio} baixo={n_baixo} falhou={n_falhou}")
    print(f"Salvo em {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
