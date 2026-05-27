"""Guarda contra leakage no antigo teste LODO.

Este arquivo mantem o nome historico, mas nao afirma mais que uma tabela
hardcoded foi validada por leave-one-dataset-out. O objetivo agora e garantir
que o painel offline default nao usa `evento_id` para buscar o gabarito.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GROQ_API_KEY"] = ""
os.environ["CLAUDE_API_KEY"] = ""
os.environ["OMNIROUTE_URL"] = ""

from engine.backtest_real import extrair_probabilidade
from engine.claude_motor import MY_PREDS_BASE, make_claude_llm_fn


ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_lodo_cv_leakage_guard ===")

ctx = "Americanas teste contexto unico para leakage guard"
ev = {
    "evento_id": "amer01",       # legado tem 0.95 para este id
    "contexto": ctx,
    "outcome_framing": "O evento sera aprovado?",
    "probabilidade_prior": 0.20,
    "outcome_real": 1,
}
nomes = {"CL002": "Steve Jobs"}

print("\n[1] default ignora MY_PREDS_BASE mesmo quando id existe")
fn = make_claude_llm_fn({ctx: ev}, nomes, preds=MY_PREDS_BASE)
out = fn([{"role": "user", "content": f"{ctx} analise"}], system_prompt="Você é Steve Jobs.")
p_default = extrair_probabilidade(out)
check(p_default is not None, f"prob extraida ({out!r})")
check(abs(p_default - MY_PREDS_BASE["amer01"]) > 0.20,
      f"default nao replica lookup legado (p={p_default}, legado={MY_PREDS_BASE['amer01']})")

print("\n[2] mudar outcome_real nao muda predicao")
ev2 = dict(ev)
ev2["outcome_real"] = 0
fn2 = make_claude_llm_fn({ctx: ev2}, nomes, preds=MY_PREDS_BASE)
out2 = fn2([{"role": "user", "content": f"{ctx} analise"}], system_prompt="Você é Steve Jobs.")
p2 = extrair_probabilidade(out2)
check(p2 == p_default, f"outcome_real blindado (p1={p_default}, p2={p2})")

print("\n[3] lookup legado continua opt-in, nao default")
legacy = make_claude_llm_fn(
    {ctx: ev}, nomes, preds=MY_PREDS_BASE, allow_event_id_lookup=True,
)
legacy_out = legacy([{"role": "user", "content": f"{ctx} analise"}], system_prompt="Você é Steve Jobs.")
p_legacy = extrair_probabilidade(legacy_out)
check(p_legacy is not None and p_legacy > 0.85,
      f"modo legado explicito reproduz tabela ({legacy_out!r})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
