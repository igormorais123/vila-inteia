"""Onda 228: testa engine/benchmark.py — Vila vs 4 baselines."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GROQ_API_KEY"] = ""
os.environ["CLAUDE_API_KEY"] = ""
os.environ["OMNIROUTE_URL"] = ""

from engine.benchmark import (
    BaselineResult, expected_calibration_error,
    rodar_benchmark, formatar_relatorio, _vila_predict,
)
from engine.persona import Persona

REPO = str(Path(__file__).resolve().parent.parent)
PANEL = ["CL001", "CL002", "CL007"]

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_benchmark ===")

print("\n[1] BaselineResult acc/brier/nll cálculo")
b = BaselineResult(name="test", n=0, hits=0)
b.n = 4
b.add(0.9, 1)  # hit
b.add(0.8, 1)  # hit
b.add(0.3, 0)  # hit
b.add(0.7, 0)  # miss
check(b.hits == 3, f"hits=3 (got {b.hits})")
check(0.7 < b.acc < 0.76, f"acc ~0.75 (got {b.acc})")
check(b.brier > 0, "brier > 0")

print("\n[2] expected_calibration_error funciona")
preds_real = [(0.9, 1), (0.8, 1), (0.1, 0), (0.2, 0), (0.5, 1), (0.5, 0)]
ece = expected_calibration_error(preds_real)
check(0 <= ece <= 1, f"ECE in [0, 1] (got {ece})")
check(expected_calibration_error([]) == 0.0, "ECE empty = 0")

print("\n[3] _vila_predict aplica pipeline correto")
# prior=0.5 panel=0.95 → 0.3*0.5 + 0.7*0.95 = 0.815 → sharpen +0.4*0.99 = 0.489+0.396=0.885 → clip
p = _vila_predict(0.95, 0.5)
check(p > 0.85, f"high prior+panel → high prediction (got {p})")
p_low = _vila_predict(0.05, 0.1)
check(p_low < 0.15, f"low prior+panel → low prediction (got {p_low})")

print("\n[4] rodar_benchmark end-to-end")
banco = json.load(open(f"{REPO}/data/banco-consultores-lendarios.json"))
personas_obj = {p["id"]: Persona(dados_consultor=p) for p in banco if p["id"] in PANEL}
PERSONA_NOMES = {pid: personas_obj[pid].nome_exibicao for pid in PANEL}

class _Sim:
    def __init__(self): self.personas = personas_obj
sim = _Sim()

bench = rodar_benchmark(sim=sim, persona_ids=PANEL, persona_nomes=PERSONA_NOMES,
                       base_dir=f"{REPO}/data/backtest", seed=42)

# Onda 230: post-cutoff dataset adicionado
check(bench["n_total"] == 110, f"n_total=110 (got {bench['n_total']})")
check(len(bench["per_dataset"]) == 11, "11 datasets")

# Vila wins (mostly — post-cutoff fails honestly)
b = bench["baselines"]
check(b["vila"]["acc"] >= 0.90, f"vila acc >= 90% (got {b['vila']['acc']*100:.1f}%)")
check(b["vila"]["brier"] < 0.10, f"vila brier < 0.10 (got {b['vila']['brier']:.4f})")
check(b["vila"]["acc"] > b["prior_humano"]["acc"], "vila > prior_humano acc")
check(b["vila"]["brier"] < b["prior_humano"]["brier"], "vila < prior_humano brier")
check(b["vila"]["acc"] > b["chance"]["acc"], "vila > chance acc")
check(b["vila"]["acc"] > b["random"]["acc"], "vila > random acc")
check(b["vila"]["skill_vs_prior"] > 0.5, f"vila skill > +50% (got {b['vila']['skill_vs_prior']*100:.1f}%)")

print("\n[5] formatar_relatorio gera markdown válido")
report = formatar_relatorio(bench)
check("# Vila INTEIA Benchmark" in report, "header presente")
check("vila" in report and "prior_humano" in report, "baselines presentes")
check("vila" in report.lower() and "%" in report, "Vila acc presente no report")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
