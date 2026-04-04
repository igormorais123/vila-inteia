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
            tipos=None,
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

    # 6. Calcular nível de confiança
    n_perspectivas = len(perspectivas)
    media_importancia = sum(p["importancia"] for p in perspectivas) / n_perspectivas
    diversidade_categorias = len(set(p["categoria"] for p in perspectivas))
    confianca = min(
        (n_perspectivas / 10 * 0.3 +
         media_importancia / 10 * 0.4 +
         diversidade_categorias / 5 * 0.3),
        1.0
    )

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
    """Identifica pontos de convergência e divergência."""
    convergencias = []
    divergencias = []

    # Agrupar por categoria/estilo
    por_estilo = {}
    for p in perspectivas:
        estilo = p["estilo"]
        if estilo not in por_estilo:
            por_estilo[estilo] = []
        por_estilo[estilo].append(p)

    if len(por_estilo) >= 2:
        estilos = list(por_estilo.keys())
        convergencias.append(
            f"Pensadores de estilos {', '.join(estilos[:3])} contribuíram perspectivas"
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
    """Gera texto de síntese."""
    n = len(perspectivas)
    nomes = ", ".join(p["agente_nome"] for p in perspectivas[:5])
    categorias = set(p["categoria"] for p in perspectivas)

    sintese = (
        f"Síntese sobre '{topico}': {n} consultores lendários "
        f"({nomes}{', e outros' if n > 5 else ''}) "
        f"de {len(categorias)} áreas distintas "
        f"contribuíram suas perspectivas. "
    )

    if convergencias:
        sintese += f"Convergências: {convergencias[0]}. "

    if divergencias:
        sintese += f"Tensões identificadas: {divergencias[0]}. "

    # Destaque do consultor mais relevante
    top = perspectivas[0]
    sintese += (
        f"A perspectiva mais relevante veio de {top['agente_nome']} "
        f"({top['titulo']}): \"{top['descricao'][:100]}...\""
    )

    return sintese


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
    """Gera recomendações acionáveis."""
    recs = []

    # Recomendação baseada na expertise coletiva
    todas_expertises = []
    for p in perspectivas[:5]:
        todas_expertises.extend(p.get("expertise", []))

    if todas_expertises:
        top_expertise = max(set(todas_expertises), key=todas_expertises.count)
        recs.append(
            f"Aprofundar análise de '{topico}' com foco em {top_expertise}"
        )

    # Recomendação de debate
    if len(perspectivas) >= 2:
        recs.append(
            f"Organizar debate entre {perspectivas[0]['agente_nome']} "
            f"e {perspectivas[1]['agente_nome']} para aprofundar divergências"
        )

    # Recomendação de síntese
    recs.append(
        f"Documentar as {len(perspectivas)} perspectivas sobre '{topico}' "
        f"para relatório de inteligência INTEIA"
    )

    return recs
