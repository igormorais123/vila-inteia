"""
CONVERSAR - Módulo de Conversação entre Agentes.

Decide se e com quem conversar, e gera diálogos autênticos
baseados nas personalidades dos consultores.

Diferente do Smallville:
- Usa relacionamentos pré-existentes (mentores, rivais)
- Estilo de argumentação e tom de voz específicos
- Personalidade molda o conteúdo da conversa
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona


def conversar(
    persona: Persona,
    percepcoes: list[dict],
    contexto: dict,
    mundo: Any,
    hora_atual: datetime,
) -> dict | None:
    """
    Decide se conversa e com quem, e gera a conversa.

    Retorna None se não conversa, ou:
    {
        "parceiro_id": str,
        "parceiro_nome": str,
        "topico": str,
        "turnos": list[tuple[str, str]],
        "local_id": str,
        "tipo_relacao": str,
    }
    """
    # Se já está conversando, não iniciar nova
    if persona.rascunho.esta_conversando:
        return None

    # Se está dormindo ou sem energia, não conversa
    if persona.rascunho.esta_dormindo or persona.rascunho.energia < 15:
        return None

    # Encontrar candidatos a conversa (presentes no mesmo local)
    candidatos = []
    for percepcao in percepcoes:
        if percepcao["tipo"] != "presenca":
            continue
        agente_id = percepcao.get("agente_id")
        agente_nome = percepcao.get("agente_nome")
        if agente_id and agente_nome:
            candidatos.append({
                "id": agente_id,
                "nome": agente_nome,
                "importancia": percepcao["importancia"],
            })

    if not candidatos:
        return None

    # Calcular probabilidade de conversa por candidato
    melhor = None
    melhor_prob = 0

    for candidato in candidatos:
        prob = _calcular_prob_conversa(persona, candidato)
        if prob > melhor_prob:
            melhor_prob = prob
            melhor = candidato

    # Decidir se conversa (roll aleatório)
    if not melhor or random.random() > melhor_prob:
        return None

    # Determinar tipo de relação
    tipo_relacao = _tipo_relacao(persona, melhor["nome"])

    # Determinar tópico
    topico = _escolher_topico(persona, melhor, contexto, tipo_relacao)

    # Tentar gerar conversa com IA; fallback para heurística
    turnos = _gerar_conversa_ia(persona, melhor, topico, tipo_relacao, mundo)
    if turnos is None:
        turnos = _gerar_conversa_heuristica(persona, melhor, topico, tipo_relacao)

    # Registrar na memória
    conversa_descricao = (
        f"{persona.nome_exibicao} conversou com {melhor['nome']} "
        f"sobre {topico}"
    )
    persona.memoria.adicionar_conversa(
        descricao=conversa_descricao,
        participantes=[persona.nome_exibicao, melhor["nome"]],
        local_id=persona.rascunho.local_atual,
        importancia=6 + (2 if tipo_relacao in ("mentor", "rival") else 0),
        palavras_chave=set(topico.lower().split()[:5]),
    )

    return {
        "parceiro_id": melhor["id"],
        "parceiro_nome": melhor["nome"],
        "topico": topico,
        "turnos": turnos,
        "local_id": persona.rascunho.local_atual,
        "tipo_relacao": tipo_relacao,
    }


def _calcular_prob_conversa(persona: Persona, candidato: dict) -> float:
    """Probabilidade de iniciar conversa com um candidato."""
    prob = 0.15  # base baixa

    nome = candidato["nome"]
    r = persona.rascunho

    # Relacionamento especial
    if nome in r.mentores:
        prob += 0.45
    elif nome in r.rivais:
        prob += 0.35
    elif nome in r.influenciou or nome in r.influenciado_por:
        prob += 0.25

    # Extroversão
    prob += r.nivel_extroversao * 0.025

    # Carisma favorece ser abordado
    prob += r.nivel_carisma * 0.01

    # Energia
    if r.energia > 70:
        prob += 0.1
    elif r.energia < 30:
        prob -= 0.15

    # Importância da percepção
    prob += candidato["importancia"] * 0.03

    return min(max(prob, 0.05), 0.85)


def _tipo_relacao(persona: Persona, nome_outro: str) -> str:
    """Identifica o tipo de relação com outro agente."""
    r = persona.rascunho
    if nome_outro in r.mentores:
        return "mentor"
    if nome_outro in r.rivais:
        return "rival"
    if nome_outro in r.influenciou:
        return "discipulo"
    if nome_outro in r.influenciado_por:
        return "influencia"
    return "colega"


def _escolher_topico(
    persona: Persona,
    candidato: dict,
    contexto: dict,
    tipo_relacao: str,
) -> str:
    """Escolhe o tópico da conversa baseado no contexto."""
    # Tópicos baseados na relação
    topicos_relacao = {
        "mentor": [
            "conselho de carreira", "lições de vida",
            "visão de futuro", "estratégia de longo prazo",
        ],
        "rival": [
            "debate de ideias", "comparação de abordagens",
            "desafio intelectual", "perspectivas opostas",
        ],
        "discipulo": [
            "legado e influência", "transferência de conhecimento",
            "evolução de ideias", "mentoria reversa",
        ],
        "influencia": [
            "inspiração mútua", "novos paradigmas",
            "colaboração potencial", "troca de frameworks",
        ],
        "colega": [
            "novidades do campus", "projetos em andamento",
            "tendências atuais", "oportunidades de colaboração",
        ],
    }

    topicos = topicos_relacao.get(tipo_relacao, topicos_relacao["colega"])

    # Adicionar tópicos da expertise do agente
    for expertise in persona.rascunho.areas_expertise[:2]:
        topicos.append(f"perspectivas sobre {expertise}")

    # Adicionar reflexões recentes como tópico
    reflexoes = contexto.get("reflexoes_recentes", [])
    if reflexoes:
        topicos.append(reflexoes[-1].descricao[:50])

    return random.choice(topicos)


def _gerar_conversa_heuristica(
    persona: Persona,
    candidato: dict,
    topico: str,
    tipo_relacao: str,
) -> list[tuple[str, str]]:
    """
    Gera turnos de conversa heurísticos (sem LLM).

    Cada turno é (nome_falante, fala).
    """
    d = persona.dados_consultor
    nome_a = persona.nome_exibicao
    nome_b = candidato["nome"]

    # Expressões típicas do consultor
    expressoes = d.get("expressoes_tipicas", [])
    if isinstance(expressoes, str):
        expressoes = [e.strip() for e in expressoes.split(";")]
    frase_chave = d.get("frase_chave", "")

    tom = d.get("tom_voz", "neutro")
    estilo_arg = d.get("estilo_argumentacao", "analítico")

    turnos = []

    # Abertura baseada na relação
    aberturas = {
        "mentor": [
            f"Bom ver você, {nome_b}. Preciso da sua perspectiva.",
            f"{nome_b}, tenho refletido sobre algo que você me ensinou.",
        ],
        "rival": [
            f"{nome_b}. Discordo fundamentalmente da sua última posição.",
            f"Interessante encontrar você aqui, {nome_b}. Podemos resolver aquele debate?",
        ],
        "discipulo": [
            f"{nome_b}, como vai? Tenho algo para compartilhar contigo.",
            f"Que bom te encontrar, {nome_b}. Sua evolução me impressiona.",
        ],
        "colega": [
            f"Olá, {nome_b}. O que acha sobre {topico}?",
            f"{nome_b}, você tem um momento? Gostaria de discutir {topico}.",
        ],
    }

    abertura = random.choice(
        aberturas.get(tipo_relacao, aberturas["colega"])
    )
    turnos.append((nome_a, abertura))

    # Resposta do outro (genérica, será refinada com LLM)
    respostas_genericas = [
        f"Claro, {nome_a}. Esse é um tema que me interessa muito.",
        f"Interessante, {nome_a}. Conte-me mais sobre sua visão.",
        f"Concordo que precisamos discutir isso, {nome_a}.",
    ]
    turnos.append((nome_b, random.choice(respostas_genericas)))

    # Desenvolvimento com personalidade
    if expressoes:
        expr = random.choice(expressoes[:3])
        turnos.append((nome_a, f"Como eu sempre digo: '{expr}'. Isso se aplica aqui."))
    else:
        turnos.append((
            nome_a,
            f"Do meu ponto de vista como {persona.titulo}, "
            f"a questão de {topico} exige uma abordagem {estilo_arg}."
        ))

    turnos.append((
        nome_b,
        "Essa é uma perspectiva válida. Mas considere também..."
    ))

    # Fechamento
    if tipo_relacao == "rival":
        turnos.append((
            nome_a,
            "Não vamos concordar hoje, mas o debate em si já é valioso."
        ))
    elif tipo_relacao == "mentor":
        turnos.append((
            nome_a,
            "Obrigado pela sabedoria. Sempre aprendo com nossas conversas."
        ))
    else:
        turnos.append((
            nome_a,
            "Boa conversa. Devemos continuar isso em breve."
        ))

    return turnos


def _gerar_conversa_ia(
    persona: "Persona",
    candidato: dict,
    topico: str,
    tipo_relacao: str,
    mundo: Any,
) -> list[tuple[str, str]] | None:
    """
    Gera conversa via LLM (OmniRoute/Haiku 4.5).
    Retorna None se LLM indisponível → chamador usa heurística.
    """
    from ..ia_client import chamar_llm_conversa, MODELO_RAPIDO

    nome_a = persona.nome_exibicao
    nome_b = candidato["nome"]

    # Buscar persona B no mundo para system prompt mais rico
    persona_b = None
    if mundo and hasattr(mundo, "personas"):
        for p in mundo.personas.values():
            if p.nome_exibicao == nome_b:
                persona_b = p
                break

    d = persona.dados_consultor
    tom_a = d.get("tom_voz", "direto")
    estilo_a = d.get("estilo_argumentacao", "analítico")
    frase_a = d.get("frase_chave", "")
    expressoes_a = d.get("expressoes_tipicas", "")
    if isinstance(expressoes_a, list):
        expressoes_a = "; ".join(expressoes_a[:3])

    info_b = ""
    if persona_b:
        db = persona_b.dados_consultor
        info_b = (
            f"Tom: {db.get('tom_voz', 'neutro')}\n"
            f"Estilo: {db.get('estilo_argumentacao', 'analítico')}\n"
            f"Frase: \"{db.get('frase_chave', '')}\""
        )
    else:
        info_b = "Outro consultor lendário do campus."

    system = f"""Você gera diálogos autênticos entre consultores lendários.
Responda APENAS os turnos de fala, formato:
{nome_a}: [fala]
{nome_b}: [fala]
Exatamente 4 turnos (2 de cada). Em português do Brasil. Sem narração."""

    user = f"""{nome_a} ({persona.titulo}), tom {tom_a}, estilo {estilo_a}.
Expressões: {expressoes_a}
Frase: "{frase_a}"
Relação com {nome_b}: {tipo_relacao}

{nome_b}: {info_b}

Tópico: {topico}
Local: Campus INTEIA"""

    resposta = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=350)
    if not resposta:
        return None

    # Parse da resposta em turnos
    turnos = []
    for linha in resposta.strip().split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        if ":" in linha:
            partes = linha.split(":", 1)
            falante = partes[0].strip()
            fala = partes[1].strip()
            if fala:
                turnos.append((falante, fala))

    if len(turnos) < 2:
        return None  # Parse falhou, usar heurística

    return turnos[:6]  # Max 6 turnos


def gerar_conversa_com_ia(
    persona_a: "Persona",
    persona_b: "Persona",
    topico: str,
    max_turnos: int = 8,
) -> str:
    """
    Prompt para gerar conversa autêntica via LLM.
    Mantido para compatibilidade.
    """
    prompt = f"""Simule uma conversa natural entre dois consultores num campus de think tank.

CONSULTOR A:
Nome: {persona_a.nome_exibicao}
Título: {persona_a.titulo}
Tom: {persona_a.rascunho.tom_voz}
Estilo: {persona_a.rascunho.estilo_comunicacao}
Frase: "{persona_a.rascunho.frase_chave}"

CONSULTOR B:
Nome: {persona_b.nome_exibicao}
Título: {persona_b.titulo}
Tom: {persona_b.rascunho.tom_voz}
Estilo: {persona_b.rascunho.estilo_comunicacao}
Frase: "{persona_b.rascunho.frase_chave}"

TÓPICO: {topico}
LOCAL: Campus INTEIA, Vila de Think Tank

Gere {max_turnos} turnos de diálogo autêntico. Cada um deve falar
no seu estilo único. O diálogo deve ser intelectualmente estimulante
e revelar as personalidades distintas dos consultores.

Formato:
{persona_a.nome_exibicao}: [fala]
{persona_b.nome_exibicao}: [fala]
..."""

    return prompt
