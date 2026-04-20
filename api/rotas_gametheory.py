"""
Rotas FastAPI — /api/v1/gametheory

Expõe engine.game_theory + opinion_dynamics + simulacao_avancada para o frontend.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.game_theory.equilibrio import nash_puro, nash_misto, stackelberg, best_response
from engine.game_theory.mecanismos import (
    Lance,
    vickrey_2nd_price,
    vcg_alocacao,
    leilao_publicacao_mirante,
)
from engine.game_theory.evolutivo import (
    replicator_convergencia,
    ess_candidatos,
    hawk_dove_ess,
)
from engine.game_theory.jogos_repetidos import (
    tit_for_tat, grim_trigger, sempre_cooperar, sempre_trair, tit_for_two_tats,
    rodada_iterada, torneio_axelrod,
)
from engine.game_theory.bem_comum import public_goods_game, ostrom_principios
from engine.opinion_dynamics.degroot import degroot_convergencia
from engine.opinion_dynamics.bounded_confidence import deffuant_simular, polarization_index
from engine.opinion_dynamics.cascatas import bikhchandani
from engine.simulacao_avancada.coalizoes import shapley_value, banzhaf_power
from engine.simulacao_avancada.schelling import tipping_point
from engine.simulacao_avancada.redes import small_world, preferential_attachment, detectar_comunidades


router = APIRouter(prefix="/api/v1/gametheory", tags=["gametheory"])


_ESTRATEGIAS = {
    "tit-for-tat": tit_for_tat,
    "grim-trigger": grim_trigger,
    "sempre-cooperar": sempre_cooperar,
    "sempre-trair": sempre_trair,
    "tit-for-two-tats": tit_for_two_tats,
}


class JogoMatricialReq(BaseModel):
    payoffs_a: list[list[float]] = Field(..., description="matriz MxN")
    payoffs_b: list[list[float]] = Field(..., description="matriz MxN")


class NashResp(BaseModel):
    ne_puros: list[dict[str, Any]]
    ne_misto: dict[str, Any] | None = None


@router.post("/nash", response_model=NashResp)
def endpoint_nash(req: JogoMatricialReq) -> NashResp:
    A = np.array(req.payoffs_a, dtype=float)
    B = np.array(req.payoffs_b, dtype=float)
    if A.shape != B.shape:
        raise HTTPException(400, "matrizes com shapes divergentes")
    puros = nash_puro(A, B)
    misto = nash_misto(A, B)
    return NashResp(
        ne_puros=[
            {
                "estrategias": [e.tolist() for e in eq.estrategias],
                "payoffs": eq.payoffs,
                "unico": eq.unico,
            }
            for eq in puros
        ],
        ne_misto=(
            {
                "estrategias": [e.tolist() for e in misto.estrategias],
                "payoffs": misto.payoffs,
            }
            if misto
            else None
        ),
    )


@router.post("/stackelberg")
def endpoint_stackelberg(req: JogoMatricialReq):
    A = np.array(req.payoffs_a, dtype=float)
    B = np.array(req.payoffs_b, dtype=float)
    eq = stackelberg(A, B)
    return {
        "estrategia_leader": eq.estrategias[0].tolist(),
        "estrategia_follower": eq.estrategias[1].tolist(),
        "payoffs": eq.payoffs,
    }


class TorneioReq(BaseModel):
    estrategias: list[str]
    rodadas: int = 200


@router.post("/torneio")
def endpoint_torneio(req: TorneioReq):
    disp = {n: _ESTRATEGIAS[n] for n in req.estrategias if n in _ESTRATEGIAS}
    if len(disp) < 2:
        raise HTTPException(400, f"estratégias desconhecidas. Disponíveis: {list(_ESTRATEGIAS.keys())}")
    ranking = torneio_axelrod(disp, rodadas=req.rodadas)
    return {"ranking": sorted(ranking.items(), key=lambda kv: kv[1], reverse=True)}


class ReplicatorReq(BaseModel):
    populacao_inicial: list[float]
    payoffs: list[list[float]]
    max_iter: int = 500


@router.post("/replicator")
def endpoint_replicator(req: ReplicatorReq):
    pop = np.array(req.populacao_inicial, dtype=float)
    A = np.array(req.payoffs, dtype=float)
    final, it = replicator_convergencia(pop, A, max_iter=req.max_iter)
    return {
        "final": final.tolist(),
        "iteracoes": it,
        "ess": ess_candidatos(A) if A.shape[0] == A.shape[1] else [],
    }


@router.get("/hawk-dove")
def endpoint_hawk_dove(v: float = 2.0, c: float = 3.0):
    return {"p_hawk_star": hawk_dove_ess(v, c)}


class LancesReq(BaseModel):
    lances: list[dict]   # [{bidder_id, valor}]
    slots: int = 1


@router.post("/leilao-vickrey")
def endpoint_vickrey(req: LancesReq):
    ls = [Lance(bidder_id=l["bidder_id"], valor=float(l["valor"])) for l in req.lances]
    if req.slots == 1:
        r = vickrey_2nd_price(ls)
        return {"vencedor": r.vencedor_id, "preco": r.preco_pago} if r else None
    rs = leilao_publicacao_mirante(ls, slots_disponiveis=req.slots)
    return [{"vencedor": a.vencedor_id, "preco": a.preco_pago} for a in rs]


class DegrootReq(BaseModel):
    crencas_inicial: list[float]
    W: list[list[float]]
    max_iter: int = 1000


@router.post("/degroot")
def endpoint_degroot(req: DegrootReq):
    x = np.array(req.crencas_inicial, dtype=float)
    W = np.array(req.W, dtype=float)
    final, it = degroot_convergencia(x, W, max_iter=req.max_iter)
    return {"final": final.tolist(), "iteracoes": it}


class DeffuantReq(BaseModel):
    crencas_inicial: list[float]
    epsilon: float = 0.3
    mu: float = 0.5
    passos: int = 5000
    seed: int = 42


@router.post("/deffuant")
def endpoint_deffuant(req: DeffuantReq):
    x = np.array(req.crencas_inicial, dtype=float)
    final = deffuant_simular(x, req.epsilon, req.mu, req.passos, req.seed)
    return {
        "final": final.tolist(),
        "polarization_index": polarization_index(final),
    }


class CascadeReq(BaseModel):
    sinais: list[int]
    prior: float = 0.5
    precisao: float = 0.7
    seed: int = 42


@router.post("/cascata")
def endpoint_cascata(req: CascadeReq):
    r = bikhchandani(req.sinais, req.prior, req.precisao, req.seed)
    return {
        "decisoes": r.decisoes,
        "cascata_formada": r.cascata_formada,
        "posicao_cascata": r.posicao_cascata,
        "decisao_final": r.decisao_final,
    }


class ShapleyReq(BaseModel):
    jogadores: list[str]
    coalizoes: dict[str, float]   # frozenset-key (string csv) -> valor


@router.post("/shapley")
def endpoint_shapley(req: ShapleyReq):
    # coalizoes key: "a,b,c" em ordem alfa
    def v(coal: frozenset) -> float:
        if not coal:
            return 0.0
        k = ",".join(sorted(coal))
        return req.coalizoes.get(k, 0.0)

    return shapley_value(req.jogadores, v)


@router.post("/banzhaf")
def endpoint_banzhaf(req: ShapleyReq):
    def v(coal: frozenset) -> float:
        if not coal:
            return 0.0
        k = ",".join(sorted(coal))
        return req.coalizoes.get(k, 0.0)

    return banzhaf_power(req.jogadores, v)


@router.get("/schelling/tipping-point")
def endpoint_tipping(
    grid_h: int = 20,
    grid_w: int = 20,
    fracao: float = 0.7,
    passos: int = 200,
    seed: int = 42,
):
    r = tipping_point(
        tamanho_grid=(grid_h, grid_w),
        fracao_preenchimento=fracao,
        passos=passos,
        seed=seed,
    )
    return r


@router.get("/redes/small-world")
def endpoint_small_world(n: int = 20, k: int = 4, p_rewire: float = 0.1, seed: int = 42):
    adj = small_world(n, k, p_rewire, seed)
    return {"n_nos": len(adj), "arestas": sum(len(v) for v in adj.values()) // 2, "adjacencias": {str(k2): v for k2, v in adj.items()}}


@router.get("/redes/barabasi-albert")
def endpoint_ba(n: int = 30, m: int = 3, seed: int = 42):
    adj = preferential_attachment(n, m, seed)
    graus = [len(adj[i]) for i in range(n)]
    return {"n_nos": len(adj), "grau_max": max(graus), "grau_medio": sum(graus) / len(graus), "grau_por_no": graus}


class ComunidadesReq(BaseModel):
    adjacencias: dict[str, list[int]]


@router.post("/redes/comunidades")
def endpoint_comunidades(req: ComunidadesReq):
    adj = {int(k): v for k, v in req.adjacencias.items()}
    c = detectar_comunidades(adj)
    return {str(k): v for k, v in c.items()}


@router.get("/bem-comum/ostrom")
def endpoint_ostrom():
    return {"principios": ostrom_principios()}


class PublicGoodsReq(BaseModel):
    dotacoes: dict[str, float]
    contribuicoes: dict[str, float]
    mpcr: float = 0.5


@router.post("/bem-comum/public-goods")
def endpoint_public_goods(req: PublicGoodsReq):
    r = public_goods_game(req.dotacoes, req.contribuicoes, mpcr=req.mpcr)
    return {
        "total_pool": r.total_pool,
        "retorno_per_capita": r.retorno_per_capita,
        "payoffs_individuais": r.payoffs_individuais,
        "eficiencia": r.eficiencia,
    }


# =====================================================
# Crenças numéricas — Tracker global (integração real Onda 10)
# =====================================================

@router.get("/crencas/topicos")
def endpoint_crencas_topicos():
    from engine.cognitivo.crenca import TRACKER_GLOBAL
    return {"topicos": sorted(TRACKER_GLOBAL.topicos_rastreados())}


@router.get("/crencas/{topico}/distribuicao")
def endpoint_crencas_distribuicao(topico: str):
    from engine.cognitivo.crenca import TRACKER_GLOBAL
    return TRACKER_GLOBAL.distribuicao(topico)


@router.get("/crencas/{topico}/snapshot")
def endpoint_crencas_snapshot(topico: str, step: int = 0):
    from engine.cognitivo.crenca import TRACKER_GLOBAL
    s = TRACKER_GLOBAL.snapshot(step=step, topico=topico)
    return {
        "step": s.step,
        "topico": s.topico,
        "valor_medio": s.valor_medio,
        "polarizacao": s.polarizacao,
        "n_agentes": s.n_agentes,
    }


@router.get("/crencas/{topico}/historico")
def endpoint_crencas_historico(topico: str):
    from engine.cognitivo.crenca import TRACKER_GLOBAL
    h = TRACKER_GLOBAL.historico(topico)
    return [
        {
            "step": s.step,
            "valor_medio": s.valor_medio,
            "polarizacao": s.polarizacao,
            "n_agentes": s.n_agentes,
        }
        for s in h
    ]


class InicializarCrencasReq(BaseModel):
    agentes: list[str]
    topico: str
    valor_default: float = 0.5
    valores_por_agente: dict[str, float] = {}


@router.post("/crencas/inicializar")
def endpoint_crencas_inicializar(req: InicializarCrencasReq):
    from engine.cognitivo.crenca import TRACKER_GLOBAL
    for a in req.agentes:
        TRACKER_GLOBAL.inicializar_agente(
            a, req.topico,
            req.valores_por_agente.get(a, req.valor_default),
        )
    return {"ok": True, "n_agentes": len(req.agentes), "topico": req.topico}
