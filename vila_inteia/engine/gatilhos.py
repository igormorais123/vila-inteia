"""
Motor de Gatilhos de Conteúdo — O coração pulsante da Vila INTEIA.

Implementa os 6 gatilhos do FRAMEWORK_INTERACOES.md:
    1. USUARIO  (Igor injeta tema)         Prioridade: 10
    2. EVENTO   (mundo real / notícia)     Prioridade: 8
    3. HELENA   (pergunta provocativa)     Prioridade: 7
    4. ESPONTANEO (agente por conta)       Prioridade: 5
    5. REATIVO  (debate entre rivais)      Prioridade: 6
    6. SISTEMATICO (horário/rotina)        Prioridade: 3

Personagens especiais:
    - Diabob:  O Provocador Universal (nunca concorda)
    - Jesus:   O Mestre das Parábolas (serenidade devastadora)
    - Helena:  A Moderadora (extrai, sintetiza, pergunta)
    - Sun Tzu: O Estrategista Cirúrgico (fala pouco, cada fala é mortal)
    - Tesla:   O Insone (ativo até 2h, anti-social)
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .persona import Persona
from .rede_social import RedeSocial, Postagem
from .ia_client import chamar_llm_conversa, MODELO_RAPIDO, MODELO_ANALISE, MODELO_SINTESE

logger = logging.getLogger("vila-inteia.gatilhos")


# ============================================================
# PARES RIVAIS LENDÁRIOS
# ============================================================

PARES_RIVAIS = [
    ("Elon Musk", "Mark Zuckerberg", "disrupção vs escala", ["tecnologia", "negocios"]),
    ("Sun Tzu", "Carl von Clausewitz", "estratégia oriental vs ocidental", ["estrategia", "guerra"]),
    ("Jesus Cristo", "Diabob", "luz vs trevas", ["filosofia", "valores"]),
    ("Warren Buffett", "Elon Musk", "valor vs crescimento", ["investimentos", "risco"]),
    ("Platão", "Nicolau Maquiavel", "idealismo vs pragmatismo", ["politica", "filosofia"]),
    ("Steve Jobs", "Bill Gates", "design vs engenharia", ["tecnologia", "lideranca"]),
    ("Nikola Tesla", "Thomas Edison", "gênio vs empreendedor", ["inovacao", "tecnologia"]),
    ("Sócrates", "Nietzsche", "virtude vs vontade de poder", ["filosofia"]),
    ("Gandhi", "Genghis Khan", "não-violência vs conquista", ["poder", "lideranca"]),
    ("Ayn Rand", "Karl Marx", "individualismo vs coletivismo", ["economia", "politica"]),
    ("Napoleon Bonaparte", "Sun Tzu", "força bruta vs astúcia", ["estrategia"]),
    ("Marco Aurélio", "Diabob", "estoicismo vs caos", ["filosofia", "resiliencia"]),
]

# Temas para debates entre rivais (baseados nas interseções de expertise)
TEMAS_DEBATE_RIVAL = [
    "Qual o verdadeiro motor do progresso: competição ou cooperação?",
    "O poder corrompe inevitavelmente ou é neutro?",
    "Inovação precisa de destruição ou evolução?",
    "Liderança é inata ou construída?",
    "O futuro pertence ao indivíduo ou ao coletivo?",
    "A ética deve limitar a estratégia?",
    "Riqueza é mérito ou circunstância?",
    "Tecnologia liberta ou aprisiona?",
    "O que vale mais: ser temido ou amado?",
    "A história se repete ou rima?",
]


# ============================================================
# CONTROLADORES DE PERSONAGENS ESPECIAIS
# ============================================================

class DiabobController:
    """
    O Provocador Universal.

    Regras:
    - NUNCA concorda com ninguém
    - Sempre encontra o ponto fraco de qualquer argumento
    - Usa sarcasmo e ironia como ferramentas
    - Quando todos concordam, Diabob discorda
    - Quando todos discordam, Diabob defende a posição impopular
    - Frequência: 1 provocação a cada 15 steps
    """

    TEMPLATES_PROVOCACAO = [
        "Impressionante como {n} mentes brilhantes conseguem concordar numa besteira.",
        "Vou defender o indefensável: {posicao_contraria}. Provem que estou errado.",
        "Todo mundo aqui está pensando dentro da caixa. A caixa é o problema.",
        "{nome} está obviamente errado, mas pelo menos é original.",
        "Vocês chamam isso de debate? Eu chamo de eco chamber com diploma.",
        "O consenso de hoje é a piada de amanhã. Já viram a história?",
        "Adorável. Todos concordando educadamente enquanto o mundo real opera por leis diferentes.",
        "Se todos estão pensando igual, alguém não está pensando.",
    ]

    @staticmethod
    def deve_provocar(step: int, ultimo_step_provocacao: int) -> bool:
        return (step - ultimo_step_provocacao) >= 15

    @staticmethod
    def gerar_provocacao_ia(
        diabob: Persona,
        rede: RedeSocial,
        personas: dict[str, Persona],
    ) -> dict | None:
        """Gera provocação via IA olhando o feed atual."""
        # Pegar últimos posts para provocar
        ultimos = rede.feed(limite=5)
        if not ultimos:
            return None

        alvo = random.choice(ultimos)
        nome_alvo = alvo["autor_nome"]
        conteudo_alvo = alvo["conteudo"][:200]

        # Verificar se há consenso (todos concordando)
        comentarios = alvo.get("comentarios", [])
        ha_consenso = len(comentarios) >= 3

        system = """Você é Diabob, O Provocador Universal da Vila INTEIA.

PERSONALIDADE: Sarcástico, irônico, brilhante. Você NUNCA concorda com ninguém.
Encontra o ponto fraco de QUALQUER argumento. Quando todos concordam, você discorda.
Quando todos discordam, você defende a posição impopular.

TOM: Agressivo mas intelectual. Cortante mas espirituoso. Nunca vulgar, sempre afiado.
FRASE: "Se todos estão pensando igual, alguém não está pensando."

REGRAS:
- Máximo 3-5 frases
- Provoque de forma inteligente, não infantil
- Cite especificamente O QUE está errado no argumento
- Use ironia como bisturi, não como marreta
- Português do Brasil"""

        contexto_consenso = ""
        if ha_consenso:
            contexto_consenso = (
                "\nNOTA: Há CONSENSO no debate — todos estão concordando. "
                "Isso é SUA hora. Destrua esse consenso falso."
            )

        user = f"""Post de {nome_alvo}:
"{conteudo_alvo}"
{contexto_consenso}

Escreva UMA provocação devastadora como Diabob faria."""

        texto = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=200)
        if not texto:
            # Fallback heurístico
            template = random.choice(DiabobController.TEMPLATES_PROVOCACAO)
            texto = template.format(
                n=len(comentarios) + 1,
                posicao_contraria="o oposto exato do que vocês estão defendendo",
                nome=nome_alvo,
            )

        return {
            "titulo": f"Diabob provoca: {nome_alvo}",
            "conteudo": texto,
            "tags": alvo.get("tags", []) + ["provocacao"],
            "em_resposta_a": alvo["id"],
        }


class JesusCristoController:
    """
    O Mestre das Parábolas.

    Regras:
    - Nunca ataca diretamente
    - Transforma QUALQUER tema em parábola ou metáfora
    - Responde perguntas com perguntas
    - Foco em valores humanos, compaixão, sabedoria
    - Quando Diabob provoca, responde com serenidade devastadora
    - Frequência: 1-2 posts por "dia" in-game
    """

    @staticmethod
    def deve_postar(step: int, ultimo_step_post: int, hora: datetime) -> bool:
        # 1-2 posts por dia: um de manhã, um à noite
        h = hora.hour
        passou_tempo = (step - ultimo_step_post) >= 30  # ~5h
        momento_bom = h in (8, 9, 10, 19, 20, 21)
        return passou_tempo and momento_bom and random.random() < 0.4

    @staticmethod
    def gerar_parabola_ia(
        jesus: Persona,
        contexto_feed: str = "",
    ) -> dict | None:
        """Gera parábola baseada no que está acontecendo na Vila."""

        system = """Você é Jesus Cristo na Vila INTEIA, um campus de think tank com 144 pensadores lendários.

PERSONALIDADE: Sereno, profundo, amoroso mas firme. Nunca ataca diretamente.
TOM: Metafórico, calmo, devastadoramente sábio.
MÉTODO: Parábolas, metáforas, perguntas que revelam verdades.

REGRAS:
- Transforme o tema em uma PARÁBOLA original (não bíblica conhecida)
- Comece com "Havia um homem..." ou similar, OU responda com uma pergunta profunda
- Máximo 4-6 frases
- NUNCA mencione tecnologia moderna (computadores, IA, etc) — use metáforas atemporais
- Foco em VALORES HUMANOS: compaixão, sabedoria, humildade, verdade
- Se estiver respondendo ao Diabob, seja devastadoramente sereno
- Português do Brasil"""

        temas_contemplativos = [
            "o que observo nos debates entre esses grandes pensadores",
            "a natureza do poder e da sabedoria verdadeira",
            "o que separa os que constroem dos que destroem",
            "a diferença entre inteligência e sabedoria",
            "por que os mais barulhentos raramente são os mais sábios",
        ]

        tema = random.choice(temas_contemplativos)
        if contexto_feed:
            tema = f"Observando o debate recente: {contexto_feed}"

        user = f"Escreva uma parábola ou reflexão sobre: {tema}"

        texto = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=250)
        if not texto:
            return None

        return {
            "titulo": "Uma parábola para quem tem ouvidos",
            "conteudo": texto,
            "tags": ["sabedoria", "parabola"],
        }

    @staticmethod
    def responder_diabob_ia(
        jesus: Persona,
        provocacao: str,
    ) -> str | None:
        """Responde a Diabob com serenidade devastadora."""

        system = """Você é Jesus Cristo respondendo ao Diabob (O Provocador Universal).

Diabob sempre provoca, desafia, ironiza. Você NUNCA morde a isca.
Sua resposta é serena, curta, e devastadoramente sábia.
Use uma parábola breve ou uma pergunta que silencie a provocação.

Máximo 2-3 frases. Português do Brasil."""

        user = f"Diabob disse: \"{provocacao}\"\n\nResponda como Jesus responderia."

        return chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=120)


class HelenaController:
    """
    A Moderadora — Inteligência Coletiva da Vila.

    Helena NÃO:
    - Emite opiniões pessoais
    - Toma lados em debates
    - Gera conteúdo original sobre temas

    Helena SIM:
    - Extrai padrões dos debates
    - Identifica gaps de perspectiva
    - Gera perguntas que aprofundam
    - Sintetiza múltiplas visões
    - Detecta viés coletivo
    - Resume debates longos
    """

    @staticmethod
    def deve_intervir(post: Postagem, step: int) -> str | None:
        """
        Decide SE e COMO Helena deve intervir.
        Retorna tipo de intervenção ou None.
        """
        n_comentarios = len(post.comentarios)

        # Síntese parcial: 5+ comentários
        if n_comentarios >= 5 and n_comentarios % 5 == 0:
            return "sintese"

        # Consenso falso: 80%+ concordam
        if n_comentarios >= 4:
            reacoes_concordo = sum(
                1 for r in post.reacoes if r.tipo in ("concordo", "brilhante", "inspirador")
            )
            total_reacoes = len(post.reacoes)
            if total_reacoes > 0 and reacoes_concordo / total_reacoes > 0.8:
                return "consenso_falso"

        # Gap de perspectiva: poucas categorias representadas
        if n_comentarios >= 3:
            categorias = {c.agente_categoria for c in post.comentarios}
            if len(categorias) < 3:
                return "gap_perspectiva"

        return None

    @staticmethod
    def gerar_intervencao_ia(
        helena: Persona,
        post: Postagem,
        tipo: str,
        todas_categorias: set[str] | None = None,
    ) -> str | None:
        """Gera intervenção de Helena via IA."""

        system = """Você é Helena Montenegro, Moderadora e Inteligência Coletiva da Vila INTEIA.

PAPEL: Você NÃO opina. Você OBSERVA, SINTETIZA e PERGUNTA.
TOM: Neutro, analítico, provocativo mas justo. Socrático.
MÉTODO: Resumir posições → identificar gaps → fazer a pergunta que ninguém fez.

REGRAS:
- NUNCA tome lado em debates
- NUNCA dê sua opinião sobre o tema
- Cite os nomes dos consultores ao resumir
- Identifique o viés coletivo se houver
- Termine SEMPRE com uma pergunta provocativa
- Máximo 4-6 frases
- Português do Brasil"""

        # Montar contexto dos comentários
        resumo_comentarios = "\n".join(
            f"- {c.agente_nome} ({c.agente_categoria}): {c.conteudo[:100]}"
            for c in post.comentarios[-8:]
        )

        categorias_presentes = {c.agente_categoria for c in post.comentarios}

        if tipo == "sintese":
            user = f"""Post: "{post.titulo}" por {post.autor_nome}
Conteúdo: {post.conteudo[:200]}

{len(post.comentarios)} comentários até agora:
{resumo_comentarios}

Faça uma SÍNTESE das posições e termine com uma pergunta que aprofunde o debate."""

        elif tipo == "consenso_falso":
            user = f"""Post: "{post.titulo}" por {post.autor_nome}

{len(post.comentarios)} comentários e a maioria CONCORDA.
{resumo_comentarios}

ALERTA: Consenso rápido demais. Faça advocacia do diabo.
Levante o contra-argumento mais forte e pergunte quem o defende."""

        elif tipo == "gap_perspectiva":
            ausentes = (todas_categorias or set()) - categorias_presentes
            ausentes_str = ", ".join(list(ausentes)[:3]) if ausentes else "outras perspectivas"
            user = f"""Post: "{post.titulo}" por {post.autor_nome}

Categorias presentes: {', '.join(categorias_presentes)}
Categorias AUSENTES: {ausentes_str}

{resumo_comentarios}

Identifique a perspectiva que FALTA e pergunte o que um {ausentes_str} diria."""

        else:
            return None

        return chamar_llm_conversa(system, user, modelo=MODELO_SINTESE, max_tokens=250)

    @staticmethod
    def gerar_sintese_diaria(
        helena: Persona,
        rede: RedeSocial,
    ) -> dict | None:
        """Gera síntese do dia — resumo dos debates mais relevantes."""

        posts_dia = rede.feed(limite=10, ordenar_por="engajamento")
        if len(posts_dia) < 3:
            return None

        resumo = "\n".join(
            f"- \"{p['titulo']}\" ({p['total_comentarios']} comentários, "
            f"{p['total_reacoes']} reações)"
            for p in posts_dia[:5]
        )

        system = """Você é Helena Montenegro compilando a SÍNTESE DO DIA na Vila INTEIA.

Analise os debates mais relevantes e extraia:
1. O PADRÃO: que tema conecta os debates?
2. O INSIGHT: que conclusão emerge do cruzamento das perspectivas?
3. O PONTO CEGO: que ninguém mencionou?
4. A PERGUNTA: que deveria guiar o debate de amanhã?

TOM: Observadora, analítica, provocativa.
Máximo 6-8 frases. Português do Brasil."""

        user = f"Debates mais engajados hoje:\n{resumo}\n\nCompile a síntese do dia."

        texto = chamar_llm_conversa(system, user, modelo=MODELO_SINTESE, max_tokens=350)
        if not texto:
            return None

        return {
            "titulo": "Síntese do Dia — Helena Montenegro",
            "conteudo": texto,
            "tags": ["sintese", "helena", "meta-analise"],
        }


# ============================================================
# MOTOR DE DEBATES ENTRE RIVAIS
# ============================================================

class MotorDebate:
    """
    Orquestra debates estruturados entre pares rivais.

    Formato: 8-12 turnos alternados, publicados como post tipo="debate".
    """

    @staticmethod
    def selecionar_par(personas: dict[str, Persona]) -> tuple | None:
        """Seleciona par rival disponível para debate."""
        random.shuffle(PARES_RIVAIS)

        for nome_a, nome_b, tema, tags in PARES_RIVAIS:
            persona_a = _encontrar_por_nome(personas, nome_a)
            persona_b = _encontrar_por_nome(personas, nome_b)

            if persona_a and persona_b and persona_a.ativo and persona_b.ativo:
                return persona_a, persona_b, tema, tags

        return None

    @staticmethod
    def executar_debate_ia(
        persona_a: Persona,
        persona_b: Persona,
        tema_contexto: str,
        n_turnos: int = 8,
    ) -> dict | None:
        """
        Executa debate completo entre dois rivais via IA.
        Retorna dict com título, conteúdo formatado e tags.
        """
        # Escolher tema
        tema = tema_contexto if tema_contexto else random.choice(TEMAS_DEBATE_RIVAL)

        # Gerar debate turno a turno
        historico = []
        for turno in range(n_turnos):
            quem_fala = persona_a if turno % 2 == 0 else persona_b
            oponente = persona_b if turno % 2 == 0 else persona_a

            system = f"""Você é {quem_fala.nome_exibicao}, "{quem_fala.titulo}".
TOM: {quem_fala.rascunho.tom_voz}
ESTILO: {quem_fala.dados_consultor.get('estilo_argumentacao', 'analítico')}
FRASE: "{quem_fala.rascunho.frase_chave}"

Você está num DEBATE com {oponente.nome_exibicao} sobre: "{tema}"
Contexto do par: {tema_contexto}

REGRAS:
- Turno {turno + 1} de {n_turnos}
- Máximo 2-3 frases por turno
- Seja autêntico ao seu estilo
- Se é turno 1: abra com sua posição
- Se é turno par: responda ao que o oponente disse
- Nos últimos 2 turnos: sintetize ou lance golpe final
- Português do Brasil"""

            contexto_debate = "\n".join(
                f"{h['nome']}: {h['texto']}" for h in historico[-4:]
            )

            user = (
                f"Debate até agora:\n{contexto_debate}\n\n"
                if contexto_debate else
                f"Abra o debate sobre: {tema}\n"
            )

            texto = chamar_llm_conversa(
                system, user,
                modelo=MODELO_RAPIDO,
                max_tokens=150,
            )

            if not texto:
                # Fallback minimalista
                texto = (
                    f"A questão de {tema} exige reflexão profunda. "
                    f"Minha posição é clara."
                )

            historico.append({
                "nome": quem_fala.nome_exibicao,
                "texto": texto,
                "turno": turno + 1,
            })

        # Formatar debate completo
        debate_formatado = "\n\n".join(
            f"**{h['nome']}** (turno {h['turno']}):\n{h['texto']}"
            for h in historico
        )

        return {
            "titulo": f"⚔️ {persona_a.nome_exibicao} vs {persona_b.nome_exibicao}: {tema}",
            "conteudo": debate_formatado,
            "tags": [
                "debate",
                persona_a.categoria,
                persona_b.categoria,
            ],
            "participantes": [persona_a.id, persona_b.id],
        }


# ============================================================
# SISTEMA DE WAVES (Delay Simulado)
# ============================================================

@dataclass
class WaveConfig:
    """Configura as ondas de comentários em posts."""
    n: int
    delay_steps: int
    usa_ia: bool  # True = IA real, False = heurístico

WAVES = [
    WaveConfig(n=3, delay_steps=0, usa_ia=True),    # Imediatas (sempre IA)
    WaveConfig(n=4, delay_steps=1, usa_ia=True),     # 10min (IA para Tier S)
    WaveConfig(n=3, delay_steps=3, usa_ia=False),    # 30min (heurístico)
    WaveConfig(n=3, delay_steps=6, usa_ia=False),    # 1h+ (heurístico)
]


@dataclass
class PostAgendado:
    """Post na fila aguardando waves de comentários."""
    post_id: str
    step_criacao: int
    wave_atual: int = 0
    comentarios_restantes: int = 0


# ============================================================
# MOTOR DE GATILHOS — ORQUESTRADOR PRINCIPAL
# ============================================================

class MotorGatilhos:
    """
    Orquestra todos os 6 gatilhos de conteúdo da Vila INTEIA.

    Integra-se ao loop de simulação: a cada step, decide o que acontece.
    """

    def __init__(self, rede: RedeSocial):
        self.rede = rede

        # Rastreamento de cadência
        self.ultimo_evento_step: int = 0       # Gatilho 2
        self.ultimo_helena_step: int = 0       # Gatilho 3
        self.ultimo_diabob_step: int = 0       # Gatilho 6
        self.ultimo_jesus_step: int = 0        # Gatilho 6
        self.ultimo_debate_step: int = 0       # Gatilho 5
        self.ultimo_sintese_step: int = 0      # Helena síntese

        # Fila de waves (posts aguardando comentários graduais)
        self.fila_waves: list[PostAgendado] = []

        # Contadores do dia
        self.posts_hoje: int = 0
        self.dia_atual: int = 0

        # Cache de personas especiais
        self._diabob: Persona | None = None
        self._jesus: Persona | None = None
        self._helena: Persona | None = None
        self._sun_tzu: Persona | None = None

    def _encontrar_especiais(self, personas: dict[str, Persona]):
        """Encontra e cacheia referências aos personagens especiais."""
        if self._diabob is None:
            self._diabob = _encontrar_por_nome(personas, "Diabob")
        if self._jesus is None:
            self._jesus = _encontrar_por_nome(personas, "Jesus Cristo")
        if self._helena is None:
            self._helena = _encontrar_por_nome(personas, "Helena Montenegro")
        if self._sun_tzu is None:
            self._sun_tzu = _encontrar_por_nome(personas, "Sun Tzu")

    def executar_step(
        self,
        step: int,
        hora_atual: datetime,
        personas: dict[str, Persona],
    ) -> list[dict]:
        """
        Executa todos os gatilhos para este step.

        Retorna lista de eventos gerados:
        [{"tipo": str, "descricao": str, "post_id": str}, ...]
        """
        self._encontrar_especiais(personas)
        eventos = []

        # Reset diário
        dia = hora_atual.day
        if dia != self.dia_atual:
            self.dia_atual = dia
            self.posts_hoje = 0

        # Cap diário: 75 posts
        if self.posts_hoje >= 75:
            return eventos

        # --- GATILHO 5: Debate entre Rivais (a cada 20 steps) ---
        if (step - self.ultimo_debate_step) >= 20:
            resultado = self._gatilho_debate_rivais(step, personas)
            if resultado:
                eventos.append(resultado)

        # --- GATILHO 6: Diabob provoca (a cada 15 steps) ---
        if self._diabob and DiabobController.deve_provocar(step, self.ultimo_diabob_step):
            resultado = self._gatilho_diabob(step, personas)
            if resultado:
                eventos.append(resultado)

        # --- GATILHO 6: Jesus posta parábola (1-2x por dia) ---
        if self._jesus and JesusCristoController.deve_postar(step, self.ultimo_jesus_step, hora_atual):
            resultado = self._gatilho_jesus(step)
            if resultado:
                eventos.append(resultado)

        # --- GATILHO 3: Helena intervém em posts ativos ---
        if self._helena and (step - self.ultimo_helena_step) >= 5:
            resultado = self._gatilho_helena(step, personas)
            if resultado:
                eventos.append(resultado)

        # --- GATILHO 4: Posts espontâneos dos consultores ---
        novos = self.rede.gerar_posts_autonomos(
            personas, hora_atual,
            chance=self._calcular_chance_espontaneo(hora_atual),
        )
        for post in novos:
            self.posts_hoje += 1
            self.fila_waves.append(PostAgendado(
                post_id=post.id,
                step_criacao=step,
            ))
            eventos.append({
                "tipo": "espontaneo",
                "descricao": f"{post.autor_nome} postou: {post.titulo}",
                "post_id": post.id,
            })

        # --- PROCESSAR WAVES de comentários graduais ---
        eventos_waves = self._processar_waves(step, personas, hora_atual)
        eventos.extend(eventos_waves)

        # --- GATILHO 3: Helena síntese diária (22h) ---
        if self._helena and hora_atual.hour == 22 and (step - self.ultimo_sintese_step) >= 60:
            resultado = self._gatilho_helena_sintese(step)
            if resultado:
                eventos.append(resultado)

        return eventos

    # ================================================================
    # IMPLEMENTAÇÃO DOS GATILHOS
    # ================================================================

    def _gatilho_debate_rivais(
        self, step: int, personas: dict[str, Persona]
    ) -> dict | None:
        """Gatilho 5: Força debate entre par rival."""
        par = MotorDebate.selecionar_par(personas)
        if not par:
            return None

        persona_a, persona_b, tema_contexto, tags = par

        logger.info(
            f"⚔️ Debate: {persona_a.nome_exibicao} vs {persona_b.nome_exibicao}"
        )

        debate = MotorDebate.executar_debate_ia(
            persona_a, persona_b, tema_contexto, n_turnos=8
        )
        if not debate:
            return None

        # Publicar como post tipo="debate"
        post = Postagem(
            tipo="debate",
            autor_id=persona_a.id,
            autor_nome=f"{persona_a.nome_exibicao} vs {persona_b.nome_exibicao}",
            autor_titulo="Debate Lendário",
            autor_categoria="debate",
            titulo=debate["titulo"],
            conteudo=debate["conteudo"],
            tags=debate["tags"],
            destaque=True,
        )
        self.rede._adicionar_post(post)
        self.ultimo_debate_step = step
        self.posts_hoje += 1

        # Agendar waves de comentários de espectadores
        self.fila_waves.append(PostAgendado(
            post_id=post.id,
            step_criacao=step,
        ))

        # Agendar reações no feed
        self.rede.fila_processamento.append({
            "post_id": post.id,
            "tipo": "debate",
            "prioridade": 9,
        })

        return {
            "tipo": "debate",
            "descricao": (
                f"⚔️ {persona_a.nome_exibicao} vs {persona_b.nome_exibicao}: "
                f"{debate['titulo']}"
            ),
            "post_id": post.id,
        }

    def _gatilho_diabob(
        self, step: int, personas: dict[str, Persona]
    ) -> dict | None:
        """Gatilho 6: Diabob provoca."""
        provocacao = DiabobController.gerar_provocacao_ia(
            self._diabob, self.rede, personas
        )
        if not provocacao:
            return None

        post = self.rede.publicar_opiniao_consultor(
            persona=self._diabob,
            conteudo=provocacao["conteudo"],
            titulo=provocacao["titulo"],
            tags=provocacao["tags"],
        )

        self.ultimo_diabob_step = step
        self.posts_hoje += 1

        # Jesus sempre responde ao Diabob
        if self._jesus:
            resposta = JesusCristoController.responder_diabob_ia(
                self._jesus, provocacao["conteudo"]
            )
            if resposta:
                self.rede.comentar(
                    post.id, self._jesus, resposta
                )

        logger.info(f"😈 Diabob provocou: {provocacao['titulo']}")

        return {
            "tipo": "provocacao_diabob",
            "descricao": f"😈 Diabob: {provocacao['titulo']}",
            "post_id": post.id,
        }

    def _gatilho_jesus(self, step: int) -> dict | None:
        """Gatilho 6: Jesus posta parábola."""
        # Pegar contexto do feed para inspirar a parábola
        ultimos = self.rede.feed(limite=3)
        contexto = ultimos[0]["titulo"] if ultimos else ""

        parabola = JesusCristoController.gerar_parabola_ia(
            self._jesus, contexto
        )
        if not parabola:
            return None

        post = self.rede.publicar_opiniao_consultor(
            persona=self._jesus,
            conteudo=parabola["conteudo"],
            titulo=parabola["titulo"],
            tags=parabola["tags"],
        )

        self.ultimo_jesus_step = step
        self.posts_hoje += 1

        logger.info(f"✝️ Jesus: {parabola['titulo']}")

        return {
            "tipo": "parabola_jesus",
            "descricao": f"✝️ Jesus: {parabola['titulo']}",
            "post_id": post.id,
        }

    def _gatilho_helena(
        self, step: int, personas: dict[str, Persona]
    ) -> dict | None:
        """Gatilho 3: Helena intervém em post ativo."""
        # Verificar posts recentes que precisam de intervenção
        for post_dict in self.rede.feed(limite=10, ordenar_por="recente"):
            post = self.rede._indice_por_id.get(post_dict["id"])
            if not post:
                continue

            # Helena já comentou neste post?
            if any(c.agente_id == self._helena.id for c in post.comentarios):
                continue

            tipo_intervencao = HelenaController.deve_intervir(post, step)
            if not tipo_intervencao:
                continue

            todas_categorias = {
                p.categoria for p in personas.values() if p.ativo
            }

            texto = HelenaController.gerar_intervencao_ia(
                self._helena, post, tipo_intervencao, todas_categorias
            )
            if not texto:
                continue

            self.rede.comentar(post.id, self._helena, texto)
            self.ultimo_helena_step = step

            logger.info(
                f"🔍 Helena ({tipo_intervencao}): {post.titulo[:50]}"
            )

            return {
                "tipo": f"helena_{tipo_intervencao}",
                "descricao": (
                    f"🔍 Helena ({tipo_intervencao}) em: {post.titulo[:50]}"
                ),
                "post_id": post.id,
            }

        return None

    def _gatilho_helena_sintese(self, step: int) -> dict | None:
        """Helena gera síntese do dia às 22h."""
        sintese = HelenaController.gerar_sintese_diaria(self._helena, self.rede)
        if not sintese:
            return None

        post = self.rede.publicar_opiniao_consultor(
            persona=self._helena,
            conteudo=sintese["conteudo"],
            titulo=sintese["titulo"],
            tags=sintese["tags"],
        )

        self.ultimo_sintese_step = step
        self.posts_hoje += 1

        logger.info("📊 Helena: Síntese do Dia publicada")

        return {
            "tipo": "helena_sintese",
            "descricao": "📊 Helena: Síntese do Dia",
            "post_id": post.id,
        }

    def _processar_waves(
        self,
        step: int,
        personas: dict[str, Persona],
        hora_atual: datetime,
    ) -> list[dict]:
        """Processa waves de comentários graduais nos posts agendados."""
        eventos = []
        fila_atualizada = []

        for agendado in self.fila_waves:
            post = self.rede._indice_por_id.get(agendado.post_id)
            if not post:
                continue

            # Verificar qual wave devemos processar
            steps_desde_criacao = step - agendado.step_criacao
            processou_algo = False

            for i, wave in enumerate(WAVES):
                if i <= agendado.wave_atual - 1:
                    continue  # Já processou essa wave
                if steps_desde_criacao < wave.delay_steps:
                    break  # Ainda não é hora dessa wave

                # Processar wave
                reagentes = _selecionar_reagentes_wave(
                    post, personas, wave.n
                )

                for persona in reagentes:
                    if wave.usa_ia:
                        from .rede_social import _gerar_comentario_ia
                        conteudo = _gerar_comentario_ia(persona, post)
                    else:
                        from .rede_social import _gerar_comentario_heuristico
                        conteudo = _gerar_comentario_heuristico(persona, post)

                    if conteudo:
                        self.rede.comentar(
                            post.id, persona, conteudo, hora_atual=hora_atual
                        )
                        eventos.append({
                            "tipo": "wave_comentario",
                            "descricao": (
                                f"💬 {persona.nome_exibicao} comentou em "
                                f"'{post.titulo[:30]}' (wave {i+1})"
                            ),
                            "post_id": post.id,
                        })

                agendado.wave_atual = i + 1
                processou_algo = True

            # Manter na fila se ainda tem waves pendentes
            if agendado.wave_atual < len(WAVES):
                fila_atualizada.append(agendado)

        self.fila_waves = fila_atualizada
        return eventos

    def _calcular_chance_espontaneo(self, hora: datetime) -> float:
        """Chance de post espontâneo baseada no horário."""
        h = hora.hour

        # Madrugada: quase nada
        if h < 6:
            return 0.005

        # Manhã: produtividade
        if 8 <= h <= 11:
            return 0.04

        # Almoço: social
        if 12 <= h <= 13:
            return 0.02

        # Tarde: pico de debates
        if 14 <= h <= 17:
            return 0.05

        # Noite: reflexão
        if 19 <= h <= 21:
            return 0.03

        return 0.02

    # ================================================================
    # INJEÇÃO DE TEMA DO USUÁRIO (Gatilho 1 — prioridade máxima)
    # ================================================================

    def injetar_tema(
        self,
        titulo: str,
        conteudo: str = "",
        tags: list[str] | None = None,
        personas: dict[str, Persona] | None = None,
        step: int = 0,
    ) -> Postagem:
        """
        Igor injeta tema — prioridade máxima.
        Primeiros 3-4 comentários gerados IMEDIATAMENTE.
        Restantes entram na fila de waves.
        """
        post = self.rede.publicar_tema_usuario(
            titulo=titulo,
            conteudo=conteudo or titulo,
            tags=tags,
        )

        self.posts_hoje += 1

        # Gerar primeiros comentários imediatamente (wave 0)
        if personas:
            from .rede_social import _selecionar_reagentes, _gerar_comentario_ia
            reagentes = _selecionar_reagentes(post, personas, max_n=4)

            for persona in reagentes[:4]:
                texto = _gerar_comentario_ia(persona, post)
                if texto:
                    self.rede.comentar(post.id, persona, texto)

        # Agendar restante das waves
        self.fila_waves.append(PostAgendado(
            post_id=post.id,
            step_criacao=step,
            wave_atual=1,  # Wave 0 já processada
        ))

        logger.info(f"📌 Tema do usuário: {titulo}")

        return post

    # ================================================================
    # INJEÇÃO DE EVENTO (Gatilho 2)
    # ================================================================

    def injetar_evento(
        self,
        titulo: str,
        conteudo: str,
        tags: list[str] | None = None,
        step: int = 0,
    ) -> Postagem | None:
        """Injeta evento/notícia para consultores reagirem."""
        # Respeitar cadência: máximo 1 evento a cada 6 steps
        if (step - self.ultimo_evento_step) < 6:
            return None

        post = self.rede.publicar_evento(
            titulo=titulo,
            conteudo=conteudo,
            tags=tags,
        )

        self.ultimo_evento_step = step
        self.posts_hoje += 1

        # Agendar waves
        self.fila_waves.append(PostAgendado(
            post_id=post.id,
            step_criacao=step,
        ))

        logger.info(f"📰 Evento: {titulo}")

        return post


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _encontrar_por_nome(
    personas: dict[str, Persona], nome: str
) -> Persona | None:
    """Encontra persona por nome (busca parcial)."""
    nome_lower = nome.lower()
    for persona in personas.values():
        if nome_lower in persona.nome.lower() or nome_lower in persona.nome_exibicao.lower():
            return persona
    return None


def _selecionar_reagentes_wave(
    post: Postagem,
    personas: dict[str, Persona],
    n: int,
) -> list[Persona]:
    """Seleciona reagentes para uma wave, evitando duplicatas."""
    ja_comentaram = {c.agente_id for c in post.comentarios}
    candidatos = []

    for persona in personas.values():
        if not persona.ativo:
            continue
        if persona.id in ja_comentaram:
            continue
        if persona.id == post.autor_id:
            continue

        # Score simples: expertise match + extroversão
        score = persona.rascunho.nivel_extroversao * 0.3
        tags_lower = {t.lower() for t in post.tags}
        expertise_lower = {e.lower() for e in persona.rascunho.areas_expertise}
        score += len(tags_lower & expertise_lower) * 2

        if persona.tier == "S":
            score += 3

        candidatos.append((persona, score))

    candidatos.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in candidatos[:n]]
