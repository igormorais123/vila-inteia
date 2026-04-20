"""Testes Ondas 43-45: metrics + CHANGELOG + E2E script."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# Onda 43

def t_rotas_metrics_importa():
    from api import rotas_metrics
    teste("rotas_metrics importa", rotas_metrics.router is not None)


def t_metrics_endpoint_retorna_texto():
    from api.rotas_metrics import endpoint_metrics
    r = endpoint_metrics()
    teste("metrics retorna str", isinstance(r, str))
    teste("metrics tem vila_steps_total", "vila_steps_total" in r)
    teste("metrics tem HELP + TYPE", "# HELP" in r and "# TYPE" in r)


def t_metrics_exposition_format():
    from api.rotas_metrics import endpoint_metrics
    r = endpoint_metrics()
    # Prometheus exposition: linhas tipo "metric_name{labels} value"
    linhas = [l for l in r.split("\n") if l and not l.startswith("#")]
    teste("metrics tem linhas de valor",
          any("vila_steps_total" in l and l.split()[-1].replace(".", "").replace("-", "").isdigit()
              for l in linhas))


# Onda 44

def t_version_file():
    p = Path("VERSION")
    teste("VERSION existe", p.exists())
    teste("VERSION contém semver",
          p.read_text().strip().count(".") >= 2)


def t_changelog_existe():
    teste("CHANGELOG.md existe", Path("CHANGELOG.md").exists())


def t_changelog_tem_v1():
    conteudo = Path("CHANGELOG.md").read_text()
    teste("CHANGELOG tem [1.0.0]", "[1.0.0]" in conteudo)
    teste("CHANGELOG menciona Onda 11", "Onda 11" in conteudo)
    teste("CHANGELOG menciona benchmark",
          "benchmark" in conteudo.lower() or "Onda 41" in conteudo)


# Onda 45

def t_e2e_script_existe():
    teste("tests/e2e_playwright.py existe",
          Path("tests/e2e_playwright.py").exists())


def t_e2e_script_parsea():
    import ast
    try:
        ast.parse(Path("tests/e2e_playwright.py").read_text())
        teste("e2e parsea Python válido", True)
    except SyntaxError as e:
        teste("e2e parsea", False, str(e))


def t_e2e_script_skip_se_sem_playwright():
    conteudo = Path("tests/e2e_playwright.py").read_text()
    teste("e2e tem SKIP se sem playwright",
          "SKIP: playwright" in conteudo)


def main():
    print("=== test_ondas_43_45 ===")
    for fn in [t_rotas_metrics_importa, t_metrics_endpoint_retorna_texto,
               t_metrics_exposition_format,
               t_version_file, t_changelog_existe, t_changelog_tem_v1,
               t_e2e_script_existe, t_e2e_script_parsea,
               t_e2e_script_skip_se_sem_playwright]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
