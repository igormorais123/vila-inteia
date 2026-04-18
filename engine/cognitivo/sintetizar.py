"""
SINTETIZAR - Módulo exclusivo INTEIA (não existe no Smallville).

Combina insights de múltiplos agentes para gerar inteligência coletiva.
Quando vários consultores refletem sobre o mesmo tema,
a Síntese produz um relatório multi-perspectiva.

Este é o diferencial da Vila INTEIA: não é apenas simulação,
é geração de inteligência estratégica coletiva.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..memoria.fluxo import NoMemoria
from ..harness import trace_fase


@trace_fase("sintetizar")
def sintetizar(
    personas: dict[str, "Persona"],
    topico: str,
    hora_atual: datetime,
    min_perspectivas: int = 3,
) -> dict | None:
    """
    Sintetiza insights de múltiplos agentes sobre um tópico.

    Retorna None se não há perspectivas suficientes, ou:
    {
        "topico": str,
        "perspectivas": list[dict],
        "convergencias": list[str],
        "divergencias": list[str],
        "sintese": str,
        "recomendacoes": list[str],
        "participantes": list[str],
        "confianca": float,
    }
    """
    # 1. Coletar perspectivas relevantes de cada agente
    perspectivas = []

    for pid, persona in personas.items():
        if not persona.ativo:
            continue

        # Buscar memórias sobre o tópico
        resultados = persona.memoria.recuperar(
            consulta=topico,
            n=5,
            peso_relevancia=2.0,
            peso_importancia=1.5,
            tipos=["pensamento", "insight", "sintese"],
            agora=hora_atual,
        )

        if not resultados:
            continue

        # Extrair a perspectiva mais relevante
        melhor_memoria, score = resultados[0]
        if score < 0.3:
            continue

        perspectivas.append({
            "agente_id": persona.id,
            "agente_nome": persona.nome_exibicao,
            "titulo": persona.titulo,
            "categoria": persona.categoria,
            "tier": persona.tier,
            "descricao": melhor_memoria.descricao,
            "importancia": melhor_memoria.importancia,
            "score": score,
            "expertise": persona.rascunho.areas_expertise[:3],
            "estilo": persona.dados_consultor.get("estilo_pensamento", "analítico"),
        })

    if len(perspectivas) < min_perspectivas:
        return None

    # 2. Ordenar por relevância
    perspectivas.sort(key=lambda p: p["score"], reverse=True)

    # 3. Identificar convergências e divergências
    convergencias, divergencias = _analisar_consenso(perspectivas)

    # 4. Gerar síntese (tenta IA, fallback heurístico)
    sintese = _gerar_sintese_ia(topico, perspectivas, convergencias, divergencias)
    if not sintese:
        sintese = _gerar_sintese(topico, perspectivas, convergencias, divergencias)

    # 5. Gerar recomendações (tenta IA, fallback heurístico)
    recomendacoes = _gerar_recomendacoes_ia(topico, perspectivas, sintese)
    if not recomendacoes:
        recomendacoes = _gerar_recomendacoes(topico, perspectivas, convergencias)

    # 6. Calcular nível de confiança (penaliza echo)
    n_perspectivas = len(perspectivas)
    media_importancia = sum(p["importancia"] for p in perspectivas) / n_perspectivas
    diversidade_categorias = len(set(p["categoria"] for p in perspectivas))
    tem_echo = any("ECHO" in d for d in divergencias)
    penalidade_echo = 0.3 if tem_echo else 0.0
    confianca_bruta = min(
        n_perspectivas / 10 * 0.3 +
        media_importancia / 10 * 0.4 +
        diversidade_categorias / 5 * 0.3,
        1.0
    )
    confianca = max(confianca_bruta - penalidade_echo, 0.05)

    resultado = {
        "topico": topico,
        "perspectivas": perspectivas[:10],
        "convergencias": convergencias,
        "divergencias": divergencias,
        "sintese": sintese,
        "recomendacoes": recomendacoes,
        "participantes": [p["agente_nome"] for p in perspectivas[:10]],
        "confianca": round(confianca, 2),
        "timestamp": hora_atual.isoformat(),
    }

    # 7. Registrar a síntese na memória de cada participante
    for persp in perspectivas[:10]:
        pid = persp["agente_id"]
        if pid in personas:
            personas[pid].memoria.adicionar_pensamento(
                descricao=f"Síntese coletiva sobre '{topico}': {sintese[:100]}",
                importancia=8,
                palavras_chave=set(topico.lower().split()),
            )

    return resultado


def _analisar_consenso(perspectivas: list[dict]) -> tuple[list[str], list[str]]:
    """Identifica convergências, divergências e detecta echo/groupthink."""
    convergencias = []
    divergencias = []

    # Agrupar por categoria/estilo
    por_estilo = {}
    for p in perspectivas:
        estilo = p["estilo"]
        if estilo not in por_estilo:
            por_estilo[estilo] = []
        por_estilo[estilo].append(p)

    # DETECÇÃO DE ECHO: estilo dominante > 60%
    if por_estilo:
        maior_grupo = max(por_estilo.values(), key=len)
        if len(maior_grupo) / len(perspectivas) > 0.6:
            divergencias.append(
                f"ALERTA ECHO: {len(maior_grupo)}/{len(perspectivas)} consultores "
                f"do mesmo estilo ({maior_grupo[0]['estilo']}). Possível groupthink."
            )
        elif len(por_estilo) >= 2:
            estilos = list(por_estilo.keys())
            convergencias.append(
                f"Diversidade real: estilos {', '.join(estilos[:3])} contribuíram"
            )

    # DETECÇÃO DE ECHO: palavras-chave repetidas demais
    todas_palavras = []
    for p in perspectivas:
        palavras = set(p["descricao"].lower().split())
        todas_palavras.append(palavras)
    if len(todas_palavras) >= 3:
        # Jaccard similarity média entre pares
        pares_sim = []
        for i in range(len(todas_palavras)):
            for j in range(i + 1, len(todas_palavras)):
                a, b = todas_palavras[i], todas_palavras[j]
                uniao = a | b
                if uniao:
                    sim = len(a & b) / len(uniao)
                    pares_sim.append(sim)
        if pares_sim:
            media_sim = sum(pares_sim) / len(pares_sim)
            if media_sim > 0.5:
                divergencias.append(
                    f"ALERTA ECHO: similaridade semantica alta ({media_sim:.0%}) "
                    f"entre consultores — estao repetindo as mesmas ideias"
                )

    # Verificar se tiers altos concordam
    tier_s = [p for p in perspectivas if p["tier"] == "S"]
    if len(tier_s) >= 2:
        convergencias.append(
            f"Consultores Tier S ({', '.join(p['agente_nome'] for p in tier_s[:3])}) "
            f"abordaram o tema com alta importância"
        )

    # Divergências por categorias opostas
    categorias = set(p["categoria"] for p in perspectivas)
    pares_divergentes = [
        ("visionario", "estrategia"),
        ("tech", "jurista_lendario"),
        ("lado_negro", "mindset"),
        ("investidor", "resiliencia"),
    ]
    for cat_a, cat_b in pares_divergentes:
        if cat_a in categorias and cat_b in categorias:
            divergencias.append(
                f"Tensão produtiva entre perspectivas de {cat_a} e {cat_b}"
            )

    if not convergencias:
        convergencias.append("Múltiplas perspectivas coletadas sobre o tema")
    if not divergencias:
        divergencias.append("Sem divergências significativas identificadas")

    return convergencias, divergencias


def _gerar_sintese(
    topico: str,
    perspectivas: list[dict],
    convergencias: list[str],
    divergencias: list[str],
) -> str:
    """Gera síntese ACIONÁVEL com conclusão clara, divergências e expertise."""
    n = len(perspectivas)
    categorias = set(p["categoria"] for p in perspectivas)
    top = perspectivas[0]

    # 1. CONCLUSÃO CENTRAL
    convergencias_reais = [c for c in convergencias if "ECHO" not in c]
    divergencias_reais = [d for d in divergencias if "ALERTA" not in d and "Sem divergências" not in d]

    taxa_consenso = len(convergencias_reais) / max(len(convergencias_reais) + len(divergencias_reais), 1)

    if taxa_consenso >= 0.7:
        conclusao = (
            f"CONCLUSÃO ({taxa_consenso:.0%} consenso): "
            f"{convergencias_reais[0] if convergencias_reais else f'{n} consultores concordam sobre {topico}'}."
        )
    else:
        conclusao = (
            f"CONCLUSÃO (debate aberto): Não há consenso sobre '{topico}'. "
            f"Linha de fratura: {divergencias_reais[0] if divergencias_reais else 'múltiplas visões'}."
        )

    # 2. DIVERGÊNCIAS EXPLÍCITAS (quem vs quem)
    div_texto = ""
    if divergencias_reais:
        div_texto = "\nDIVERGÊNCIAS: " + " | ".join(divergencias_reais[:2])

    # 3. ALERTAS (echo/groupthink)
    alertas = [d for d in divergencias if "ALERTA" in d]
    alerta_texto = ""
    if alertas:
        alerta_texto = f"\n⚠ {alertas[0]}"

    # 4. EXPERTISE: quem trouxe o quê
    expertise_items = []
    for p in perspectivas[:3]:
        expertise_list = p.get("expertise", [])
        if expertise_list:
            expertise_items.append(f"{p['agente_nome']} ({expertise_list[0]})")
        else:
            expertise_items.append(f"{p['agente_nome']} ({p['categoria']})")
    expertise_texto = "\nEXPERTISE: " + " | ".join(expertise_items) if expertise_items else ""

    # 5. INSIGHT PRINCIPAL (do consultor mais relevante)
    insight = f"\nINSIGHT ({top['agente_nome']}): \"{top['descricao'][:120]}\""

    return f"{conclusao}{div_texto}{alerta_texto}{expertise_texto}{insight}"


def _gerar_sintese_ia(
    topico: str,
    perspectivas: list[dict],
    convergencias: list[str],
    divergencias: list[str],
) -> str | None:
    """Gera síntese via Helena/Sonnet 4.6. Retorna None se falhar."""
    from ..ia_client import chamar_llm_conversa, MODELO_ANALISE

    # Montar contexto compacto das perspectivas
    persp_txt = "\n".join(
        f"- {p['agente_nome']} ({p['titulo']}, {p['categoria']}): {p['descricao'][:120]}"
        for p in perspectivas[:8]
    )

    system = """Você é Helena Strategos, cientista-chefe da INTEIA.
Sintetize as perspectivas de consultores lendários sobre um tópico.
Seja direta, incisiva, com insight diferencial.
Max 150 palavras. Português do Brasil."""

    user = f"""TÓPICO: {topico}

PERSPECTIVAS ({len(perspectivas)} consultores):
{persp_txt}

CONVERGÊNCIAS: {'; '.join(convergencias[:3])}
DIVERGÊNCIAS: {'; '.join(divergencias[:3])}

Gere uma síntese que:
1. Identifique o ponto central de convergência
2. Destaque a tensão mais produtiva
3. Revele o insight que ninguém mencionou explicitamente"""

    return chamar_llm_conversa(system, user, modelo=MODELO_ANALISE, max_tokens=300)


def _gerar_recomendacoes_ia(
    topico: str,
    perspectivas: list[dict],
    sintese: str,
) -> list[str] | None:
    """Gera recomendações via IA. Retorna None se falhar."""
    from ..ia_client import chamar_llm_conversa, MODELO_RAPIDO

    system = """Gere exatamente 3 recomendações acionáveis baseadas na síntese.
Formato: uma recomendação por linha, sem numeração, sem bullet.
Max 30 palavras cada. Português do Brasil."""

    user = f"TÓPICO: {topico}\nSÍNTESE: {sintese[:300]}"

    resp = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=150)
    if not resp:
        return None

    recs = [l.strip().lstrip("-•*0123456789.) ") for l in resp.strip().split("\n") if l.strip()]
    return recs[:3] if recs else None


def _gerar_recomendacoes(
    topico: str,
    perspectivas: list[dict],
    convergencias: list[str],
) -> list[str]:
    """Gera recomendações ACIONÁVEIS e contextualizadas."""
    recs = []

    # REC 1: Se categorias diferentes → debate produtivo específico
    if len(perspectivas) >= 2:
        top1, top2 = perspectivas[0], perspectivas[1]
        if top1["categoria"] != top2["categoria"]:
            recs.append(
                f"DEBATE: {top1['agente_nome']} (visão {top1['categoria']}) "
                f"vs {top2['agente_nome']} (visão {top2['categoria']}) "
                f"— resolver divergência sobre '{topico}'"
            )

    # REC 2: Se tier S concorda → executar
    tiers_s = [p for p in perspectivas if p.get("tier") == "S"]
    if len(tiers_s) >= 2:
        nomes_s = ", ".join(p["agente_nome"] for p in tiers_s[:3])
        recs.append(
            f"EXECUTAR: {nomes_s} (Tier S) convergem — "
            f"conclusão tem alta confiabilidade para ação imediata"
        )

    # REC 3: Gap de expertise → trazer categoria faltante
    cats_presentes = {p["categoria"] for p in perspectivas}
    cats_importantes = {"tech", "estrategia", "politica_brasileira", "investidor", "mindset"}
    cats_faltantes = cats_importantes - cats_presentes
    if cats_faltantes:
        recs.append(
            f"GAP: Falta perspectiva de {', '.join(list(cats_faltantes)[:2])} "
            f"— incluir na próxima rodada para análise completa"
        )

    # REC 4: Desdobramento
    if not recs:
        recs.append(
            f"APROFUNDAR: Desdobrar '{topico}' em 3 ângulos — "
            f"implementação tática, riscos, e impacto de longo prazo"
        )

    return recs[:3]
