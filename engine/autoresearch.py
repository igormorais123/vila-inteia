"""
Motor de Autoresearch da Vila INTEIA.

Pesquisa autonoma e evolutiva: a cada N steps, seleciona um tema
relevante, consulta especialistas, sintetiza, e gera novas perguntas.
Descobertas alimentam a simulacao (novos topicos, insights Helena).

Roda no backend (engine), nao no frontend.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .ia_client import chamar_llm, chamar_llm_conversa, MODELO_RAPIDO, MODELO_SINTESE

logger = logging.getLogger("vila-inteia.autoresearch")


@dataclass
class CicloResearch:
    """Um ciclo de pesquisa evolutiva."""
    ciclo: int
    tipo: str  # "semente" ou "evolutivo"
    tema: str
    participantes: list[dict] = field(default_factory=list)
    respostas: list[dict] = field(default_factory=list)
    sintese: Optional[str] = None
    perguntas_geradas: list[str] = field(default_factory=list)
    saturacao: float = 0.0
    inicio: Optional[datetime] = None
    fim: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "ciclo": self.ciclo,
            "tipo": self.tipo,
            "tema": self.tema,
            "participantes": self.participantes,
            "respostas": self.respostas,
            "sintese": self.sintese,
            "perguntas_geradas": self.perguntas_geradas,
            "saturacao": round(self.saturacao, 2),
            "duracao_s": (self.fim - self.inicio).total_seconds() if self.fim and self.inicio else 0,
        }


@dataclass
class PesquisaCompleta:
    """Resultado de uma pesquisa completa (multi-ciclo)."""
    tema_original: str
    ciclos: list[CicloResearch] = field(default_factory=list)
    descoberta_principal: str = ""
    recomendacoes: list[str] = field(default_factory=list)
    topicos_gerados: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "tema_original": self.tema_original,
            "total_ciclos": len(self.ciclos),
            "descoberta_principal": self.descoberta_principal,
            "recomendacoes": self.recomendacoes,
            "topicos_gerados": self.topicos_gerados,
            "ciclos": [c.to_dict() for c in self.ciclos],
            "timestamp": self.timestamp.isoformat(),
        }


class MotorAutoresearch:
    """
    Motor de pesquisa autonoma integrado ao loop da simulacao.

    A cada intervalo (config), seleciona tema e roda ciclos evolutivos.
    Descobertas viram topicos ativos e alimentam Helena.
    """

    def __init__(self, intervalo_steps: int = 100, max_ciclos: int = 3):
        self.intervalo_steps = intervalo_steps
        self.max_ciclos = max_ciclos
        self.ultimo_research_step: int = 0
        self.pesquisas: list[PesquisaCompleta] = []
        self.descobertas_acumuladas: list[str] = []

    def deve_pesquisar(self, step: int) -> bool:
        """Verifica se e hora de iniciar nova pesquisa."""
        return step - self.ultimo_research_step >= self.intervalo_steps

    def selecionar_tema(self, tendencias: list = None, topicos_ativos: list = None) -> Optional[str]:
        """Seleciona o melhor tema para pesquisar."""
        # Prioridade 1: tendencias emergentes
        if tendencias:
            emergentes = [t for t in tendencias if t.direcao == "emergente"]
            if emergentes:
                return emergentes[0].topico

        # Prioridade 2: topicos ativos que nao foram pesquisados
        temas_pesquisados = {p.tema_original for p in self.pesquisas}
        if topicos_ativos:
            novos = [t for t in topicos_ativos if t not in temas_pesquisados]
            if novos:
                return novos[0]

        # Prioridade 3: topicos ja pesquisados com saturacao baixa
        for pesquisa in reversed(self.pesquisas[-5:]):
            if pesquisa.ciclos and pesquisa.ciclos[-1].saturacao < 0.5:
                # Tem perguntas nao exploradas
                for pergunta in pesquisa.ciclos[-1].perguntas_geradas:
                    if pergunta not in temas_pesquisados:
                        return pergunta

        return None

    def executar_pesquisa(
        self,
        tema: str,
        personas: dict,
        step: int,
    ) -> Optional[PesquisaCompleta]:
        """
        Executa pesquisa evolutiva completa (sincrono).

        Seleciona consultores relevantes, coleta perspectivas,
        sintetiza, gera perguntas, e evolui ate saturar.
        """
        self.ultimo_research_step = step
        pesquisa = PesquisaCompleta(tema_original=tema)

        logger.info(f"[AUTORESEARCH] Iniciando pesquisa: '{tema}'")

        # Ciclo 1: Semente
        respondentes = self._selecionar_respondentes(tema, personas, n=5)
        if len(respondentes) < 2:
            logger.warning("[AUTORESEARCH] Poucos respondentes, abortando")
            return None

        ciclo = self._executar_ciclo(
            ciclo_num=1,
            tipo="semente",
            tema=tema,
            respondentes=respondentes,
            contexto_anterior=None,
        )
        pesquisa.ciclos.append(ciclo)

        # Ciclos evolutivos
        for ciclo_num in range(2, self.max_ciclos + 1):
            ciclo_anterior = pesquisa.ciclos[-1]

            # Parar se saturou
            if ciclo_anterior.saturacao >= 0.8:
                logger.info(f"[AUTORESEARCH] Saturou no ciclo {ciclo_num - 1}")
                break

            # Parar se nao gerou perguntas
            if not ciclo_anterior.perguntas_geradas:
                break

            pergunta = ciclo_anterior.perguntas_geradas[0]
            novos_respondentes = self._selecionar_respondentes(pergunta, personas, n=4)

            ciclo = self._executar_ciclo(
                ciclo_num=ciclo_num,
                tipo="evolutivo",
                tema=pergunta,
                respondentes=novos_respondentes,
                contexto_anterior=ciclo_anterior.sintese,
            )
            pesquisa.ciclos.append(ciclo)

        # Gerar descoberta principal e recomendacoes
        pesquisa.descoberta_principal = self._extrair_descoberta(pesquisa)
        pesquisa.recomendacoes = self._gerar_recomendacoes(pesquisa)
        pesquisa.topicos_gerados = self._extrair_topicos(pesquisa)

        self.pesquisas.append(pesquisa)
        self.descobertas_acumuladas.append(pesquisa.descoberta_principal)

        # Manter historico limitado
        if len(self.pesquisas) > 50:
            self.pesquisas = self.pesquisas[-50:]

        logger.info(
            f"[AUTORESEARCH] Pesquisa '{tema}' completa: "
            f"{len(pesquisa.ciclos)} ciclos, "
            f"descoberta: '{pesquisa.descoberta_principal[:60]}...'"
        )

        return pesquisa

    def _selecionar_respondentes(self, tema: str, personas: dict, n: int = 5) -> list:
        """Seleciona consultores por expertise real, nao aleatoriedade."""
        palavras = set(w for w in tema.lower().split() if len(w) > 3)
        scored = []

        for pid, persona in personas.items():
            if not persona.ativo or pid == "IGOR001":
                continue

            score = 0.0
            d = persona.dados_consultor

            # Expertise match (peso forte)
            expertise = " ".join(d.get("areas_expertise") or []).lower()
            tags = " ".join(d.get("tags") or []).lower()
            _cp = d.get("consultor_para") or ""
            consultor_para = (" ".join(_cp) if isinstance(_cp, list) else str(_cp)).lower()
            bio = (d.get("biografia_resumida") or "").lower()

            for p in palavras:
                if p in expertise:
                    score += 3.0
                elif p in tags:
                    score += 2.0
                elif p in consultor_para:
                    score += 2.5
                elif p in bio:
                    score += 1.0

            # Tier bonus
            tier = d.get("tier", "C")
            score += {"S": 2.0, "A": 1.2, "B": 0.5}.get(tier, 0.2)

            # Filtrar irrelevantes
            if score < 0.5:
                continue

            scored.append((persona, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Top N sem shuffle — expertise determina
        return [p for p, _ in scored[:n]]

    def _executar_ciclo(
        self,
        ciclo_num: int,
        tipo: str,
        tema: str,
        respondentes: list,
        contexto_anterior: Optional[str],
    ) -> CicloResearch:
        """Executa um ciclo de pesquisa."""
        ciclo = CicloResearch(
            ciclo=ciclo_num,
            tipo=tipo,
            tema=tema,
            inicio=datetime.now(),
            participantes=[
                {"id": p.id, "nome": p.nome_exibicao, "cat": p.categoria}
                for p in respondentes
            ],
        )

        # Coletar respostas
        for persona in respondentes:
            prompt_tipo = "PESQUISA PROFUNDA" if tipo == "semente" else "APROFUNDAMENTO"
            ctx = f"\n\nContexto do ciclo anterior:\n{contexto_anterior}" if contexto_anterior else ""

            # Prompt RICO montado pela Helena Master (10 técnicas)
            tipo_prompt = "pesquisa" if tipo == "semente" else "aprofundamento"
            system, user = persona.gerar_prompt_pesquisa(
                tema=f"{tema}{ctx}" if ctx else tema,
                tipo=tipo_prompt,
            )

            resposta = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=200)

            if resposta:
                ciclo.respostas.append({
                    "consultor": persona.nome_exibicao,
                    "id": persona.id,
                    "cat": persona.categoria,
                    "texto": resposta,
                })

        # Sintetizar
        if ciclo.respostas:
            ctx_respostas = "\n\n".join(
                f"{r['consultor']}: {r['texto']}" for r in ciclo.respostas
            )
            prompt_sintese = (
                f"SINTESE {'EVOLUTIVA' if tipo == 'evolutivo' else 'DE PESQUISA'} sobre \"{tema}\".\n\n"
                f"Respostas dos consultores:\n{ctx_respostas}\n\n"
                f"Gere: (1) DESCOBERTA PRINCIPAL em 1 frase, "
                f"(2) CONVERGENCIAS, (3) DIVERGENCIAS, "
                f"(4) NIVEL DE SATURACAO (0-100%), "
                f"(5) 2-3 PERGUNTAS para o proximo ciclo."
            )

            sintese = chamar_llm_conversa(
                "Voce e Helena Strategos, cientista-chefe da INTEIA. Neutra, analitica.",
                prompt_sintese,
                modelo=MODELO_SINTESE,
                max_tokens=400,
            )

            ciclo.sintese = sintese

            # Extrair perguntas e saturacao
            if sintese:
                linhas = sintese.split("\n")
                ciclo.perguntas_geradas = [
                    l.strip().lstrip("0123456789.-)*").strip()
                    for l in linhas if "?" in l and len(l) > 20
                ][:3]

                # Extrair saturacao
                import re
                match = re.search(r"satura[çc]a?o[:\s]*(\d+)", sintese, re.IGNORECASE)
                ciclo.saturacao = int(match.group(1)) / 100 if match else 0.3

        ciclo.fim = datetime.now()
        return ciclo

    def _extrair_descoberta(self, pesquisa: PesquisaCompleta) -> str:
        """Extrai descoberta ESTRUTURADA com achado, impacto e próximo passo."""
        tema = pesquisa.tema_original

        if not pesquisa.ciclos or not any(c.respostas for c in pesquisa.ciclos):
            return f"Pesquisa sobre '{tema}' inconclusiva — sem respostas dos consultores"

        # Coletar dados dos ciclos
        n_ciclos = len(pesquisa.ciclos)
        n_respostas = sum(len(c.respostas) for c in pesquisa.ciclos)
        consultores = list({r["consultor"] for c in pesquisa.ciclos for r in c.respostas})

        # Achado principal: última síntese ou resumo
        ultima_sintese = ""
        for ciclo in reversed(pesquisa.ciclos):
            if ciclo.sintese:
                ultima_sintese = ciclo.sintese[:200]
                break

        if not ultima_sintese:
            ultima_sintese = pesquisa.ciclos[-1].respostas[0]["texto"][:200] if pesquisa.ciclos[-1].respostas else "sem dados"

        # Perguntas geradas (indicam onde aprofundar)
        perguntas = []
        for ciclo in pesquisa.ciclos:
            perguntas.extend(ciclo.perguntas_geradas[:1])

        descoberta = (
            f"DESCOBERTA: {ultima_sintese}\n"
            f"MÉTODO: {n_ciclos} ciclos, {n_respostas} respostas de {', '.join(consultores[:4])}"
            f"{f' e +{len(consultores)-4}' if len(consultores) > 4 else ''}.\n"
            f"PRÓXIMO PASSO: {perguntas[0] if perguntas else 'Aprofundar com especialistas de categoria faltante'}"
        )
        return descoberta

    def _gerar_recomendacoes(self, pesquisa: PesquisaCompleta) -> list[str]:
        """Extrai recomendacoes da pesquisa."""
        recs = []
        for ciclo in pesquisa.ciclos:
            for pergunta in ciclo.perguntas_geradas:
                if pergunta not in recs:
                    recs.append(pergunta)
        return recs[:5]

    def _extrair_topicos(self, pesquisa: PesquisaCompleta) -> list[str]:
        """Extrai novos topicos para injetar na simulacao."""
        topicos = []
        for ciclo in pesquisa.ciclos:
            for pergunta in ciclo.perguntas_geradas:
                # Transformar pergunta em topico
                topico = pergunta.rstrip("?").strip()
                if len(topico) > 10 and topico not in topicos:
                    topicos.append(topico)
        return topicos[:3]

    def to_dict(self) -> dict:
        return {
            "total_pesquisas": len(self.pesquisas),
            "ultimo_research_step": self.ultimo_research_step,
            "pesquisas_recentes": [p.to_dict() for p in self.pesquisas[-5:]],
            "descobertas": self.descobertas_acumuladas[-10:],
        }
