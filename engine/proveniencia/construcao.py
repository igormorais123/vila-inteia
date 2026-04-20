"""
Construção da árvore de proveniência a partir de traces raw.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class NoTrace:
    trace_id: str
    fase: str
    agente_id: str
    inicio: str
    fim: str
    duracao_ms: int
    tokens: int
    custo_usd: float
    resultado: str            # "sucesso" | "falha" | "aprovacao_humana"
    causal_parent: str | None = None
    filhos: list["NoTrace"] = field(default_factory=list)


@dataclass
class Influencia:
    agente_origem: str
    agente_destino: str
    peso: float               # frequência normalizada de citação/resposta


@dataclass
class Proveniencia:
    materia_id: str
    trace_hash: str           # preenchido por hash_helper
    raiz: NoTrace | None
    agentes_envolvidos: list[str]
    tokens_totais: int
    custo_usd_total: float
    duracao_ms_total: int
    fases_cobertas: list[str]
    grafo_influencia: list[Influencia]
    created_at: str = ""


def construir_proveniencia(
    materia_id: str,
    traces: list[dict],
    agentes_envolvidos: list[str] | None = None,
    citacoes: list[tuple[str, str]] | None = None,
) -> Proveniencia:
    """
    Monta árvore causal a partir de traces e calcula métricas agregadas.

    traces: lista de dicts com formato vila_traces
    citacoes: (origem_id, destino_id) — pares de citação derivados de conversas
    """
    if agentes_envolvidos is None:
        agentes_envolvidos = sorted({t.get("agente_id", "") for t in traces if t.get("agente_id")})

    # Mapeia trace_id -> NoTrace
    nos: dict[str, NoTrace] = {}
    for t in traces:
        n = NoTrace(
            trace_id=t.get("trace_id", ""),
            fase=t.get("fase", "?"),
            agente_id=t.get("agente_id", ""),
            inicio=t.get("inicio", ""),
            fim=t.get("fim", ""),
            duracao_ms=int(t.get("duracao_ms", 0)),
            tokens=int(t.get("tokens_consumidos", t.get("tokens", 0))),
            custo_usd=float(t.get("custo_usd", 0.0)),
            resultado=t.get("resultado", "sucesso"),
            causal_parent=t.get("causal_parent"),
        )
        nos[n.trace_id] = n

    # Liga pais → filhos
    raiz = None
    for n in nos.values():
        if n.causal_parent and n.causal_parent in nos:
            nos[n.causal_parent].filhos.append(n)
        else:
            if raiz is None:
                raiz = n

    # Agregados
    tokens = sum(n.tokens for n in nos.values())
    custo = sum(n.custo_usd for n in nos.values())
    duracao = sum(n.duracao_ms for n in nos.values())
    fases = sorted({n.fase for n in nos.values()})

    # Grafo de influência: pares agregados
    influencias: list[Influencia] = []
    if citacoes:
        contagem: dict[tuple[str, str], int] = defaultdict(int)
        for o, d in citacoes:
            contagem[(o, d)] += 1
        total = max(1, sum(contagem.values()))
        for (o, d), c in contagem.items():
            influencias.append(Influencia(
                agente_origem=o,
                agente_destino=d,
                peso=c / total,
            ))

    return Proveniencia(
        materia_id=materia_id,
        trace_hash="",        # preenchido depois
        raiz=raiz,
        agentes_envolvidos=agentes_envolvidos,
        tokens_totais=tokens,
        custo_usd_total=custo,
        duracao_ms_total=duracao,
        fases_cobertas=fases,
        grafo_influencia=influencias,
    )


def serializar_arvore(no: NoTrace | None) -> dict:
    """Dict serializável (para JSON / hash)."""
    if no is None:
        return {}
    return {
        "trace_id": no.trace_id,
        "fase": no.fase,
        "agente_id": no.agente_id,
        "inicio": no.inicio,
        "duracao_ms": no.duracao_ms,
        "tokens": no.tokens,
        "custo_usd": round(no.custo_usd, 6),
        "resultado": no.resultado,
        "filhos": [serializar_arvore(f) for f in no.filhos],
    }
