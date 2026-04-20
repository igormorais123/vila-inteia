"""Testes provider Groq no ia_client (Onda 63)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _limpar_env():
    for k in ("OMNIROUTE_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY",
              "CLAUDE_API_KEY", "GROQ_MODEL_RAPIDO", "GROQ_MODEL_ANALISE",
              "GROQ_MODEL_SINTESE", "GEMINI_MODEL"):
        os.environ.pop(k, None)


def t_groq_detectado():
    _limpar_env()
    os.environ["GROQ_API_KEY"] = "fake-groq-key"

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("provider = groq", m._provider == "groq")
    teste("client criado", m._client is not None)


def t_groq_modelos_default():
    _limpar_env()
    os.environ["GROQ_API_KEY"] = "fake"

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("rapido → llama-3.1-8b-instant",
          m._modelo("rapido") == "llama-3.1-8b-instant")
    teste("analise → llama-3.3-70b-versatile",
          m._modelo("analise") == "llama-3.3-70b-versatile")
    teste("sintese → llama-3.1-8b-instant",
          m._modelo("sintese") == "llama-3.1-8b-instant")


def t_groq_override_modelo():
    _limpar_env()
    os.environ["GROQ_API_KEY"] = "fake"
    os.environ["GROQ_MODEL_ANALISE"] = "mixtral-8x7b-32768"

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("override GROQ_MODEL_ANALISE respeitado",
          m._modelo("analise") == "mixtral-8x7b-32768")


def t_prioridade_omniroute_sobre_groq():
    _limpar_env()
    os.environ["OMNIROUTE_API_KEY"] = "fake-omni"
    os.environ["GROQ_API_KEY"] = "fake-groq"

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("omniroute tem prioridade sobre groq",
          m._provider == "omniroute")


def t_groq_sobre_gemini():
    _limpar_env()
    os.environ["GROQ_API_KEY"] = "fake-groq"
    os.environ["GEMINI_API_KEY"] = "fake-gemini"

    import importlib
    import engine.ia_client as m
    importlib.reload(m)
    m._detectar_provider()

    teste("groq tem prioridade sobre gemini",
          m._provider == "groq")


def main():
    print("=== test_groq_provider ===")
    for fn in [t_groq_detectado, t_groq_modelos_default,
               t_groq_override_modelo, t_prioridade_omniroute_sobre_groq,
               t_groq_sobre_gemini]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
