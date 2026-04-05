"""
Problem Solving Engine — 28 tecnicas baseadas em Van Aken & Berends.

Ciclo de 5 fases:
  1. Definicao do Problema
  2. Analise e Diagnostico
  3. Design de Solucao
  4. Intervencao
  5. Avaliacao

+ Tecnicas transversais

Cada tecnica: funcao(simulacao, tema, n_consultores) -> dict com resultados estruturados.
Os consultores da Vila sao selecionados por relevancia de categoria e recebem prompts
especificos da tecnica, respondendo em carater (persona + expertise).
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Optional

from .ia_client import chamar_llm_conversa


# ============================================================
# REGISTRO DE TECNICAS
# ============================================================

TECNICAS = {}


def registrar(fase: str, slug: str, nome: str, descricao: str, categorias_pref: list[str]):
    """Decorator para registrar tecnica no catalogo."""
    def decorator(fn):
        TECNICAS[slug] = {
            "slug": slug,
            "nome": nome,
            "descricao": descricao,
            "fase": fase,
            "categorias_pref": categorias_pref,
            "fn": fn,
        }
        return fn
    return decorator


COMBOS_AREAS = {
    "juridico": {
        "nome": "Juridico",
        "descricao": "Casos judiciais, peticoes, compliance, contratos, litigios",
        "icon": "⚖️",
        "cor": "#f59e0b",
        "tecnicas": ["stakeholder", "cinco_porques", "cbr", "resistencia"],
        "fluxo": "Mapear partes → Causa raiz → Precedentes → Implementar",
        "exemplo_tema": "Empresa recebeu auto de infracao do CADE por pratica anticoncorrencial",
    },
    "eleitoral": {
        "nome": "Eleitoral / Campanha",
        "descricao": "Estrategia de campanha, comunicacao politica, analise de cenarios",
        "icon": "🗳️",
        "cor": "#8b5cf6",
        "tecnicas": ["steepled", "quick_scan", "mcdm", "plano_comunicacao", "piloto"],
        "fluxo": "Macro-contexto → Gaps → Decidir → Comunicar → Testar",
        "exemplo_tema": "Candidato a governador do DF com 12% das intencoes precisa chegar a 25% em 60 dias",
    },
    "educacao": {
        "nome": "Educacao / Politica Publica",
        "descricao": "Reforma curricular, gestao escolar, avaliacao de programas educacionais",
        "icon": "🎓",
        "cor": "#22c55e",
        "tecnicas": ["ssm", "design_thinking", "piloto", "pos_teste", "action_research"],
        "fluxo": "Entender complexidade → Centrar no usuario → Testar → Medir → Co-criar",
        "exemplo_tema": "Evasao de 30% no ensino medio noturno da rede publica do DF",
    },
    "startup": {
        "nome": "Startup / Inovacao",
        "descricao": "Validacao de produto, MVP, pivot, growth, product-market fit",
        "icon": "🚀",
        "cor": "#06b6d4",
        "tecnicas": ["quick_scan", "triz", "idealized_design", "design_thinking", "piloto"],
        "fluxo": "Diagnostico rapido → Inventar → Idealizar → Prototipar → Testar",
        "exemplo_tema": "SaaS de IA juridica com 50 usuarios beta e churn de 40% no primeiro mes",
    },
    "gestao_publica": {
        "nome": "Gestao Publica",
        "descricao": "Reforma administrativa, eficiencia, transparencia, servicos ao cidadao",
        "icon": "🏛️",
        "cor": "#3b82f6",
        "tecnicas": ["steepled", "bpm", "stakeholder", "resistencia", "action_research", "triangulacao"],
        "fluxo": "Contexto macro → Processos → Partes → Resistencia → Co-criar → Validar",
        "exemplo_tema": "Secretaria de Educacao leva 45 dias para processar pedido de transferencia escolar",
    },
    "saude": {
        "nome": "Saude / Gestao Hospitalar",
        "descricao": "Processos hospitalares, qualidade assistencial, gestao de leitos, protocolos clinicos",
        "icon": "🏥",
        "cor": "#ef4444",
        "tecnicas": ["ishikawa", "bpm", "cinco_porques", "piloto", "pos_teste"],
        "fluxo": "Causas raiz → Processo → Profundidade → Testar → Medir",
        "exemplo_tema": "Taxa de infeccao hospitalar 3x acima da media nacional na UTI",
    },
    "pesquisa_academica": {
        "nome": "Pesquisa Academica",
        "descricao": "Doutorado, artigos, teses, revisao sistematica, metodologia cientifica",
        "icon": "📚",
        "cor": "#a855f7",
        "tecnicas": ["revisao_literatura", "snowball", "triangulacao", "member_check"],
        "fluxo": "Evidencia → Expandir → Validar → Confirmar",
        "exemplo_tema": "Revisao sistematica sobre impacto de IA generativa na administracao publica (2020-2025)",
    },
    "crise": {
        "nome": "Crise / Urgencia",
        "descricao": "Problema grave com deadline, incidente critico, emergencia operacional",
        "icon": "🚨",
        "cor": "#dc2626",
        "tecnicas": ["quick_scan", "cinco_porques", "causa_efeito", "plano_comunicacao", "pos_teste"],
        "fluxo": "Rapido → Causa raiz → Estruturar → Comunicar → Medir",
        "exemplo_tema": "Vazamento de dados de 50 mil clientes descoberto ha 2 horas — LGPD exige notificacao em 72h",
    },
}


def listar_combos() -> dict:
    """Retorna catalogo de combos por area."""
    return {
        slug: {
            "slug": slug,
            "nome": c["nome"],
            "descricao": c["descricao"],
            "icon": c["icon"],
            "cor": c["cor"],
            "tecnicas": c["tecnicas"],
            "fluxo": c["fluxo"],
            "exemplo_tema": c["exemplo_tema"],
        }
        for slug, c in COMBOS_AREAS.items()
    }


def executar_combo(simulacao, area_slug: str, tema: str, n_consultores: int = 5) -> dict:
    """Executa sequencia de tecnicas de uma area, passando contexto entre elas."""
    if area_slug not in COMBOS_AREAS:
        return {"erro": f"Area '{area_slug}' nao encontrada. Disponiveis: {list(COMBOS_AREAS.keys())}"}

    combo = COMBOS_AREAS[area_slug]
    resultados = []
    contexto_acumulado = ""
    tempo_total = 0

    for i, slug in enumerate(combo["tecnicas"]):
        if slug not in TECNICAS:
            continue
        # Enriquecer tema com contexto das fases anteriores
        tema_enriquecido = tema
        if contexto_acumulado:
            tema_enriquecido = (
                f"{tema}\n\n"
                f"--- CONTEXTO DAS FASES ANTERIORES ---\n"
                f"{contexto_acumulado[-1500:]}"
            )
        start = time.time()
        t = TECNICAS[slug]
        try:
            resultado = t["fn"](simulacao, tema_enriquecido, n_consultores)
        except Exception as e:
            resultado = {
                "contribuicoes": [],
                "sintese": f"[Erro na execucao: {str(e)[:200]}]",
            }
        metricas = _calcular_metricas(resultado.get("contribuicoes", []), resultado.get("sintese", ""))
        elapsed = round(time.time() - start, 1)
        tempo_total += elapsed

        resultado["meta"] = {
            "tecnica": t["nome"],
            "slug": slug,
            "fase": t["fase"],
            "tema": tema,
            "n_consultores": n_consultores,
            "tempo_segundos": elapsed,
            "passo": i + 1,
            "total_passos": len(combo["tecnicas"]),
        }
        resultado["metricas"] = metricas
        resultados.append(resultado)

        # Acumular contexto para proximo passo
        sintese = resultado.get("sintese", "")
        if sintese:
            contexto_acumulado += f"\n[{t['nome']}]: {sintese[:500]}\n"

    # Sintese final do combo
    todas_sinteses = "\n".join(
        f"Fase {r['meta']['passo']}/{r['meta']['total_passos']} - {r['meta']['tecnica']}:\n{r.get('sintese', '')[:400]}"
        for r in resultados
    )
    try:
        sintese_final = chamar_llm_conversa(
            "Voce e o sintetizador estrategico da INTEIA. "
            f"Um combo de {len(resultados)} tecnicas de Problem Solving foi aplicado na area '{combo['nome']}' "
            f"seguindo o fluxo: {combo['fluxo']}.\n"
            "Produza uma SINTESE EXECUTIVA FINAL integrando todos os resultados.\n"
            "FORMATO:\n"
            "1. DIAGNOSTICO INTEGRADO: visao holistica do problema\n"
            "2. RECOMENDACOES PRIORIZADAS: top 3-5 acoes concretas com responsavel e prazo\n"
            "3. RISCOS E MITIGACOES: principais riscos e como reduzir\n"
            "4. PROXIMO PASSO IMEDIATO: acao #1 para segunda-feira\n"
            "5. NIVEL DE CONFIANCA: 0-100% com justificativa\n"
            "Seja CONCRETO com dados e numeros. Maximo 500 palavras.",
            f"TEMA: {tema}\n\nRESULTADOS DAS TECNICAS:\n{todas_sinteses}",
            modelo="rapido",
            max_tokens=800,
        )
    except Exception:
        sintese_final = None

    if not sintese_final:
        sintese_final = (
            "SINTESE AUTOMATICA (fallback):\n"
            + "\n".join(
                f"- {r['meta']['tecnica']}: {r.get('sintese', '(sem sintese)')[:200]}"
                for r in resultados
            )
        )

    return {
        "area": combo["nome"],
        "area_slug": area_slug,
        "fluxo": combo["fluxo"],
        "tema": tema,
        "resultados": resultados,
        "sintese_final": sintese_final,
        "meta": {
            "area": combo["nome"],
            "tecnicas_executadas": len(resultados),
            "total_tecnicas": len(combo["tecnicas"]),
            "tempo_total_segundos": round(tempo_total, 1),
            "n_consultores": n_consultores,
            "timestamp": datetime.now().isoformat(),
        },
    }


def listar_tecnicas() -> dict:
    """Retorna catalogo agrupado por fase."""
    fases = {
        "definicao": {"nome": "Definicao do Problema", "ordem": 1, "tecnicas": []},
        "diagnostico": {"nome": "Analise e Diagnostico", "ordem": 2, "tecnicas": []},
        "solucao": {"nome": "Design de Solucao", "ordem": 3, "tecnicas": []},
        "intervencao": {"nome": "Intervencao", "ordem": 4, "tecnicas": []},
        "avaliacao": {"nome": "Avaliacao", "ordem": 5, "tecnicas": []},
        "transversal": {"nome": "Transversais", "ordem": 6, "tecnicas": []},
    }
    for slug, t in TECNICAS.items():
        fase = t["fase"]
        if fase in fases:
            fases[fase]["tecnicas"].append({
                "slug": slug,
                "nome": t["nome"],
                "descricao": t["descricao"],
            })
    return fases


def executar_tecnica(simulacao, slug: str, tema: str, n_consultores: int = 5) -> dict:
    """Despacha para a tecnica correta."""
    if slug not in TECNICAS:
        return {"erro": f"Tecnica '{slug}' nao encontrada. Disponiveis: {list(TECNICAS.keys())}"}
    t = TECNICAS[slug]
    start = time.time()
    resultado = t["fn"](simulacao, tema, n_consultores)
    # Calcular metricas de qualidade
    metricas = _calcular_metricas(resultado.get("contribuicoes", []), resultado.get("sintese", ""))
    resultado["meta"] = {
        "tecnica": t["nome"],
        "slug": slug,
        "fase": t["fase"],
        "tema": tema,
        "n_consultores": n_consultores,
        "tempo_segundos": round(time.time() - start, 1),
        "timestamp": datetime.now().isoformat(),
    }
    resultado["metricas"] = metricas
    return resultado


# ============================================================
# HELPERS
# ============================================================

def _selecionar_agentes(simulacao, n: int, categorias_pref: list[str]):
    """Seleciona agentes priorizando categorias relevantes."""
    todos = list(simulacao.personas.values())
    if not todos:
        return []

    # Priorizar agentes das categorias preferidas
    prioritarios = [p for p in todos if p.categoria in categorias_pref and p.ativo]
    outros = [p for p in todos if p.categoria not in categorias_pref and p.ativo]

    pool = prioritarios + outros
    if not pool:
        pool = todos

    return random.sample(pool, min(n, len(pool)))


def _consultar_agentes(agentes, system_template: str, user_prompt: str, max_tokens: int = 400) -> list[dict]:
    """Consulta N agentes com prompts personalizados e retorna contribuicoes."""
    contribuicoes = []
    for ag in agentes:
        areas = ", ".join(ag.rascunho.areas_expertise[:3]) if hasattr(ag.rascunho, "areas_expertise") else "analise geral"
        system = system_template.format(
            nome=ag.nome_exibicao,
            titulo=ag.titulo,
            categoria=ag.categoria,
            areas=areas,
        )
        resp = chamar_llm_conversa(system, user_prompt, modelo="rapido", max_tokens=max_tokens)
        if resp:
            contribuicoes.append({
                "agente_id": ag.id,
                "agente_nome": ag.nome_exibicao,
                "titulo": ag.titulo,
                "categoria": ag.categoria,
                "resposta": resp,
            })
    return contribuicoes


def _sintetizar(contribuicoes: list[dict], tema: str, tecnica_nome: str) -> str:
    """Gera sintese executiva a partir das contribuicoes."""
    todas = "\n".join(
        f"- {c['agente_nome']} ({c['categoria']}): {c['resposta'][:400]}"
        for c in contribuicoes
    )
    return chamar_llm_conversa(
        "Voce e o sintetizador estrategico da INTEIA. Produza uma sintese EXECUTIVA "
        f"da tecnica '{tecnica_nome}' aplicada ao tema abaixo. "
        "FORMATO OBRIGATORIO:\n"
        "1. CONVERGENCIA: onde os consultores concordam (2-3 pontos)\n"
        "2. DIVERGENCIA: onde discordam e por que\n"
        "3. INSIGHT DIFERENCIAL: o que so esse painel combinado revelaria\n"
        "4. RECOMENDACAO ACIONAVEL: 3 acoes concretas priorizadas por impacto\n"
        "5. NIVEL DE CONFIANCA: Alta/Media/Baixa + justificativa\n"
        "Max 350 palavras. Portugues.",
        f"Tema: {tema}\n\nContribuicoes:\n{todas}",
        modelo="rapido",
        max_tokens=700,
    ) or "Sintese nao disponivel."


def _calcular_metricas(contribuicoes: list[dict], sintese: str) -> dict:
    """
    Indicadores anti-trapaca: medem qualidade REAL, nao apenas quantidade.

    Principios anti-dissimulacao:
    1. Medir ESTRUTURA (a tecnica foi seguida?) nao apenas tamanho
    2. Medir ESPECIFICIDADE (dados concretos?) nao apenas fluencia
    3. Medir DIVERGENCIA (consultores discordam?) nao apenas concordancia
    4. Medir UNICIDADE (respostas sao diferentes entre si?) nao copias
    5. Todos os indicadores sao verificaveis por humano em <30s
    """
    import re

    n = len(contribuicoes)
    if n == 0:
        return _metricas_zeradas()

    respostas = [c["resposta"] for c in contribuicoes]
    cats = set(c["categoria"] for c in contribuicoes)

    # ===== 1. ADERENCIA ESTRUTURAL (a tecnica foi aplicada?) =====
    # Verifica se a resposta segue o formato pedido pela tecnica
    # Conta marcadores estruturais: headers (#), listas (1. ou -), labels (MAIUSCULAS:)
    marcadores_por_resp = []
    for r in respostas:
        headers = len(re.findall(r'^#{1,3}\s', r, re.MULTILINE))
        listas = len(re.findall(r'^\s*[\d]+[.)]\s|^\s*[-*]\s', r, re.MULTILINE))
        labels = len(re.findall(r'^[A-Z][A-Z\s]{2,}:', r, re.MULTILINE))
        marcadores_por_resp.append(headers + listas + labels)
    aderencia = round(sum(1 for m in marcadores_por_resp if m >= 3) / n, 2)

    # ===== 2. ESPECIFICIDADE (dados concretos, nao genericos) =====
    # Conta: numeros, percentuais, nomes proprios (Maiusculas), datas, valores R$
    espec_por_resp = []
    for r in respostas:
        numeros = len(re.findall(r'\d+[%,.]?\d*', r))
        nomes_proprios = len(re.findall(r'\b[A-Z][a-záéíóúâêôãõç]+(?:\s[A-Z][a-záéíóúâêôãõç]+)*\b', r))
        valores = len(re.findall(r'R\$\s?[\d.,]+|US\$\s?[\d.,]+|\d+\s?(?:mil|milhao|bi)', r, re.IGNORECASE))
        total = numeros + nomes_proprios + valores
        espec_por_resp.append(total)
    especificidade = round(sum(1 for e in espec_por_resp if e >= 5) / n, 2)

    # ===== 3. UNICIDADE (respostas diferentes entre si?) =====
    # Compara pares de respostas: se muito similares, flag de copia/template
    def _similaridade_simples(a, b):
        """Jaccard de palavras — robusto e sem dependencia externa."""
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return 0
        return len(wa & wb) / len(wa | wb)

    pares_sim = []
    for i in range(n):
        for j in range(i + 1, n):
            pares_sim.append(_similaridade_simples(respostas[i], respostas[j]))
    sim_media = sum(pares_sim) / max(len(pares_sim), 1) if pares_sim else 0
    # Unicidade: 1.0 se respostas muito diferentes, 0.0 se copias
    unicidade = round(max(0, 1.0 - sim_media * 2), 2)

    # ===== 4. DIVERGENCIA (tem discordancia real?) =====
    # Verifica se a sintese menciona divergencia/discordancia
    div_keywords = ["divergen", "discorda", "contrari", "oposto", "diferent", "nao concorda",
                    "contra-argum", "ressalva", "porem", "entretanto", "no entanto"]
    sintese_lower = (sintese or "").lower()
    divergencia_encontrada = sum(1 for k in div_keywords if k in sintese_lower)
    divergencia = round(min(divergencia_encontrada / 3, 1.0), 2)

    # ===== 5. COMPLETUDE SUBSTANCIAL (nao apenas tamanho) =====
    # Resposta >100 chars E com estrutura E com dados = completa
    completas = sum(
        1 for i, r in enumerate(respostas)
        if len(r) > 150 and marcadores_por_resp[i] >= 2 and espec_por_resp[i] >= 3
    )
    completude = round(completas / n, 2)

    # ===== 6. DIVERSIDADE DE PERSPECTIVA =====
    diversidade = round(len(cats) / max(n, 1), 2)

    # ===== 7. COBERTURA DA SINTESE =====
    # Sintese deve mencionar pelo menos 50% dos consultores pelo nome
    nomes_na_sintese = sum(1 for c in contribuicoes if c["agente_nome"].split()[0] in (sintese or ""))
    cob_nomes = round(nomes_na_sintese / n, 2) if n > 0 else 0
    cob_tamanho = 1.0 if sintese and len(sintese) > 300 else 0.5 if sintese and len(sintese) > 100 else 0.0
    cobertura = round((cob_nomes * 0.5 + cob_tamanho * 0.5), 2)

    # ===== SCORE COMPOSTO (ponderado, dificil de manipular) =====
    # Peso maior nos indicadores mais dificeis de falsificar
    score = round((
        aderencia * 0.20 +        # Seguiu a estrutura da tecnica?
        especificidade * 0.20 +    # Tem dados concretos?
        unicidade * 0.20 +         # Respostas sao unicas?
        divergencia * 0.10 +       # Existe discordancia real?
        completude * 0.15 +        # Substancialmente completo?
        diversidade * 0.05 +       # Categorias diferentes?
        cobertura * 0.10           # Sintese integra todos?
    ) * 10, 1)

    # ===== FLAGS ANTI-TRAPACA =====
    flags = []
    if sim_media > 0.4:
        flags.append("ALERTA: respostas muito similares entre si (possivel template)")
    if especificidade < 0.3:
        flags.append("ALERTA: respostas genericas sem dados concretos")
    if aderencia < 0.3:
        flags.append("ALERTA: tecnica nao foi seguida estruturalmente")
    if divergencia == 0:
        flags.append("ALERTA: zero divergencia — possivel pensamento de grupo")
    if any(len(r) < 80 for r in respostas):
        flags.append("ALERTA: resposta(s) suspeitamente curta(s)")

    return {
        "score_qualidade": score,
        "aderencia_estrutural": aderencia,
        "especificidade_dados": especificidade,
        "unicidade_respostas": unicidade,
        "divergencia_real": divergencia,
        "completude_substancial": completude,
        "diversidade_categorias": diversidade,
        "cobertura_sintese": cobertura,
        "categorias_representadas": list(cats),
        "profundidade_media_chars": round(sum(len(r) for r in respostas) / n),
        "similaridade_media_pares": round(sim_media, 3),
        "total_contribuicoes": n,
        "flags_anti_trapaca": flags,
        "verificavel_humano": True,
    }


def _metricas_zeradas():
    return {
        "score_qualidade": 0, "aderencia_estrutural": 0, "especificidade_dados": 0,
        "unicidade_respostas": 0, "divergencia_real": 0, "completude_substancial": 0,
        "diversidade_categorias": 0, "cobertura_sintese": 0, "categorias_representadas": [],
        "profundidade_media_chars": 0, "similaridade_media_pares": 0, "total_contribuicoes": 0,
        "flags_anti_trapaca": ["SEM DADOS"], "verificavel_humano": True,
    }


_SYS = (
    "Voce e {nome}, {titulo}. Especialidades: {areas}. "
    "REGRAS: (1) Responda EM CARATER como voce mesmo — use seu estilo, vocabulario e perspectiva unicos. "
    "(2) Inclua DADOS CONCRETOS: numeros, percentuais, exemplos reais, nomes de empresas/casos. "
    "(3) Seja ESPECIFICO ao tema — nao generalize. "
    "(4) Max 250 palavras. Portugues do Brasil."
)


# ============================================================
# FASE 1 — DEFINICAO DO PROBLEMA
# ============================================================

@registrar("definicao", "causa_efeito", "Arvore de Causa-Efeito",
    "Mapeia causas raiz e efeitos de um problema em estrutura hierarquica",
    ["estrategia", "qi_extremo", "mindset", "visionario"])
def causa_efeito(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["causa_efeito"]["categorias_pref"])
    prompt = (
        f"Construa uma Arvore de Causa-Efeito para o problema: {tema}\n\n"
        "Formato:\n"
        "PROBLEMA CENTRAL: [descreva]\n"
        "CAUSAS RAIZ (nivel 1):\n  1. [causa] -> subcausa a, subcausa b\n  2. ...\n"
        "EFEITOS:\n  1. [efeito direto] -> [efeito secundario]\n  2. ...\n"
        "CAUSA RAIZ PRIORITARIA: [qual atacar primeiro e por que]"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Arvore de Causa-Efeito")}


@registrar("definicao", "steepled", "Analise STEEPLED",
    "Scan macro-ambiental: Social, Tecnologico, Economico, Ecologico, Politico, Legal, Etico, Demografico",
    ["estrategia", "investidor", "lado_negro", "visionario"])
def steepled(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["steepled"]["categorias_pref"])
    prompt = (
        f"Faca uma analise STEEPLED completa para: {tema}\n\n"
        "Cubra TODOS os 8 fatores:\n"
        "S - Social: tendencias sociais que afetam\n"
        "T - Tecnologico: mudancas tecnologicas relevantes\n"
        "E - Economico: fatores economicos de impacto\n"
        "E - Ecologico/Ambiental: questoes ambientais\n"
        "P - Politico: cenario politico e regulatorio\n"
        "L - Legal: marcos legais aplicaveis\n"
        "E - Etico: dilemas eticos envolvidos\n"
        "D - Demografico: mudancas populacionais\n\n"
        "Para cada fator: tendencia + impacto (alto/medio/baixo) + horizonte temporal."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "STEEPLED")}


@registrar("definicao", "stakeholder", "Analise de Stakeholders",
    "Mapeia partes interessadas, interesses, poder e estrategia de engajamento",
    ["estrategia", "negociacao", "lado_negro", "investidor"])
def stakeholder(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["stakeholder"]["categorias_pref"])
    prompt = (
        f"Faca uma Analise de Stakeholders para: {tema}\n\n"
        "Para cada stakeholder identifique:\n"
        "1. NOME/GRUPO\n"
        "2. INTERESSE: o que querem?\n"
        "3. PODER: alto/medio/baixo\n"
        "4. POSICAO: apoiador/neutro/opositor\n"
        "5. ESTRATEGIA: como engajar?\n\n"
        "Identifique pelo menos 5 stakeholders. Inclua uma matriz Poder x Interesse."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Stakeholder Analysis")}


@registrar("definicao", "quick_scan", "Quick Scan",
    "Analise rapida de desempenho: identifica gaps e oportunidades em minutos",
    ["estrategia", "investidor", "visionario", "qi_extremo"])
def quick_scan(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["quick_scan"]["categorias_pref"])
    prompt = (
        f"Quick Scan — analise rapida de desempenho para: {tema}\n\n"
        "Avalie em 4 dimensoes:\n"
        "1. DESEMPENHO ATUAL: como esta hoje? (nota 1-10 + justificativa)\n"
        "2. BENCHMARK: como estao os melhores do setor?\n"
        "3. GAPS: quais as maiores lacunas?\n"
        "4. QUICK WINS: o que pode ser melhorado IMEDIATAMENTE (< 30 dias)?\n\n"
        "Seja especifico com numeros e exemplos concretos."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Quick Scan")}


# ============================================================
# FASE 2 — ANALISE E DIAGNOSTICO
# ============================================================

@registrar("diagnostico", "ishikawa", "Diagrama de Ishikawa (Espinha de Peixe)",
    "Identifica causas raiz organizadas por categorias (6M: Mao de obra, Metodo, Material, Maquina, Medida, Meio)",
    ["estrategia", "qi_extremo", "tech", "mindset"])
def ishikawa(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["ishikawa"]["categorias_pref"])
    prompt = (
        f"Construa um Diagrama de Ishikawa (Fishbone) para: {tema}\n\n"
        "EFEITO (cabeca do peixe): [defina o problema]\n\n"
        "ESPINHAS (categorias de causa):\n"
        "1. MAO DE OBRA: pessoas, competencias, motivacao\n"
        "2. METODO: processos, procedimentos, politicas\n"
        "3. MATERIAL: insumos, dados, informacoes\n"
        "4. MAQUINA: tecnologia, equipamentos, ferramentas\n"
        "5. MEDIDA: metricas, indicadores, monitoramento\n"
        "6. MEIO AMBIENTE: cultura, contexto, regulacao\n\n"
        "Para cada categoria liste 2-3 causas especificas. Destaque a causa raiz mais provavel."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Ishikawa")}


@registrar("diagnostico", "incidente_critico", "Tecnica do Incidente Critico",
    "Analisa eventos decisivos (positivos e negativos) para extrair padroes",
    ["estrategia", "lado_negro", "mindset", "negociacao"])
def incidente_critico(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["incidente_critico"]["categorias_pref"])
    prompt = (
        f"Aplique a Tecnica do Incidente Critico para: {tema}\n\n"
        "Identifique 3 incidentes criticos (momentos decisivos):\n\n"
        "Para cada incidente:\n"
        "- CONTEXTO: o que estava acontecendo?\n"
        "- ACAO: o que foi feito (ou deixou de ser feito)?\n"
        "- RESULTADO: qual foi o impacto?\n"
        "- LICAO: que padrao emerge deste incidente?\n\n"
        "Inclua pelo menos 1 incidente positivo e 1 negativo."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Incidente Critico")}


@registrar("diagnostico", "bpm", "Modelagem de Processos de Negocio",
    "Mapeia o processo atual (AS-IS) e propoe o processo ideal (TO-BE)",
    ["tech", "estrategia", "ia_futuro", "visionario"])
def bpm(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["bpm"]["categorias_pref"])
    prompt = (
        f"Modele o processo de negocio para: {tema}\n\n"
        "PROCESSO AS-IS (atual):\n"
        "1. [Etapa] -> [Responsavel] -> [Tempo estimado] -> [Gargalo?]\n"
        "2. ...\n\n"
        "GARGALOS IDENTIFICADOS: [liste os 3 principais]\n\n"
        "PROCESSO TO-BE (proposto):\n"
        "1. [Etapa otimizada] -> [O que muda] -> [Ganho esperado]\n"
        "2. ...\n\n"
        "GANHO ESTIMADO: [reducao de tempo, custo ou erro em %]"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "BPM")}


@registrar("diagnostico", "cinco_porques", "5 Porques",
    "Iteracao de 'por que?' ate chegar na causa raiz real",
    ["qi_extremo", "mindset", "estrategia", "visionario"])
def cinco_porques(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["cinco_porques"]["categorias_pref"])
    prompt = (
        f"Aplique a tecnica dos 5 Porques para: {tema}\n\n"
        "PROBLEMA: [reformule o problema com precisao]\n\n"
        "POR QUE 1? [resposta] -> evidencia\n"
        "POR QUE 2? [resposta] -> evidencia\n"
        "POR QUE 3? [resposta] -> evidencia\n"
        "POR QUE 4? [resposta] -> evidencia\n"
        "POR QUE 5? [resposta] -> evidencia\n\n"
        "CAUSA RAIZ IDENTIFICADA: [sintese]\n"
        "ACAO CORRETIVA SUGERIDA: [o que fazer na raiz]"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "5 Porques")}


@registrar("diagnostico", "ssm", "Soft Systems Methodology",
    "Abordagem para problemas mal-estruturados (wicked problems) via visoes de mundo",
    ["visionario", "mindset", "ficticio", "estrategia"])
def ssm(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["ssm"]["categorias_pref"])
    prompt = (
        f"Aplique Soft Systems Methodology (Checkland) para: {tema}\n\n"
        "1. SITUACAO PROBLEMATICA: descreva a 'bagunca' sem simplificar\n"
        "2. RICH PICTURE: que atores, processos e tensoes existem?\n"
        "3. ROOT DEFINITION (CATWOE):\n"
        "   - C (Clientes): quem se beneficia?\n"
        "   - A (Atores): quem executa?\n"
        "   - T (Transformacao): que mudanca desejamos?\n"
        "   - W (Weltanschauung): que visao de mundo sustenta?\n"
        "   - O (Owner): quem pode parar/autorizar?\n"
        "   - E (Environment): restricoes do contexto\n"
        "4. MODELO CONCEITUAL: atividades necessarias para a transformacao\n"
        "5. COMPARACAO: modelo vs. realidade — onde ha lacunas?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "SSM")}


# ============================================================
# FASE 3 — DESIGN DE SOLUCAO
# ============================================================

@registrar("solucao", "idealized_design", "Idealized Design (Ackoff)",
    "Projeta a solucao ideal sem restricoes, depois retroage para o viavel",
    ["visionario", "ia_futuro", "ficticio", "tech"])
def idealized_design(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["idealized_design"]["categorias_pref"])
    prompt = (
        f"Aplique Idealized Design (Russell Ackoff) para: {tema}\n\n"
        "PASSO 1 — DESTRUICAO SELETIVA: o que do sistema atual voce eliminaria?\n"
        "PASSO 2 — DESIGN IDEALIZADO: se pudesse comecar do zero SEM RESTRICOES, "
        "como seria o sistema ideal? Descreva em detalhes.\n"
        "PASSO 3 — RESTRICOES REAIS: quais limitacoes existem de fato?\n"
        "PASSO 4 — APROXIMACAO: como chegar o mais perto possivel do ideal "
        "respeitando as restricoes? Liste 3 acoes concretas."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Idealized Design")}


@registrar("solucao", "triz", "TRIZ (Resolucao Inventiva de Problemas)",
    "40 principios inventivos para superar contradicoes tecnicas e fisicas",
    ["tech", "ia_futuro", "qi_extremo", "visionario"])
def triz(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["triz"]["categorias_pref"])
    prompt = (
        f"Aplique TRIZ (Altshuller) para resolver: {tema}\n\n"
        "1. CONTRADICAO TECNICA: o que melhora vs. o que piora quando tentamos resolver?\n"
        "   - Parametro que queremos melhorar: __\n"
        "   - Parametro que piora: __\n\n"
        "2. PRINCIPIOS INVENTIVOS aplicaveis (escolha 3 dos 40 principios TRIZ):\n"
        "   - Principio N: [nome] -> como aplicar aqui\n\n"
        "3. SOLUCAO INVENTIVA proposta: como superar a contradicao?\n\n"
        "4. RECURSO IDEAL: que recurso ja existe no sistema que podemos explorar?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "TRIZ")}


@registrar("solucao", "design_thinking", "Design Thinking",
    "Empatia, Definicao, Ideacao, Prototipagem, Teste — centrado no usuario",
    ["marca", "visionario", "mkt_digital", "ficticio"])
def design_thinking(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["design_thinking"]["categorias_pref"])
    prompt = (
        f"Aplique Design Thinking (5 fases) para: {tema}\n\n"
        "1. EMPATIZAR: quem e o usuario? Quais suas dores e desejos reais?\n"
        "2. DEFINIR: reformule o problema como 'Como poderiamos...' (HMW)?\n"
        "3. IDEAR: liste 5 solucoes criativas (quantidade > qualidade)\n"
        "4. PROTOTIPAR: como testar a melhor ideia com custo minimo em 1 semana?\n"
        "5. TESTAR: que perguntas fazer ao usuario? Que metrica define sucesso?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Design Thinking")}


@registrar("solucao", "appreciative_inquiry", "Investigacao Apreciativa",
    "Foca no que funciona bem para amplificar (4D: Discover, Dream, Design, Destiny)",
    ["mindset", "visionario", "marca", "ficticio"])
def appreciative_inquiry(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["appreciative_inquiry"]["categorias_pref"])
    prompt = (
        f"Aplique Investigacao Apreciativa (Cooperrider) para: {tema}\n\n"
        "1. DISCOVERY (Descoberta): o que ja funciona BEM? Quais os pontos fortes?\n"
        "2. DREAM (Sonho): como seria o cenario ideal se amplificassemos o que funciona?\n"
        "3. DESIGN (Desenho): que estruturas e processos sustentariam esse sonho?\n"
        "4. DESTINY (Destino): que acoes concretas iniciar AGORA para chegar la?\n\n"
        "Foco: construir sobre forcas, nao consertar fraquezas."
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Investigacao Apreciativa")}


@registrar("solucao", "mcdm", "Decisao Multicriterio",
    "Avalia alternativas com multiplos criterios ponderados (AHP/MCDM)",
    ["estrategia", "investidor", "qi_extremo", "negociacao"])
def mcdm(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["mcdm"]["categorias_pref"])
    prompt = (
        f"Aplique Decisao Multicriterio (MCDM) para: {tema}\n\n"
        "1. ALTERNATIVAS: liste 3-4 opcoes viaveis\n"
        "2. CRITERIOS: defina 4-5 criterios de avaliacao com PESOS (somando 100%)\n"
        "3. MATRIZ DE DECISAO:\n"
        "   | Alternativa | Criterio 1 (peso%) | Criterio 2 (peso%) | ... | TOTAL |\n"
        "   Pontue cada alternativa em cada criterio (1-10)\n"
        "4. RECOMENDACAO: qual alternativa vence e por que?\n"
        "5. SENSIBILIDADE: mudando os pesos, o resultado mudaria?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "MCDM")}


@registrar("solucao", "cbr", "Raciocinio Baseado em Casos",
    "Busca solucoes em casos similares do passado (analogias estrategicas)",
    ["estrategia", "investidor", "lado_negro", "visionario"])
def cbr(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["cbr"]["categorias_pref"])
    prompt = (
        f"Aplique Raciocinio Baseado em Casos para: {tema}\n\n"
        "Identifique 3 CASOS ANALOGOS (historicos ou de outros setores):\n\n"
        "Para cada caso:\n"
        "- CASO: [descricao breve da situacao similar]\n"
        "- SOLUCAO ADOTADA: o que foi feito?\n"
        "- RESULTADO: funcionou? Por que?\n"
        "- ADAPTACAO: como adaptar essa solucao para o contexto atual?\n\n"
        "RECOMENDACAO FINAL: qual caso e mais transferivel e por que?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "CBR")}


# ============================================================
# FASE 4 — INTERVENCAO
# ============================================================

@registrar("intervencao", "resistencia", "Analise de Resistencia",
    "Mapeia fontes de resistencia a mudanca e estrategias para supera-las",
    ["negociacao", "lado_negro", "mindset", "estrategia"])
def resistencia(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["resistencia"]["categorias_pref"])
    prompt = (
        f"Analise as resistencias para implementar: {tema}\n\n"
        "1. FONTES DE RESISTENCIA (Kotter):\n"
        "   - Racional: falta de informacao, discordancia logica\n"
        "   - Emocional: medo, perda de status, inseguranca\n"
        "   - Politica: perda de poder, conflito de interesses\n\n"
        "2. MAPA DE FORCAS (Lewin): forcas a favor vs. contra (com intensidade 1-5)\n\n"
        "3. ESTRATEGIAS DE SUPERACAO para cada fonte:\n"
        "   - Educacao, Participacao, Facilitacao, Negociacao, Cooptacao, Coercao\n\n"
        "4. PLANO DE ACAO: 3 passos priorizados por impacto"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Analise de Resistencia")}


@registrar("intervencao", "plano_comunicacao", "Plano de Comunicacao",
    "Define mensagens, canais, audiencias e cronograma de comunicacao da mudanca",
    ["marca", "mkt_digital", "negociacao", "estrategia"])
def plano_comunicacao(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["plano_comunicacao"]["categorias_pref"])
    prompt = (
        f"Crie um Plano de Comunicacao para: {tema}\n\n"
        "Para cada AUDIENCIA-CHAVE:\n"
        "1. QUEM: grupo/persona\n"
        "2. MENSAGEM-CHAVE: o que precisa ouvir (max 1 frase)\n"
        "3. CANAL: como recebe melhor (email, reuniao, WhatsApp, etc)\n"
        "4. TIMING: quando comunicar\n"
        "5. RESPONSAVEL: quem comunica\n\n"
        "Inclua pelo menos 4 audiencias diferentes.\n"
        "RISCO COMUNICACIONAL: o que pode dar errado na mensagem?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Plano de Comunicacao")}


@registrar("intervencao", "piloto", "Implementacao Piloto",
    "Desenha experimento controlado para validar solucao antes do rollout",
    ["tech", "estrategia", "investidor", "qi_extremo"])
def piloto(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["piloto"]["categorias_pref"])
    prompt = (
        f"Desenhe uma Implementacao Piloto para: {tema}\n\n"
        "1. ESCOPO DO PILOTO: onde testar? (area, equipe, periodo)\n"
        "2. HIPOTESE: 'Se fizermos X, esperamos Y medido por Z'\n"
        "3. METRICAS DE SUCESSO: KPIs antes/depois\n"
        "4. GRUPO CONTROLE: como comparar?\n"
        "5. DURACAO: tempo minimo para resultados significativos\n"
        "6. CRITERIOS GO/NO-GO: em que ponto decidimos escalar ou pivotar?\n"
        "7. RISCOS DO PILOTO: o que pode viciar os resultados?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Piloto")}


@registrar("intervencao", "action_research", "Pesquisa-Acao",
    "Ciclo intervir-observar-refletir-replanejar (Lewin)",
    ["mindset", "visionario", "estrategia", "qi_extremo"])
def action_research(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["action_research"]["categorias_pref"])
    prompt = (
        f"Desenhe um ciclo de Pesquisa-Acao (Lewin) para: {tema}\n\n"
        "CICLO 1:\n"
        "1. PLANEJAR: que intervencao faremos? Hipotese?\n"
        "2. AGIR: como implementar concretamente?\n"
        "3. OBSERVAR: que dados coletar? Como?\n"
        "4. REFLETIR: que aprendizado esperamos? Como alimenta o Ciclo 2?\n\n"
        "CICLO 2 (projetado):\n"
        "- O que ajustariamos com base no aprendizado do Ciclo 1?\n\n"
        "PARTICIPACAO: como envolver os atores afetados como co-pesquisadores?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Pesquisa-Acao")}


# ============================================================
# FASE 5 — AVALIACAO
# ============================================================

@registrar("avaliacao", "pos_teste", "Avaliacao Pos-Teste",
    "Mede resultados apos intervencao comparando com baseline",
    ["estrategia", "investidor", "qi_extremo", "tech"])
def pos_teste(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["pos_teste"]["categorias_pref"])
    prompt = (
        f"Desenhe uma Avaliacao Pos-Teste para: {tema}\n\n"
        "1. BASELINE (antes): que metricas registrar ANTES da intervencao?\n"
        "2. INDICADORES: quais KPIs medem sucesso? (listar pelo menos 5)\n"
        "3. METODO DE COLETA: como medir cada indicador?\n"
        "4. COMPARACAO: antes vs. depois — como garantir que a mudanca causou o efeito?\n"
        "5. AMEACAS A VALIDADE: que fatores externos poderiam explicar a mudanca?\n"
        "6. RELATORIO: como apresentar os resultados para decisores?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Pos-Teste")}


@registrar("avaliacao", "comparative_change", "Design Comparativo de Mudanca",
    "Compara grupo experimental vs. controle para isolar efeito da intervencao",
    ["qi_extremo", "estrategia", "investidor", "tech"])
def comparative_change(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["comparative_change"]["categorias_pref"])
    prompt = (
        f"Desenhe um Design Comparativo de Mudanca para: {tema}\n\n"
        "1. GRUPO EXPERIMENTAL: quem recebe a intervencao?\n"
        "2. GRUPO CONTROLE: quem nao recebe (e por que sao comparaveis)?\n"
        "3. VARIAVEIS:\n"
        "   - Independente: a intervencao\n"
        "   - Dependentes: o que medimos\n"
        "   - Controle: o que mantemos constante\n"
        "4. TIMELINE: pre-teste -> intervencao -> pos-teste\n"
        "5. ANALISE ESTATISTICA: que teste usar? (t-test, ANOVA, etc)\n"
        "6. LIMITACOES: por que nao e um RCT perfeito?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Comparative Change")}


@registrar("avaliacao", "post_project_review", "Revisao Pos-Projeto",
    "Retrospectiva estruturada: o que funcionou, o que nao, licoes aprendidas",
    ["estrategia", "mindset", "lado_negro", "visionario"])
def post_project_review(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["post_project_review"]["categorias_pref"])
    prompt = (
        f"Conduza uma Revisao Pos-Projeto para: {tema}\n\n"
        "1. OBJETIVOS ORIGINAIS: o que queriamos alcançar?\n"
        "2. RESULTADOS OBTIDOS: o que de fato alcancamos? (gap analysis)\n"
        "3. O QUE FUNCIONOU BEM: praticas a replicar\n"
        "4. O QUE NAO FUNCIONOU: erros e suas causas raiz\n"
        "5. SURPRESAS: o que ninguem previu?\n"
        "6. LICOES APRENDIDAS: top 5 licoes para o proximo projeto\n"
        "7. RECOMENDACOES: o que fazer diferente da proxima vez?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Revisao Pos-Projeto")}


@registrar("avaliacao", "triangulacao", "Triangulacao",
    "Valida conclusoes usando multiplas fontes, metodos e perspectivas",
    ["qi_extremo", "visionario", "estrategia", "mindset"])
def triangulacao(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["triangulacao"]["categorias_pref"])
    prompt = (
        f"Aplique Triangulacao para validar conclusoes sobre: {tema}\n\n"
        "1. TRIANGULACAO DE FONTES: 3 fontes diferentes de dados sobre o mesmo fenomeno\n"
        "2. TRIANGULACAO DE METODOS: analise o tema com 3 metodos distintos "
        "(quantitativo, qualitativo, documental)\n"
        "3. TRIANGULACAO DE PERSPECTIVAS: como 3 stakeholders diferentes "
        "veem o mesmo resultado?\n"
        "4. CONVERGENCIA: onde os 3 concordam? (validacao forte)\n"
        "5. DIVERGENCIA: onde discordam? (necessita investigacao)\n"
        "6. CONFIANCA FINAL: alta/media/baixa + justificativa"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Triangulacao")}


# ============================================================
# TRANSVERSAIS
# ============================================================

@registrar("transversal", "revisao_literatura", "Revisao Sistematica de Literatura",
    "Busca e analisa literatura relevante com criterios de inclusao/exclusao",
    ["qi_extremo", "visionario", "estrategia", "tech"])
def revisao_literatura(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["revisao_literatura"]["categorias_pref"])
    prompt = (
        f"Conduza uma Revisao Sistematica de Literatura para: {tema}\n\n"
        "1. PERGUNTA DE PESQUISA: formule usando PICO ou similar\n"
        "2. ESTRATEGIA DE BUSCA: palavras-chave, bases de dados\n"
        "3. CRITERIOS DE INCLUSAO/EXCLUSAO: que estudos entram?\n"
        "4. RESULTADOS: liste 5 referencias-chave (autor, ano, contribuicao)\n"
        "5. SINTESE: que consenso emerge? Onde ha lacunas?\n"
        "6. LIMITACOES: vieses da revisao"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Revisao Sistematica")}


@registrar("transversal", "snowball", "Metodo Snowball",
    "Expande rede de informantes/fontes a partir de um ponto inicial",
    ["estrategia", "visionario", "negociacao", "investidor"])
def snowball(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["snowball"]["categorias_pref"])
    prompt = (
        f"Aplique o Metodo Snowball para explorar: {tema}\n\n"
        "SEMENTE (ponto de partida): [defina o caso/fonte/contato inicial]\n\n"
        "ONDA 1: a partir da semente, quem/o que mais e relevante? (3-5 indicacoes)\n"
        "ONDA 2: a partir da Onda 1, que novas fontes emergem?\n"
        "ONDA 3: ha saturacao (novas fontes repetem as anteriores)?\n\n"
        "MAPA RESULTANTE: como as fontes se conectam?\n"
        "SATURACAO: atingida? Em que onda?\n"
        "VIÉS: o snowball superrepresenta que perspectiva?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Snowball")}


@registrar("transversal", "member_check", "Member Check (Validacao)",
    "Valida achados com os proprios participantes/stakeholders",
    ["negociacao", "mindset", "estrategia", "marca"])
def member_check(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["member_check"]["categorias_pref"])
    prompt = (
        f"Aplique Member Check para validar conclusoes sobre: {tema}\n\n"
        "ACHADOS A VALIDAR: [liste 3 conclusoes sobre o tema]\n\n"
        "Para cada achado, como STAKEHOLDER:\n"
        "1. PRECISAO: esta descricao corresponde a sua experiencia? (sim/parcialmente/nao)\n"
        "2. COMPLETUDE: falta algo importante?\n"
        "3. INTERPRETACAO: a conclusao do pesquisador e justa?\n"
        "4. CORRECAO: o que voce mudaria?\n\n"
        "VEREDICTO: os achados sao criveis? Que ajuste e necessario?"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Member Check")}


@registrar("transversal", "pratica_deliberada", "Pratica Deliberada",
    "Planeja desenvolvimento de competencias com feedback iterativo (Ericsson)",
    ["mindset", "qi_extremo", "visionario", "estrategia"])
def pratica_deliberada(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["pratica_deliberada"]["categorias_pref"])
    prompt = (
        f"Projete um programa de Pratica Deliberada (Ericsson) para: {tema}\n\n"
        "1. COMPETENCIA-ALVO: o que precisa ser dominado?\n"
        "2. NIVEL ATUAL: onde estamos (novato/intermediario/avancado)?\n"
        "3. DECOMPOSICAO: quebre a competencia em sub-habilidades treinaveis\n"
        "4. EXERCICIOS ESPECIFICOS: 3 exercicios com dificuldade progressiva\n"
        "5. FEEDBACK LOOP: como medir progresso a cada sessao?\n"
        "6. MENTOR/MODELO: quem ja domina? Que padrao seguir?\n"
        "7. CRONOGRAMA: plano de 4 semanas com marcos"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "Pratica Deliberada")}
