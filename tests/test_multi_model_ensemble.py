"""Testes Onda 164: multi-model ensemble."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_chamar_ensemble_probs_mock(monkeypatch=None):
    """Stub chamar_llm pra não bater LLM real."""
    from engine import ia_client
    from engine import multi_model_ensemble as mme

    call_log = []
    def fake_chamar_llm(mensagens, modelo, max_tokens, temperatura, system_prompt, bypass_step_cap):
        modelo_real = os.environ.get("GROQ_MODEL_RAPIDO", "unknown")
        call_log.append(modelo_real)
        # Retorna respostas diferentes pro mesmo prompt
        mapping = {
            "model_a": "Resp A. PROBABILIDADE FINAL: 60%",
            "model_b": "Resp B. PROBABILIDADE FINAL: 70%",
            "model_c": "Resp C. PROBABILIDADE FINAL: 80%",
        }
        return mapping.get(modelo_real, "PROBABILIDADE FINAL: 50%")

    orig = ia_client.chamar_llm
    ia_client.chamar_llm = fake_chamar_llm
    try:
        r = mme.chamar_ensemble_probs(
            mensagens=[{"role": "user", "content": "x"}],
            modelos=["model_a", "model_b", "model_c"],
        )
        teste("3 modelos queried", len(r["modelos_queried"]) == 3)
        teste("3 probs extraídas", r["n_validas"] == 3)
        teste("median = 0.70", abs(r["median"] - 0.70) < 1e-9)
        teste("0 erros", r["errors"] == 0)
    finally:
        ia_client.chamar_llm = orig


def t_chamar_ensemble_com_falhas():
    from engine import ia_client
    from engine import multi_model_ensemble as mme

    def fake_chamar_llm(mensagens, modelo, max_tokens, temperatura, system_prompt, bypass_step_cap):
        modelo_real = os.environ.get("GROQ_MODEL_RAPIDO", "unknown")
        if modelo_real == "model_b":
            return None
        return "PROBABILIDADE FINAL: 70%"

    orig = ia_client.chamar_llm
    ia_client.chamar_llm = fake_chamar_llm
    try:
        r = mme.chamar_ensemble_probs(
            mensagens=[{"role": "user", "content": "x"}],
            modelos=["model_a", "model_b", "model_c"],
        )
        teste("2 valid (model_b falhou)", r["n_validas"] == 2)
        teste("1 error contado", r["errors"] == 1)
        teste("median sobre 2 probs válidas", r["median"] == 0.70)
    finally:
        ia_client.chamar_llm = orig


def t_sem_probs_extraidas():
    from engine import ia_client
    from engine import multi_model_ensemble as mme

    def fake_chamar_llm(mensagens, modelo, max_tokens, temperatura, system_prompt, bypass_step_cap):
        return "sem número"

    orig = ia_client.chamar_llm
    ia_client.chamar_llm = fake_chamar_llm
    try:
        r = mme.chamar_ensemble_probs(
            mensagens=[{"role": "user", "content": "x"}],
            modelos=["model_a"],
        )
        teste("sem prob: median=None", r["median"] is None)
        teste("n_validas=0", r["n_validas"] == 0)
    finally:
        ia_client.chamar_llm = orig


def t_modelos_constante_nao_vazia():
    from engine.multi_model_ensemble import MODELOS_GROQ_DIVERSE
    teste("MODELOS_GROQ_DIVERSE tem entries", len(MODELOS_GROQ_DIVERSE) >= 3)


def main():
    print("=== test_multi_model_ensemble ===")
    for fn in [t_chamar_ensemble_probs_mock, t_chamar_ensemble_com_falhas,
               t_sem_probs_extraidas, t_modelos_constante_nao_vazia]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
