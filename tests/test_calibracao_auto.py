"""Testes Onda 150: auto-select Platt vs isotonic."""

from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.calibracao_auto import fit_melhor_calibrador, salvar_melhor_calibrador
from engine.calibracao_runtime import carregar_coefs, aplicar

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_poucos_amostras_retorna_nenhum():
    r = fit_melhor_calibrador([0.5, 0.5], [0, 1])
    teste("n<5 → nenhum", r["vencedor"] == "nenhum")


def t_escolhe_melhor_brier():
    # Dados que Platt calibra bem (over-confident)
    probs = [0.95, 0.88, 0.92, 0.78, 0.85, 0.90, 0.70, 0.80, 0.65, 0.75]
    y =     [1,    1,    0,    0,    1,    0,    1,    0,    1,    0]
    r = fit_melhor_calibrador(probs, y)
    teste("vencedor definido", r["vencedor"] in ("platt", "isotonic"))
    teste("melhor brier <= raw", min(r["platt"]["brier"], r["isotonic"]["brier"]) <= r["brier_raw"] + 1e-9)


def t_salvar_melhor_formato_correto():
    probs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    y =     [0,    0,    1,    0,    1,    1,    1,    0,    1]
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    r = salvar_melhor_calibrador(probs, y, fonte="test_auto", path=tmp.name)
    teste("salvo_como não-None", r["salvo_como"] is not None)
    loaded = carregar_coefs(path=tmp.name, use_cache=False)
    if r["salvo_como"] == "platt":
        teste("Platt loaded a,b", loaded.get("a") is not None and loaded.get("b") is not None)
    else:
        teste("Isotonic loaded mapping", loaded.get("tipo") == "isotonic")
    os.unlink(tmp.name)


def t_aplicar_reduz_brier_em_over_confident():
    probs = [0.9, 0.9, 0.9, 0.9, 0.5, 0.5, 0.5, 0.5, 0.1, 0.1]
    y =     [1,   0,   1,   0,   1,   0,   1,   0,   0,   0]
    r = fit_melhor_calibrador(probs, y)
    melhor = min(r["platt"]["brier"], r["isotonic"]["brier"])
    teste(f"calibrador reduziu brier (raw {r['brier_raw']:.3f} → melhor {melhor:.3f})",
          melhor <= r["brier_raw"])


def main():
    print("=== test_calibracao_auto ===")
    for fn in [t_poucos_amostras_retorna_nenhum,
               t_escolhe_melhor_brier,
               t_salvar_melhor_formato_correto,
               t_aplicar_reduz_brier_em_over_confident]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
