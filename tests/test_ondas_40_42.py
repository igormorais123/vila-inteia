"""Testes Ondas 40-42: docker-compose + benchmark + README."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# Onda 40

def t_docker_compose_existe():
    p = Path("docker-compose.yml")
    teste("docker-compose.yml existe", p.exists())


def t_docker_compose_valido():
    conteudo = Path("docker-compose.yml").read_text()
    teste("define serviço vila", "vila:" in conteudo)
    teste("define serviço mcp-server", "mcp-server:" in conteudo)
    teste("healthcheck definido", "healthcheck:" in conteudo)
    teste("volumes definidos", "volumes:" in conteudo)


def t_dockerignore_existe():
    teste(".dockerignore existe", Path(".dockerignore").exists())


# Onda 41

def t_benchmark_existe():
    teste("tests/benchmark.py existe", Path("tests/benchmark.py").exists())


def t_benchmark_parsea():
    import ast
    src = Path("tests/benchmark.py").read_text()
    try:
        ast.parse(src)
        teste("benchmark.py parsea Python válido", True)
    except SyntaxError as e:
        teste("benchmark.py parsea", False, str(e))


def t_benchmark_tem_runner():
    conteudo = Path("tests/benchmark.py").read_text()
    teste("benchmark tem main()", "def main()" in conteudo)
    teste("benchmark tem @bench decorator", "@bench" in conteudo)


# Onda 42

def t_readme_quickstart():
    conteudo = Path("README.md").read_text()
    teste("README tem Quickstart", "## Quickstart" in conteudo)
    teste("README tem 3 passos", "3 passos" in conteudo)
    teste("README menciona cockpit.html", "cockpit.html" in conteudo)
    teste("README menciona docker-compose", "docker-compose" in conteudo)


def t_readme_cli_quickstart():
    conteudo = Path("README.md").read_text()
    teste("README tem CLI quickstart", "vila_cli.py" in conteudo)
    teste("README tem tabela benchmark", "Latência" in conteudo and "Ops/s" in conteudo)


def main():
    print("=== test_ondas_40_42 ===")
    for fn in [t_docker_compose_existe, t_docker_compose_valido, t_dockerignore_existe,
               t_benchmark_existe, t_benchmark_parsea, t_benchmark_tem_runner,
               t_readme_quickstart, t_readme_cli_quickstart]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
