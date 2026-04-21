#!/usr/bin/env python3
"""
Onda 92: roda backtest em eventos históricos reais usando
engine.backtest_real + persona chat LLM direto (bypass sim).

Uso:
  python scripts/rodar_backtest_real.py
  python scripts/rodar_backtest_real.py --ds impeachment_dilma_2016 --max 5
  python scripts/rodar_backtest_real.py --out ~/Downloads/backtest_result.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _carregar_env():
    env_file = Path.home() / ".vila_env"
    if env_file.exists():
        for linha in env_file.read_text().splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    os.environ.setdefault("GROQ_MODEL_RAPIDO", "openai/gpt-oss-120b")
    os.environ.setdefault("GROQ_MODEL_CHAIN", "llama-3.3-70b-versatile,llama-3.1-8b-instant,meta-llama/llama-4-scout-17b-16e-instruct")
    os.environ["OMNIROUTE_API_KEY"] = ""
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["CLAUDE_API_KEY"] = ""


class _SimMinima:
    """Sim mínima com personas preenchidas do banco-consultores."""
    def __init__(self, personas_ids: list[str]):
        import json as _j
        banco = _j.load(open("data/banco-consultores-lendarios.json"))
        from engine.persona import Persona
        self.personas = {}
        for p in banco:
            if p["id"] in personas_ids:
                self.personas[p["id"]] = Persona(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ds", default=None, help="só 1 dataset (sem extensão)")
    ap.add_argument("--max", type=int, default=None, help="max eventos por dataset")
    ap.add_argument("--personas", default="CL001,CL002,CL007,CL022",
                    help="CSV de persona IDs (Musk/Jobs/Buffett/Gates default)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--base", default="data/backtest")
    ap.add_argument("--sleep-eventos", type=float, default=6.0,
                    help="segundos entre eventos (respeita TPM)")
    ap.add_argument("--sleep-datasets", type=float, default=15.0)
    args = ap.parse_args()

    _carregar_env()

    from engine.backtest_real import rodar_backtest, rodar_backtest_todos

    ids = [p.strip() for p in args.personas.split(",") if p.strip()]
    print(f"# Backtest real — panel: {ids}")
    print(f"# max eventos/dataset: {args.max}")
    print()

    sim = _SimMinima(ids)
    print(f"Sim loaded: {len(sim.personas)} personas")
    if len(sim.personas) < len(ids):
        print(f"  AVISO: {set(ids) - set(sim.personas.keys())} não encontradas no banco")
    print()

    if args.ds:
        path = Path(args.base) / f"{args.ds}.csv"
        if not path.exists():
            print(f"dataset {path} não existe")
            sys.exit(1)
        r = rodar_backtest(path, sim, persona_ids=ids, max_eventos=args.max,
                            sleep_entre_eventos_s=args.sleep_eventos)
        _imprimir_resumo_ds(r)
        saida = {"agregado": None, "datasets": [r]}
    else:
        saida = rodar_backtest_todos(
            base_dir=args.base, sim=sim, persona_ids=ids,
            max_eventos_por_ds=args.max,
            sleep_entre_eventos_s=args.sleep_eventos,
            sleep_entre_datasets_s=args.sleep_datasets,
        )
        for ds in saida["datasets"]:
            _imprimir_resumo_ds(ds)
        print()
        print("=" * 60)
        print("AGREGADO")
        print("=" * 60)
        ag = saida.get("agregado", {})
        for k, v in ag.items():
            if isinstance(v, float):
                print(f"  {k:35s} {v:.4f}")
            else:
                print(f"  {k:35s} {v}")

    # Onda 93: aplicar Platt calibração ao agregado
    try:
        from engine.calibracao_platt import avaliar_calibracao
        probs_raw, ys = [], []
        for ds in saida.get("datasets", []):
            if "erro" in ds: continue
            for e in ds.get("eventos", []):
                if e.get("prob_vila") is not None:
                    probs_raw.append(e["prob_vila"])
                    ys.append(e["outcome_real"])
        if len(probs_raw) >= 5:
            cal = avaliar_calibracao(probs_raw, ys)
            print()
            print("=" * 60)
            print("CALIBRAÇÃO PLATT (Onda 93)")
            print("=" * 60)
            print(f"  n amostras             {cal['n']}")
            print(f"  platt (a, b)           ({cal['platt_a']:.3f}, {cal['platt_b']:.3f})")
            print(f"  Brier antes            {cal['brier_antes']:.4f}")
            print(f"  Brier depois           {cal['brier_depois']:.4f}   Δ {cal['brier_antes']-cal['brier_depois']:+.4f}")
            print(f"  Log-loss antes         {cal['log_loss_antes']:.4f}")
            print(f"  Log-loss depois        {cal['log_loss_depois']:.4f}   Δ {cal['log_loss_antes']-cal['log_loss_depois']:+.4f}")
            print(f"  ECE antes              {cal['ece_antes']:.4f}")
            print(f"  ECE depois             {cal['ece_depois']:.4f}   Δ {cal['ece_antes']-cal['ece_depois']:+.4f}")
            saida["calibracao_platt"] = {k: v for k, v in cal.items() if k != "probs_calibradas"}
    except Exception as e:
        print(f"\n(calibração Platt skip: {e})")

    if args.out:
        Path(args.out).write_text(json.dumps(saida, indent=2, ensure_ascii=False))
        print(f"\nJSON: {args.out}")


def _imprimir_resumo_ds(r: dict):
    name = Path(r.get("dataset", "?")).stem
    print(f"## {name}")
    if "erro" in r:
        print(f"  ERRO: {r['erro']}")
        return
    print(f"  n_eventos       {r['n_eventos']}")
    print(f"  n_respondidos   {r['n_respondidos']}")
    print(f"  accuracy_vila   {r['accuracy_vila']:.2%}")
    b_v = r.get("brier_vila_avg")
    b_p = r.get("brier_prior_avg")
    sk = r.get("skill_brier_vs_prior")
    print(f"  brier_vila      {b_v:.4f}" if b_v is not None else "  brier_vila      —")
    print(f"  brier_prior     {b_p:.4f}" if b_p is not None else "  brier_prior     —")
    print(f"  skill vs prior  {sk:+.4f}" if sk is not None else "  skill vs prior  —")
    # Per-evento
    for e in r.get("eventos", [])[:6]:
        mk = "✓" if e.get("acertou_vila") else "✗"
        pv = e.get("prob_vila")
        pv_s = f"{pv:.2f}" if pv is not None else "—"
        print(f"  {mk} {e['evento_id']:8s} real={e['outcome_real']} prior={e['prob_prior']:.2f} vila={pv_s} — {e['contexto'][:80]}")
    print()


if __name__ == "__main__":
    main()
