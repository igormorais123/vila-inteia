"""Testes Onda 160: peso_vila override per-dataset."""

from __future__ import annotations
import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.peso_vila_dataset import (
    obter_peso_vila, salvar_peso, listar_overrides, _normalize_key,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _tmppath():
    p = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    os.unlink(p)
    return p


def t_normalize_path():
    teste("extrai stem de path",
          _normalize_key("data/backtest/impeachment_dilma_2016.csv") == "impeachment_dilma_2016")
    teste("extrai stem de nome sem path",
          _normalize_key("crypto_bitcoin_2024.csv") == "crypto_bitcoin_2024")
    teste("preserva sem extensão",
          _normalize_key("impeachment_dilma_2016") == "impeachment_dilma_2016")


def t_default_sem_arquivo():
    p = _tmppath()
    teste("default 0.7 sem arquivo",
          obter_peso_vila("qualquer_ds", path=p) == 0.7)


def t_default_override_ausente():
    p = _tmppath()
    salvar_peso("foo", 0.5, path=p)
    teste("outro dataset retorna default",
          obter_peso_vila("bar", path=p) == 0.7)


def t_salvar_obter_roundtrip():
    p = _tmppath()
    salvar_peso("crypto_bitcoin_2024", 0.4, path=p)
    teste("obter retorna salvo",
          obter_peso_vila("crypto_bitcoin_2024", path=p) == 0.4)
    os.unlink(p)


def t_clamp_range():
    p = _tmppath()
    salvar_peso("x", 1.5, path=p)
    teste("clamp max 1.0", obter_peso_vila("x", path=p) == 1.0)
    salvar_peso("x", -0.3, path=p)
    teste("clamp min 0.0", obter_peso_vila("x", path=p) == 0.0)
    os.unlink(p)


def t_listar_overrides():
    p = _tmppath()
    salvar_peso("a", 0.5, path=p)
    salvar_peso("b", 0.8, path=p)
    r = listar_overrides(path=p)
    teste("listar 2 entries", len(r) == 2)
    teste("a preservado", r["a"] == 0.5)
    os.unlink(p)


def main():
    print("=== test_peso_vila_dataset ===")
    for fn in [t_normalize_path, t_default_sem_arquivo,
               t_default_override_ausente, t_salvar_obter_roundtrip,
               t_clamp_range, t_listar_overrides]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
