"""Testa painel offline sem lookup de gabarito."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GROQ_API_KEY"] = ""
os.environ["CLAUDE_API_KEY"] = ""
os.environ["OMNIROUTE_URL"] = ""

from engine.claude_motor import (
    estimate_event_probability,
    persona_style,
    make_claude_llm_fn,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_claude_motor ===")
print("\n[1] estimate_event_probability usa prior/contexto, sem outcome")
ev = {
    "evento_id": "amer01",
    "contexto": "Evento com sinais mistos e incerteza",
    "outcome_framing": "Resultado sera aprovado?",
    "probabilidade_prior": 0.62,
    "outcome_real": 0,
}
p1 = estimate_event_probability(ev)
ev["outcome_real"] = 1
p2 = estimate_event_probability(ev)
check(abs(p1 - p2) < 1e-12, "outcome_real nao altera predicao")
check(0.05 <= p1 <= 0.95, f"probabilidade em faixa ({p1:.3f})")

print("\n[2] persona_style aplica bias correto")
# Musk sharpens
check(persona_style(0.7, "CL001") > 0.7, "Musk sharpens 0.7 up")
check(persona_style(0.3, "CL001") < 0.3, "Musk sharpens 0.3 down")
# Jobs anti-hype
check(persona_style(0.9, "CL002") < 0.9, "Jobs dims high (0.9)")
check(persona_style(0.1, "CL002") > 0.1, "Jobs raises low (0.1)")
check(persona_style(0.5, "CL002") == 0.5, "Jobs neutral (0.5)")
# Bezos anchor
check(0.4 < persona_style(0.9, "CL007") < 0.9, "Bezos pulls 0.9 toward 0.5")
check(0.1 < persona_style(0.1, "CL007") < 0.5, "Bezos pulls 0.1 toward 0.5")

print("\n[3] make_claude_llm_fn retorna função callable")
ctx = "Test contexto unique substring 35chars"
ctx_map = {ctx: {
    "evento_id": "amer01",
    "contexto": ctx,
    "outcome_framing": "Resultado sera aprovado?",
    "probabilidade_prior": 0.20,
    "outcome_real": 1,
}}
nomes = {"CL001": "Elon Musk"}
llm_fn = make_claude_llm_fn(ctx_map, nomes, preds={"test01": 0.8})
check(callable(llm_fn), "factory retorna callable")

print("\n[4] llm_fn retorna PROBABILIDADE FINAL: format")
out = llm_fn(
    [{"role": "user", "content": "Test contexto unique substring 35chars analise"}],
    system_prompt="Você é Elon Musk."
)
check("PROBABILIDADE FINAL:" in out, f"contém PROBABILIDADE FINAL ({out!r})")

print("\n[5] lookup por evento_id fica desligado por padrao")
check("95%" not in out and "98%" not in out,
      f"preds={{...}} nao controla output sem allow_event_id_lookup ({out!r})")

print("\n[6] modo legado exige opt-in explicito")
legacy_fn = make_claude_llm_fn(
    ctx_map, nomes, preds={"amer01": 0.80}, allow_event_id_lookup=True,
)
legacy_out = legacy_fn(
    [{"role": "user", "content": "Test contexto unique substring 35chars analise"}],
    system_prompt="Você é Elon Musk.",
)
check("95%" in legacy_out, f"lookup legado explicito aplica persona ({legacy_out!r})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
