"""Testes Ondas 52-54."""

from __future__ import annotations
import sys, os, subprocess, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# Onda 52

def t_nature_html_existe():
    teste("vila_inteia_nature.html existe",
          Path("docs/artigo/vila_inteia_nature.html").exists())


def t_nature_html_tem_secoes_imrad():
    conteudo = Path("docs/artigo/vila_inteia_nature.html").read_text()
    secoes = ["Introduction", "Architecture", "Formal modules",
               "Results", "Discussion", "Methods", "References"]
    for s in secoes:
        teste(f"nature tem seção {s}", s.upper() in conteudo.upper())


def t_nature_tem_refs_numeradas():
    conteudo = Path("docs/artigo/vila_inteia_nature.html").read_text()
    teste("refs numeradas inline <sup class='ref'>",
          'class="ref"' in conteudo and "<sup" in conteudo)


# Onda 53

def t_dump_openapi_script():
    teste("dump_openapi.py existe", Path("scripts/dump_openapi.py").exists())


def t_dump_openapi_executa():
    import importlib.util
    with tempfile.TemporaryDirectory() as d:
        out = f"{d}/spec.json"
        r = subprocess.run(
            ["python", "scripts/dump_openapi.py", "--out", out],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": "."},
        )
        teste("dump_openapi retorna 0", r.returncode == 0,
              f"stderr={r.stderr[:200]}")
        if os.path.exists(out):
            spec = json.loads(Path(out).read_text())
            teste("openapi válido (paths)", "paths" in spec)
            teste("openapi >= 10 paths", len(spec.get("paths", {})) >= 10)


# Onda 54

def t_synth_gen_script():
    teste("gen_synth_dataset.py existe",
          Path("scripts/gen_synth_dataset.py").exists())


def t_synth_gen_executa():
    with tempfile.TemporaryDirectory() as d:
        out = f"{d}/synth.json"
        r = subprocess.run(
            ["python", "scripts/gen_synth_dataset.py",
             "--n-steps", "100", "--mule-rate", "0.1", "--out", out],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "PYTHONPATH": "."},
        )
        teste("synth gera arquivo", r.returncode == 0)
        if os.path.exists(out):
            dados = json.loads(Path(out).read_text())
            teste("synth tem trajetória", len(dados.get("trajetoria", [])) == 100)
            teste("synth tem mules_injetados",
                  isinstance(dados.get("mules_injetados"), list))


def t_synth_mule_rate_zero_nenhum_mule():
    with tempfile.TemporaryDirectory() as d:
        out = f"{d}/synth0.json"
        r = subprocess.run(
            ["python", "scripts/gen_synth_dataset.py",
             "--n-steps", "50", "--mule-rate", "0", "--out", out],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "PYTHONPATH": "."},
        )
        if r.returncode == 0:
            dados = json.loads(Path(out).read_text())
            teste("mule_rate=0: 0 mules injetados",
                  len(dados["mules_injetados"]) == 0)


def main():
    print("=== test_ondas_52_54 ===")
    for fn in [t_nature_html_existe, t_nature_html_tem_secoes_imrad, t_nature_tem_refs_numeradas,
               t_dump_openapi_script, t_dump_openapi_executa,
               t_synth_gen_script, t_synth_gen_executa, t_synth_mule_rate_zero_nenhum_mule]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
