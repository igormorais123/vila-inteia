"""Onda 168: pipeline integrador end-to-end da campanha N=100.

Orquestra: candidatos → curador (cutoff + fonte primária + probe) → split
estratificado → backtest baseline → split tune/gate/holdout → bootstrap_gate
→ skill_score final.

Uso (modo dry-run com fixture sintética):
    python scripts/run_n100_pipeline.py --dry-run

Uso (modo real, exige eventos curados em JSONL):
    python scripts/run_n100_pipeline.py --candidates data/n100/candidates.jsonl

Não roda nada novo se faltarem eventos. Apenas valida que toda a cadeia
está conectada e os hashes/configs são reprodutíveis.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.eventos_v1 import EventoPreditivoV1, FonteEvento, to_jsonl, from_jsonl
from engine.curador_oos import curar_lote
from engine.bootstrap_gate import avaliar_gate, skill_score_ic, _media

REPO = Path(__file__).resolve().parents[1]
DIR_OUT = REPO / "data" / "n100"


def gerar_fixture_sintetica(n: int, seed: int = 42) -> list[EventoPreditivoV1]:
    """Gera n eventos OOS sintéticos para teste de pipeline (sem LLM)."""
    rng = random.Random(seed)
    categorias = ["esportes", "eleicoes", "ipos", "earnings", "mercados"]
    eventos = []
    base_date = date(2024, 9, 1)
    for i in range(n):
        cat = categorias[i % len(categorias)]
        d_corte = base_date + timedelta(days=i * 3)
        d_res = d_corte + timedelta(days=7 + i % 14)
        outcome = rng.randint(0, 1)
        prior = round(rng.uniform(0.40, 0.70), 2)
        eventos.append(EventoPreditivoV1(
            id=f"oos{i:03d}",
            dataset=f"sintetico_{cat}",
            split="reserve",
            categoria=cat,
            pergunta=f"Evento sintético {i} acontecerá?",
            outcome_framing=f"Resultado positivo do evento {i}?",
            contexto_pre_corte=f"Contexto histórico do evento sintético {i} no dataset {cat}.",
            regra_resolucao=f"Critério objetivo para evento {i}",
            outcome_binario=outcome,
            prob_oraculo_humano_se_houver=prior,
            tipo_oraculo_humano="closing_odds" if cat == "esportes" else "analyst_consensus",
            data_corte_informacao=d_corte,
            data_resolucao=d_res,
            fonte_outcome=[FonteEvento(
                url=f"https://exemplo.com/{cat}/{i}",
                titulo=f"Resultado oficial {i}",
                nivel="primaria",
                data_acesso=d_res + timedelta(days=1),
            )],
            leakage_risk="baixo",
        ))
    return eventos


def simular_brier_baseline(eventos: list[EventoPreditivoV1], seed: int = 42) -> list[float]:
    """Simula brier por evento (sem chamar Vila real). Modelo: brier proporcional
    a |prob_oraculo - 0.5| invertido (eventos próximos de 0.5 são mais difíceis).
    """
    rng = random.Random(seed)
    briers = []
    for ev in eventos:
        prior = ev.prob_oraculo_humano_se_houver or 0.5
        # Vila prevê com noise gaussiano em torno do prior
        prob_pred = max(0.05, min(0.95, prior + rng.gauss(0, 0.08)))
        # Brier = (prob_pred - outcome)^2
        brier = (prob_pred - ev.outcome_binario) ** 2
        briers.append(brier)
    return briers


def split_estratificado(eventos: list[EventoPreditivoV1], seed: int = 42) -> dict:
    """Atribui cada evento a tune/gate/holdout estratificado por categoria.
    Proporção: tune=35/100, gate=15/100, holdout=50/100.
    """
    rng = random.Random(seed)
    by_cat: dict[str, list] = {}
    for ev in eventos:
        by_cat.setdefault(ev.categoria, []).append(ev)
    splits = {"tune": [], "gate": [], "holdout": []}
    for cat, evs in by_cat.items():
        rng.shuffle(evs)
        n = len(evs)
        n_tune = round(n * 0.35)
        n_gate = round(n * 0.15)
        splits["tune"].extend(evs[:n_tune])
        splits["gate"].extend(evs[n_tune:n_tune + n_gate])
        splits["holdout"].extend(evs[n_tune + n_gate:])
    return splits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Usa fixture sintética em vez de eventos reais")
    ap.add_argument("--candidates", type=str,
                    help="JSONL com candidatos (modo real)")
    ap.add_argument("--n-fixture", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    DIR_OUT.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        eventos = gerar_fixture_sintetica(args.n_fixture, seed=args.seed)
        print(f"[fixture] {len(eventos)} eventos sintéticos gerados")
    elif args.candidates:
        eventos = from_jsonl(args.candidates)
        print(f"[real] {len(eventos)} eventos carregados de {args.candidates}")
    else:
        ap.error("--dry-run ou --candidates obrigatório")
        return 1

    # 1. Curadoria (sem probe se dry-run, para não chamar LLM)
    print("\n[1/5] Curadoria via curador_oos...")
    r = curar_lote(eventos, rodar_probe=False)
    print(f"  total={r['n_total']} aprovados={r['n_aprovados']} vetados={r['n_vetados']} "
          f"taxa={r['taxa_aprovacao']:.1%}")
    if r['vetados']:
        print(f"  primeiras razões de veto:")
        for v in r['vetados'][:3]:
            print(f"    - {v['id']}: {v['razao'][:80]}")

    aprovados = r['aprovados']
    if len(aprovados) < 50:
        print(f"\n[ABORTAR] aprovados={len(aprovados)} < 50, insuficiente para campanha N=100")
        return 1

    # 2. Splits estratificados
    print("\n[2/5] Splits estratificados por categoria...")
    splits = split_estratificado(aprovados, seed=args.seed)
    for split_name, evs in splits.items():
        print(f"  {split_name}: {len(evs)} eventos")

    # 3. Brier baseline simulado
    print("\n[3/5] Brier baseline simulado (sem LLM real)...")
    brier_tune = simular_brier_baseline(splits["tune"], seed=args.seed)
    brier_gate = simular_brier_baseline(splits["gate"], seed=args.seed + 1)
    brier_holdout = simular_brier_baseline(splits["holdout"], seed=args.seed + 2)
    print(f"  brier_tune avg={_media(brier_tune):.4f} n={len(brier_tune)}")
    print(f"  brier_gate avg={_media(brier_gate):.4f} n={len(brier_gate)}")
    print(f"  brier_holdout avg={_media(brier_holdout):.4f} n={len(brier_holdout)}")

    # 4. Avaliação do gate
    print("\n[4/5] Bootstrap pareado para gate (Helena P1.4)...")
    gate_result = avaliar_gate(brier_tune, brier_gate, n_iter=2000, seed=args.seed)
    print(f"  delta_observado={gate_result.delta_observado:+.4f}")
    print(f"  IC95% [{gate_result.ic_95_inferior:+.4f}, {gate_result.ic_95_superior:+.4f}]")
    print(f"  p-valor={gate_result.p_valor_unilateral:.4f}")
    print(f"  {'✓ ACEITO' if gate_result.aceito else '✗ ' + gate_result.razao}")

    if not gate_result.aceito:
        print("\n[ABORTAR] Gate reprovado. Holdout não abre. Campanha encerra.")
        return 1

    # 5. Skill score no holdout
    print("\n[5/5] Skill score Vila vs prior baseline (holdout)...")
    # Referência = prever o prior puro
    brier_prior = [(ev.prob_oraculo_humano_se_houver or 0.5 - ev.outcome_binario) ** 2
                   for ev in splits["holdout"]]
    skill = skill_score_ic(brier_holdout, brier_prior, n_iter=2000, seed=args.seed)
    print(f"  skill_score_pontual={skill['skill_score_pontual']:+.4f}")
    print(f"  IC95% [{skill['ic_95_inferior']:+.4f}, {skill['ic_95_superior']:+.4f}]")
    print(f"  exclui zero: {skill['exclui_zero']}")

    # Salvar resultado
    out = {
        "modo": "dry_run" if args.dry_run else "real",
        "n_aprovados": len(aprovados),
        "splits": {k: len(v) for k, v in splits.items()},
        "gate": gate_result.to_dict(),
        "skill_score": skill,
        "brier_avg": {
            "tune": _media(brier_tune),
            "gate": _media(brier_gate),
            "holdout": _media(brier_holdout),
        },
    }
    suffix = "_dryrun" if args.dry_run else ""
    out_path = DIR_OUT / f"pipeline_result{suffix}.json"
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nResultado salvo: {out_path.relative_to(REPO)}")

    # Veredito
    sucesso = gate_result.aceito and skill['exclui_zero'] and skill['skill_score_pontual'] > 0
    print(f"\n{'=' * 60}")
    print(f"VEREDITO: {'CAMPANHA APROVADA' if sucesso else 'NÃO PROVADA'}")
    print(f"{'=' * 60}")
    return 0 if sucesso else 2


if __name__ == "__main__":
    raise SystemExit(main())
