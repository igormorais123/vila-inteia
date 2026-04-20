"""Testes Onda 64: wiring tier+cache+budget no chamar_llm."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_budget_esgotado_bloqueia():
    import importlib
    import engine.ia_client as ic
    importlib.reload(ic)
    from engine.budget_tracker import BUDGET_GLOBAL
    # Força budget esgotado
    BUDGET_GLOBAL.limite_usd = 0.0
    BUDGET_GLOBAL.total_usd = 1.0
    r = ic.chamar_llm([{"role": "user", "content": "x"}], modelo="rapido")
    teste("budget esgotado: chamar_llm retorna None", r is None)
    # Restaura
    BUDGET_GLOBAL.limite_usd = float("inf")
    BUDGET_GLOBAL.total_usd = 0.0


def t_cache_hit_retorna_sem_provider():
    # Limpa env de providers
    for k in ("OMNIROUTE_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
              "CLAUDE_API_KEY"):
        os.environ.pop(k, None)

    import importlib
    import engine.ia_client as ic
    importlib.reload(ic)
    from engine.ia_cache import CACHE_GLOBAL, cache_chave

    # Pré-popula cache
    system = "sys"
    user = "q"
    # Determinar modelo_real via _modelo() — provider=nenhum, cai em Anthropic map
    # Pega diretamente
    modelo_real = ic._modelo("rapido")
    chave = cache_chave(system, user, modelo_real)
    CACHE_GLOBAL.put(chave, "CACHED_RESP")

    r = ic.chamar_llm(
        [{"role": "user", "content": user}],
        system_prompt=system, modelo="rapido", temperatura=0.1,
    )
    teste("cache hit com temp baixa retorna valor",
          r == "CACHED_RESP", f"got {r!r}")


def t_cache_skip_temp_alta():
    # Limpa cache
    from engine.ia_cache import CACHE_GLOBAL, cache_chave
    CACHE_GLOBAL.limpar()
    import importlib
    import engine.ia_client as ic
    importlib.reload(ic)

    modelo_real = ic._modelo("rapido")
    chave = cache_chave("sys", "q", modelo_real)
    CACHE_GLOBAL.put(chave, "CACHED_RESP")

    # Temp 0.8 → cache desabilitado
    r = ic.chamar_llm(
        [{"role": "user", "content": "q"}],
        system_prompt="sys", modelo="rapido", temperatura=0.8,
    )
    teste("temp alta não usa cache", r != "CACHED_RESP")


def t_registrar_uso_incrementa_budget():
    for k in ("OMNIROUTE_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
              "CLAUDE_API_KEY"):
        os.environ.pop(k, None)
    import importlib
    import engine.ia_client as ic
    importlib.reload(ic)
    from engine.budget_tracker import BUDGET_GLOBAL

    BUDGET_GLOBAL.resetar()
    BUDGET_GLOBAL.limite_usd = float("inf")

    ic._registrar_uso(
        "gemini-2.5-flash-lite",
        [{"role": "user", "content": "x" * 4000}],  # ~1000 tokens
        system_prompt="y" * 400,                     # ~100 tokens
        resposta="z" * 2000,                          # ~500 tokens
    )
    s = BUDGET_GLOBAL.stats()
    teste("n_chamadas=1", s["n_chamadas"] == 1)
    teste("tokens_in > 0", s["total_tokens_in"] > 0)
    teste("tokens_out > 0", s["total_tokens_out"] > 0)
    teste("total_usd > 0", s["total_usd"] > 0)


def main():
    print("=== test_onda_64 ===")
    for fn in [t_budget_esgotado_bloqueia, t_cache_hit_retorna_sem_provider,
               t_cache_skip_temp_alta, t_registrar_uso_incrementa_budget]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
