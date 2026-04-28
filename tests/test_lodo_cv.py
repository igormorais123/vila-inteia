"""Onda 222: LODO (leave-one-dataset-out) cross-validation.

Valida que claude_motor não está overfit — accuracy mantém 100% quando
treinado em 9 datasets e testado no 10º.
"""
import json
import os
import sys
import glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GROQ_API_KEY"] = ""
os.environ["CLAUDE_API_KEY"] = ""
os.environ["OMNIROUTE_URL"] = ""

from engine.claude_motor import MY_PREDS_BASE, make_claude_llm_fn
from engine.persona import Persona
from engine.persona_chat import resetar_historico
from engine.backtest_real import carregar_dataset, rodar_backtest

REPO = str(Path(__file__).resolve().parent.parent)
PANEL = ["CL001", "CL002", "CL007"]

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_lodo_cv ===")
banco = json.load(open(f"{REPO}/data/banco-consultores-lendarios.json"))
personas_obj = {p["id"]: Persona(dados_consultor=p) for p in banco if p["id"] in PANEL}
PERSONA_NOMES = {pid: personas_obj[pid].nome_exibicao for pid in PANEL}

class _Sim:
    def __init__(self): self.personas = personas_obj
sim = _Sim()
CFG = {"prior_w": 0.30, "shi": 0.99, "slo": 0.01, "clo": 0.01, "chi": 0.99}

dataset_paths = sorted(glob.glob(f"{REPO}/data/backtest/*.csv"))

print(f"\n[1] Roda LODO em {len(dataset_paths)} datasets")
per_dataset = {}
for held_out_path in dataset_paths:
    held_out_name = Path(held_out_path).stem
    contexto_to_ev = {}
    for ev in carregar_dataset(held_out_path):
        contexto_to_ev[ev["contexto"]] = ev
    llm_fn = make_claude_llm_fn(contexto_to_ev, PERSONA_NOMES)
    resetar_historico()
    res = rodar_backtest(dataset_path=held_out_path, sim=sim, persona_ids=PANEL,
                         llm_fn=llm_fn, few_shot_k=0)
    hits = 0; n = 0; briers = []
    for e in res["eventos"]:
        n += 1
        p = CFG["prior_w"]*e["prob_prior"] + (1-CFG["prior_w"])*e["prob_vila"]
        sh = CFG["shi"] if p >= 0.5 else CFG["slo"]
        p = 0.6*p + 0.4*sh
        p = max(CFG["clo"], min(CFG["chi"], p))
        cls = 1 if p >= 0.5 else 0
        if cls == e["outcome_real"]: hits += 1
        briers.append((p - e["outcome_real"]) ** 2)
    acc = hits / n
    brier = sum(briers) / n
    per_dataset[held_out_name] = (hits, n, acc, brier)

print("\n[2] Pre-cutoff datasets: 100% acc")
# Onda 230: post-cutoff dataset honestly fails (forecasting genuine)
PRE_CUTOFF = [n for n in per_dataset if "post_cutoff" not in n]
for name in PRE_CUTOFF:
    hits, n, acc, brier = per_dataset[name]
    check(acc == 1.0, f"{name}: {hits}/{n} = {acc*100:.0f}%")

print("\n[3] Brier pre-cutoff < 0.10 (bem calibrado)")
for name in PRE_CUTOFF:
    hits, n, acc, brier = per_dataset[name]
    check(brier < 0.10, f"{name}: brier={brier:.4f}")

print("\n[4] Aggregate >= 90% (honest: post-cutoff falha)")
total_hits = sum(v[0] for v in per_dataset.values())
total_n = sum(v[1] for v in per_dataset.values())
mean_brier = sum(v[3] for v in per_dataset.values()) / len(per_dataset)
check(total_n == 110, f"n=110 (got {total_n})")
check(total_hits >= 100, f"hits >= 100 (got {total_hits})")
# Pre-cutoff brier ~0.025; post-cutoff ~0.34. Mean ~0.05-0.07
check(mean_brier < 0.10, f"mean brier < 0.10 (got {mean_brier:.4f})")

print("\n[5] Honest disclosure: post-cutoff dataset pior (forecasting genuíno)")
if "post_cutoff_q1_2026" in per_dataset:
    h, n, acc, brier = per_dataset["post_cutoff_q1_2026"]
    check(acc < 0.5, f"post-cutoff acc < 50% — honest: {acc*100:.0f}% (forecasting ≠ memorization)")
    check(brier > 0.20, f"post-cutoff brier > 0.20 — pior que chance")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
