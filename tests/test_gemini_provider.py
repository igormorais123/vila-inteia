"""Smoke test provider Gemini no ia_client (Onda 58)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Não chama LLM real — só verifica lógica de seleção de provider e modelos.

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_provider_detecta_gemini():
    # Clean env, set só Gemini
    old = {}
    for k in ("OMNIROUTE_API_KEY", "GEMINI_API_KEY", "CLAUDE_API_KEY"):
        old[k] = os.environ.pop(k, None)

    os.environ["GEMINI_API_KEY"] = "fake-key-p-testar-logica"
    # Reimporta modulo para resetar globals
    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("provider = gemini", m._provider == "gemini")
    teste("client criado", m._client is not None)
    teste("rapido → gemini-2.5-flash-lite (default)",
          m._modelo("rapido") == "gemini-2.5-flash-lite")

    # Restaurar
    for k, v in old.items():
        if v is not None: os.environ[k] = v
        else: os.environ.pop(k, None)


def t_gemini_model_override():
    for k in ("OMNIROUTE_API_KEY", "CLAUDE_API_KEY"):
        os.environ.pop(k, None)
    os.environ["GEMINI_API_KEY"] = "fake"
    os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("override GEMINI_MODEL respeitado",
          m._modelo("rapido") == "gemini-2.5-flash")

    del os.environ["GEMINI_MODEL"]
    os.environ.pop("GEMINI_API_KEY", None)


def t_sem_provider_volta_para_heuristica():
    for k in ("OMNIROUTE_API_KEY", "GEMINI_API_KEY", "CLAUDE_API_KEY"):
        os.environ.pop(k, None)

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("provider = nenhum", m._provider == "nenhum")
    teste("client = None", m._client is None)


def main():
    print("=== test_gemini_provider ===")
    for fn in [t_provider_detecta_gemini, t_gemini_model_override,
               t_sem_provider_volta_para_heuristica]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
