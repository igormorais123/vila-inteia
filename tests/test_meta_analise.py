"""Testes meta-análise cross-runs (Onda 35)."""

from __future__ import annotations
import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.meta_analise import (
    analisar, carregar_runs_de_pasta, relatorio_markdown, MetaEstatistica,
)
from engine.psicohistoria.replay import ExportRun

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _run(vila_id: str, estados: list[str]) -> ExportRun:
    return ExportRun(
        vila_id=vila_id, timestamp_export=0.0,
        n_steps=len(estados), estados=list(estados),
        steps=list(range(len(estados))), metricas=[], mules=[], meta={},
    )


def t_analisar_vazio():
    m = analisar([])
    teste("vazio: n_runs=0", m.n_runs == 0)


def t_analisar_1_run():
    m = analisar([_run("a", ["x", "y", "x"])])
    teste("1 run: n_runs=1", m.n_runs == 1)
    teste("agregada = distribuição dessa run",
          abs(m.distribuicao_agregada["x"] - 2/3) < 1e-9)


def t_variancia_baixa_runs_similares():
    runs = [_run(f"r{i}", ["a", "a", "b"]) for i in range(5)]
    m = analisar(runs)
    teste("runs idênticas: variância ≈ 0",
          all(v < 1e-9 for v in m.variancia_por_estado.values()))


def t_variancia_alta_runs_distintas():
    runs = [
        _run("r1", ["a"] * 10),
        _run("r2", ["b"] * 10),
        _run("r3", ["c"] * 10),
    ]
    m = analisar(runs)
    teste("runs totalmente distintas: variância > 0.2 em algum estado",
          max(m.variancia_por_estado.values()) > 0.2)


def t_estados_universais():
    runs = [_run(f"r{i}", ["a", "b"]) for i in range(3)]
    m = analisar(runs)
    teste("universais = [a, b]", set(m.estados_universais) == {"a", "b"})


def t_estados_raros():
    # 'c' aparece só em 1 de 4 runs
    runs = [
        _run("r1", ["a", "b"]),
        _run("r2", ["a", "b"]),
        _run("r3", ["a", "b"]),
        _run("r4", ["a", "c"]),
    ]
    m = analisar(runs)
    teste("c é raro", "c" in m.estados_raros)
    teste("a e b não são raros",
          "a" not in m.estados_raros and "b" not in m.estados_raros)


def t_convergencia_final():
    runs = [
        _run("r1", ["a", "equilibrio"]),
        _run("r2", ["b", "equilibrio"]),
        _run("r3", ["c", "polarizacao"]),
    ]
    m = analisar(runs)
    teste("equilibrio convergência 2",
          m.convergencia_final.get("equilibrio") == 2)
    teste("polarizacao convergência 1",
          m.convergencia_final.get("polarizacao") == 1)


def t_kl_range():
    runs = [_run(f"r{i}", ["x", "y"]) for i in range(3)]
    m = analisar(runs)
    kl_min, kl_max = m.correlacao_inter_run_ranges
    teste("KL iguais: min=max≈0", kl_min < 1e-6 and kl_max < 1e-6)


def t_carregar_runs_de_pasta():
    with tempfile.TemporaryDirectory() as d:
        # Cria 2 arquivos JSON válidos
        for i in range(2):
            payload = {
                "vila_id": f"r{i}", "timestamp_export": 0.0,
                "n_steps": 3, "estados": ["a", "b", "a"],
                "steps": [0, 1, 2], "metricas": [], "mules": [], "meta": {},
            }
            with open(f"{d}/run_{i}.json", "w") as f:
                json.dump(payload, f)
        runs = carregar_runs_de_pasta(d)
        teste("carregou 2 runs da pasta", len(runs) == 2)


def t_relatorio_markdown():
    runs = [_run("r1", ["a", "b"]), _run("r2", ["a", "a"])]
    m = analisar(runs)
    md = relatorio_markdown(m)
    teste("relatório tem título", "# Meta-análise" in md)
    teste("relatório menciona runs count", "(2 runs)" in md)
    teste("relatório tem seção universais", "Universais" in md)


def main():
    print("=== test_meta_analise ===")
    for fn in [t_analisar_vazio, t_analisar_1_run,
               t_variancia_baixa_runs_similares, t_variancia_alta_runs_distintas,
               t_estados_universais, t_estados_raros, t_convergencia_final,
               t_kl_range, t_carregar_runs_de_pasta, t_relatorio_markdown]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
