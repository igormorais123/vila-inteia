"""
Meta-análise cross-runs (Onda 35).

Agrega múltiplos ExportRun para extrair:
    - Baseline médio (distribuição típica de estados)
    - Variância cross-run (reprodutibilidade)
    - Estados outliers (aparecem em poucos runs)
    - Estatísticas de convergência
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
from collections import defaultdict, Counter

from engine.psicohistoria.replay import ExportRun, carregar_run


@dataclass
class MetaEstatistica:
    n_runs: int
    distribuicao_agregada: dict[str, float]
    variancia_por_estado: dict[str, float]
    estados_universais: list[str]         # presentes em todos os runs
    estados_raros: list[str]              # presentes em < 50% dos runs
    convergencia_final: dict[str, int]    # estado final → contagem
    correlacao_inter_run_ranges: tuple[float, float]  # KL mín, máx


def _distribuicao(estados: list[str]) -> dict[str, float]:
    if not estados:
        return {}
    c = Counter(estados)
    n = len(estados)
    return {k: v / n for k, v in c.items()}


def _kl(p: dict[str, float], q: dict[str, float]) -> float:
    eps = 1e-12
    total = 0.0
    for k in set(p) | set(q):
        pk = max(p.get(k, 0), eps)
        qk = max(q.get(k, 0), eps)
        total += pk * math.log(pk / qk)
    return total


def analisar(runs: list[ExportRun]) -> MetaEstatistica:
    """Agrega estatisticamente N runs."""
    if not runs:
        return MetaEstatistica(0, {}, {}, [], [], {}, (0, 0))

    # Distribuição agregada (peso igual por run, não por step)
    por_run = [_distribuicao(r.estados) for r in runs]
    todos_estados = set()
    for d in por_run:
        todos_estados |= set(d)

    agregada = {e: sum(d.get(e, 0) for d in por_run) / len(runs)
                for e in todos_estados}

    # Variância por estado entre runs
    variancia = {}
    for e in todos_estados:
        vals = [d.get(e, 0) for d in por_run]
        media = agregada[e]
        var = sum((v - media) ** 2 for v in vals) / len(vals)
        variancia[e] = var

    # Universais vs raros
    presencas = {e: sum(1 for d in por_run if d.get(e, 0) > 0) for e in todos_estados}
    universais = sorted([e for e, n in presencas.items() if n == len(runs)])
    raros = sorted([e for e, n in presencas.items() if n / len(runs) < 0.5])

    # Estados finais
    finais = Counter(r.estados[-1] for r in runs if r.estados)

    # KL pairwise: min e max
    kls = []
    for i in range(len(por_run)):
        for j in range(i + 1, len(por_run)):
            kls.append(_kl(por_run[i], por_run[j]))
    kl_range = (min(kls), max(kls)) if kls else (0.0, 0.0)

    return MetaEstatistica(
        n_runs=len(runs),
        distribuicao_agregada=agregada,
        variancia_por_estado=variancia,
        estados_universais=universais,
        estados_raros=raros,
        convergencia_final=dict(finais),
        correlacao_inter_run_ranges=kl_range,
    )


def carregar_runs_de_pasta(pasta: str | Path) -> list[ExportRun]:
    """Carrega todos JSON da pasta como ExportRun (best-effort)."""
    p = Path(pasta)
    runs = []
    for arquivo in p.glob("*.json"):
        try:
            runs.append(carregar_run(arquivo))
        except Exception:
            pass
    return runs


def relatorio_markdown(m: MetaEstatistica) -> str:
    """Gera relatório compacto em Markdown."""
    linhas = [
        f"# Meta-análise ({m.n_runs} runs)",
        "",
        "## Distribuição agregada",
        "",
    ]
    for e, p in sorted(m.distribuicao_agregada.items(), key=lambda x: -x[1]):
        var = m.variancia_por_estado.get(e, 0)
        linhas.append(f"- `{e}`: {p*100:.1f}% (σ²={var:.4f})")

    linhas.extend([
        "",
        f"## Universais ({len(m.estados_universais)})",
        ", ".join(f"`{e}`" for e in m.estados_universais) or "nenhum",
        "",
        f"## Raros ({len(m.estados_raros)})",
        ", ".join(f"`{e}`" for e in m.estados_raros) or "nenhum",
        "",
        "## Convergência final",
    ])
    for e, n in sorted(m.convergencia_final.items(), key=lambda x: -x[1]):
        linhas.append(f"- `{e}`: {n}/{m.n_runs} runs")

    kl_min, kl_max = m.correlacao_inter_run_ranges
    linhas.extend([
        "",
        f"## Variabilidade inter-run (KL pairwise)",
        f"- mínima: {kl_min:.4f}",
        f"- máxima: {kl_max:.4f}",
    ])
    return "\n".join(linhas)
