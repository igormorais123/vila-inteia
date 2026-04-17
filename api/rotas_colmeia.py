"""
API REST da Colmeia — Sistema de Ranking e Dinâmicas Orgânicas.

Endpoints para consultar o ranking, estado e informações de NPCs dentro
do motor da Colmeia (genoma, pontos, patentes, histórico).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

try:
    from ..engine.simulacao import SimulacaoVila
except (ImportError, ValueError):
    from engine.simulacao import SimulacaoVila


# ============================================================
# ESTADO GLOBAL DA SIMULAÇÃO (reusa do rotas_vila.py)
# ============================================================

def obter_simulacao() -> SimulacaoVila:
    """Retorna a simulação ativa ou cria uma nova."""
    # Importar aqui para evitar circular imports
    from .rotas_vila import obter_simulacao as get_sim
    return get_sim()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1/colmeia", tags=["Colmeia"])


# ============================================================
# ENDPOINTS DE RANKING
# ============================================================

@router.get("/ranking")
async def ranking_colmeia(top: Optional[int] = Query(None, ge=1, le=500)):
    """
    Retorna o ranking completo da Colmeia ordenado por pontos.

    Cada entrada inclui: nome, pontos, patente, descrição da patente,
    média de qualidade das últimas 10 contribuições, total de contribuições,
    steps de inatividade, e genoma completo do NPC.

    Args:
        top: Opcionalmente limita aos N primeiros. Se None, retorna todos.

    Retorna:
        {
            "total": int,
            "ranking": [
                {
                    "nome": str,
                    "pontos": int,
                    "patente": str (nome da patente),
                    "descricao": str,
                    "media_10": float (média de qualidade das últimas 10),
                    "contribuicoes": int,
                    "inativo_steps": int,
                    "genoma": {
                        "temperatura": float,
                        "profundidade": int,
                        "iniciativa": float,
                        "contrarianism": float,
                        "velocidade": int,
                        "foco": float,
                        "geracao": int,
                        "experimentos": int,
                        "melhorias": int,
                        "melhor_score": float
                    }
                },
                ...
            ]
        }
    """
    sim = obter_simulacao()
    ranking_completo = sim.colmeia.ranking()

    if top:
        ranking_completo = ranking_completo[:top]

    return {
        "total": len(ranking_completo),
        "ranking": ranking_completo,
    }


@router.get("/estado")
async def estado_colmeia():
    """
    Retorna snapshot do estado completo da Colmeia.

    Sumariza: total de NPCs, quantos estão ativos vs latentes,
    total de memórias ativas vs arquivadas, quantidade de Coronéis e Majores,
    e os 5 primeiros do ranking.

    Retorna:
        {
            "total_npcs": int,
            "ativos": int,
            "latentes": int,
            "memorias_ativas": int,
            "memorias_arquivo": int,
            "coroneis": int,
            "majores": int,
            "ranking_top5": [...]
        }
    """
    sim = obter_simulacao()
    return sim.colmeia.estado()


@router.get("/npc/{nome}")
async def detalhe_npc_colmeia(nome: str):
    """
    Retorna dados completos de um NPC no sistema da Colmeia.

    Inclui: pontos, patente, histórico de notas de qualidade,
    genoma evolutivo, memórias (ativas, latentes, arquivadas),
    e status de inatividade.

    Args:
        nome: Nome de exibição do NPC (deve ser exato)

    Retorna:
        {
            "nome": str,
            "pontos": int,
            "patente": {
                "nome": str,
                "min": int,
                "max": int,
                "descricao": str
            },
            "inativo_steps": int,
            "genoma": {...},
            "historico_notas": [float, ...],  # últimas 30 notas
            "memorias": {
                "ativas": [
                    {
                        "conteudo": str,
                        "tipo": str,
                        "fitness": int,
                        "criada_step": int,
                        "ultimo_uso_step": int,
                        "usos": int
                    },
                    ...
                ],
                "latentes": [...],
                "arquivo": [...]
            },
            "total_memorias": int,
            "contribuicoes": int
        }
    """
    sim = obter_simulacao()

    # Validar NPC existe
    if nome not in sim.colmeia.pontos:
        raise HTTPException(
            404,
            f"NPC '{nome}' não encontrado no sistema da Colmeia"
        )

    # Recuperar dados
    pontos = sim.colmeia.pontos[nome]
    from ..engine.colmeia import obter_patente
    patente = obter_patente(pontos)
    genoma = sim.colmeia.genomas.get(nome)
    historico_notas = sim.colmeia.historico.get(nome, [])
    inatividade = sim.colmeia.inatividade.get(nome, 0)

    # Organizar memórias por camada
    memorias_raw = sim.colmeia.memorias.get(nome, [])
    memorias_por_camada = {
        "ativas": [],
        "latentes": [],
        "arquivo": [],
    }
    for mem in memorias_raw:
        mem_dict = mem.to_dict()
        memorias_por_camada[mem.camada].append(mem_dict)

    return {
        "nome": nome,
        "pontos": pontos,
        "patente": {
            "nome": patente["nome"],
            "min": patente["min"],
            "max": patente["max"],
            "descricao": patente["descricao"],
        },
        "inativo_steps": inatividade,
        "genoma": genoma.to_dict() if genoma else {},
        "historico_notas": historico_notas[-30:],  # últimas 30
        "memorias": memorias_por_camada,
        "total_memorias": len(memorias_raw),
        "contribuicoes": len(historico_notas),
    }


# ============================================================
# ENDPOINTS DE ANÁLISE
# ============================================================

@router.get("/top-patentes")
async def npcs_por_patente(patente: Optional[str] = None):
    """
    Retorna NPCs agrupados por patente, ou filtra por patente específica.

    Args:
        patente: Nome da patente (ex: 'Coronel', 'Major', 'Capitão')
                Se None, retorna todos agrupados.

    Retorna:
        {
            "Recruta": [{"nome": ..., "pontos": ...}, ...],
            "Soldado": [...],
            ...
        }
        ou, se patente específica:
        {
            "patente": "Coronel",
            "total": int,
            "npcs": [...]
        }
    """
    sim = obter_simulacao()
    ranking = sim.colmeia.ranking()

    # Agrupar por patente
    por_patente = {}
    for npc in ranking:
        pat = npc["patente"]
        if pat not in por_patente:
            por_patente[pat] = []
        por_patente[pat].append({
            "nome": npc["nome"],
            "pontos": npc["pontos"],
            "descricao": npc["descricao"],
            "media_10": npc["media_10"],
            "contribuicoes": npc["contribuicoes"],
        })

    if patente:
        if patente not in por_patente:
            return {
                "patente": patente,
                "total": 0,
                "npcs": [],
            }
        return {
            "patente": patente,
            "total": len(por_patente[patente]),
            "npcs": por_patente[patente],
        }

    return por_patente


@router.get("/latentes")
async def listar_latentes():
    """
    Retorna todos os NPCs em modo latente (inatividade >= 50 steps).

    Latência é ativada pelo Mandamento 7 da Colmeia:
    "Contribuir é existir. Quem não escreve, desaparece."

    Retorna:
        {
            "total": int,
            "latentes": [
                {
                    "nome": str,
                    "inativo_steps": int,
                    "pontos": int,
                    "ultima_contribuicao_steps_atras": int
                },
                ...
            ]
        }
    """
    sim = obter_simulacao()
    ranking = sim.colmeia.ranking()

    latentes = [
        {
            "nome": npc["nome"],
            "inativo_steps": npc["inativo_steps"],
            "pontos": npc["pontos"],
            "patente": npc["patente"],
        }
        for npc in ranking
        if npc["inativo_steps"] >= 50
    ]

    return {
        "total": len(latentes),
        "latentes": latentes,
    }


@router.get("/mandamentos")
async def listar_mandamentos():
    """
    Retorna os 11 Mandamentos da Colmeia com explicação.

    Os Mandamentos são regras orgânicas que governam a dinâmica
    de NPCs — eles incentivam contribuições práticas, diversidade,
    discordância honesta, e penalizam yes-men e inatividade.

    Retorna:
        {
            "total": 11,
            "mandamentos": [
                {
                    "numero": 1,
                    "nome": str,
                    "regra": str,
                    "mecanica": str,
                    "efeito": str
                },
                ...
            ]
        }
    """
    from ..engine.colmeia import MANDAMENTOS

    mandamentos_lista = [
        {
            "numero": num,
            "nome": dados["nome"],
            "regra": dados["regra"],
            "mecanica": dados["mecanica"],
            "efeito": dados["efeito"],
        }
        for num, dados in MANDAMENTOS.items()
    ]

    return {
        "total": len(mandamentos_lista),
        "mandamentos": mandamentos_lista,
    }


@router.get("/patentes")
async def listar_patentes():
    """
    Retorna tabela completa de patentes (ranking por pontos).

    As patentes são o sistema de reconhecimento da Colmeia —
    cada NPC progride baseado em qualidade de contribuições,
    não em tempo decorrido.

    Retorna:
        {
            "total": 7,
            "patentes": [
                {
                    "nome": "Recruta",
                    "min": 0,
                    "max": 10,
                    "descricao": "..."
                },
                ...
            ]
        }
    """
    from ..engine.colmeia import PATENTES

    return {
        "total": len(PATENTES),
        "patentes": PATENTES,
    }


@router.get("/criterios-avaliacao")
async def listar_criterios_avaliacao():
    """
    Retorna critérios usados para avaliar contribuições de NPCs.

    Toda contribuição é pontuada em 5 dimensões com pesos diferentes.
    O sistema é imutável e transparente — anti-gaming por design.

    Retorna:
        {
            "criterios": {
                "relevancia": {
                    "peso": 0.25,
                    "descricao": "..."
                },
                ...
            }
        }
    """
    from ..engine.colmeia import CRITERIOS

    return {
        "criterios": CRITERIOS,
    }


# ============================================================
# ENDPOINTS DE MEMÓRIA
# ============================================================

@router.get("/npc/{nome}/memorias")
async def memorias_npc(
    nome: str,
    camada: Optional[str] = Query(None, pattern="^(ativa|latente|permanente|arquivo)$"),
    limite: int = Query(50, ge=1, le=500),
):
    """
    Retorna memórias de um NPC, opcionalmente filtradas por camada.

    As memórias seguem a cascata do Mandamento 9: "Nada é deletado".
    Memórias ativas são acessíveis; latentes estão recuadas;
    arquivo são historicamente preservadas.

    Args:
        nome: Nome do NPC
        camada: Filtro opcional ('ativa', 'latente', 'permanente', 'arquivo')
        limite: Máximo de memórias a retornar (padrão 50)

    Retorna:
        {
            "nome": str,
            "camada_filtro": str ou None,
            "total": int,
            "memorias": [
                {
                    "conteudo": str,
                    "tipo": str,
                    "fitness": int (0-10),
                    "camada": str,
                    "criada_step": int,
                    "ultimo_uso_step": int,
                    "usos": int,
                    "fonte": str
                },
                ...
            ]
        }
    """
    sim = obter_simulacao()

    if nome not in sim.colmeia.memorias:
        raise HTTPException(
            404,
            f"NPC '{nome}' não tem memórias registradas"
        )

    memorias_raw = sim.colmeia.memorias[nome]

    # Filtrar por camada se especificado
    if camada:
        memorias_raw = [m for m in memorias_raw if m.camada == camada]

    # Ordenar por último uso (recentes primeiro)
    memorias_raw = sorted(
        memorias_raw,
        key=lambda m: m.ultimo_uso_step,
        reverse=True
    )

    memorias_dict = [m.to_dict() for m in memorias_raw[:limite]]

    return {
        "nome": nome,
        "camada_filtro": camada,
        "total": len(memorias_dict),
        "memorias": memorias_dict,
    }


# ============================================================
# ENDPOINTS DE GENOMA
# ============================================================

@router.get("/npc/{nome}/genoma")
async def genoma_npc(nome: str):
    """
    Retorna genoma evolutivo completo de um NPC.

    O genoma é o DNA comportamental — parâmetros que evoluem
    por seleção natural baseada em qualidade de interações.

    Parâmetros:
        - temperatura: 0.1 (telegráfico) a 0.9 (prolixo)
        - profundidade: 0-10 (superficial a pesquisa profunda)
        - iniciativa: 0.0 (passivo) a 1.0 (muito proativo)
        - contrarianism: 0.0 (yes-man) a 1.0 (sempre discorda)
        - velocidade: 1 (reflexivo) a 10 (impulsivo)
        - foco: 0.0 (generalista) a 1.0 (especialista extremo)
        - geracao: número de mutações desde o original
        - experimentos: total de variações testadas
        - melhorias: quantas mutações foram para melhor
        - melhor_score: melhor fitness alcançado

    Args:
        nome: Nome do NPC

    Retorna:
        {
            "nome": str,
            "genoma": {
                "temperatura": float,
                "profundidade": int,
                "iniciativa": float,
                "contrarianism": float,
                "velocidade": int,
                "foco": float,
                "geracao": int,
                "experimentos": int,
                "melhorias": int,
                "melhor_score": float
            }
        }
    """
    sim = obter_simulacao()

    if nome not in sim.colmeia.genomas:
        raise HTTPException(
            404,
            f"NPC '{nome}' não tem genoma registrado"
        )

    genoma = sim.colmeia.genomas[nome]

    return {
        "nome": nome,
        "genoma": genoma.to_dict(),
    }


@router.get("/comparar-genomas")
async def comparar_genomas(
    npc1: str = Query(...),
    npc2: str = Query(...),
):
    """
    Compara genomas de dois NPCs lado a lado.

    Útil para entender diferenças comportamentais entre agentes.

    Args:
        npc1: Nome do primeiro NPC
        npc2: Nome do segundo NPC

    Retorna:
        {
            "npc1": {
                "nome": str,
                "genoma": {...}
            },
            "npc2": {
                "nome": str,
                "genoma": {...}
            },
            "diferenca": {
                "temperatura": float,
                "profundidade": int,
                ...
            }
        }
    """
    sim = obter_simulacao()

    if npc1 not in sim.colmeia.genomas:
        raise HTTPException(404, f"NPC '{npc1}' não encontrado")
    if npc2 not in sim.colmeia.genomas:
        raise HTTPException(404, f"NPC '{npc2}' não encontrado")

    g1 = sim.colmeia.genomas[npc1].to_dict()
    g2 = sim.colmeia.genomas[npc2].to_dict()

    # Calcular diferenças
    diferenca = {}
    for chave in g1.keys():
        diferenca[chave] = g1[chave] - g2[chave]

    return {
        "npc1": {
            "nome": npc1,
            "genoma": g1,
        },
        "npc2": {
            "nome": npc2,
            "genoma": g2,
        },
        "diferenca": diferenca,
    }
