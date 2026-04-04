"""
Auto-Research Engine — Inspirado no loop de auto-aprimoramento de Andrej Karpathy.

Ciclo: Gerar -> Avaliar -> Criticar -> Refinar -> Sintetizar -> Loop
Cada iteracao melhora a qualidade do output usando critica cruzada entre consultores.

Referencia: Karpathy (2024) — "The unreasonable effectiveness of self-play"
Conceito: Ao inves de um unico prompt -> resposta, o sistema roda N iteracoes
onde agentes geram, avaliam, criticam e refinam suas respostas. O score
de qualidade sobe a cada iteracao ate atingir um threshold.
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Optional

from .ia_client import chamar_llm_conversa


class AutoResearchLoop:
    """
    Loop de pesquisa autonoma com auto-aprimoramento.

    Fluxo por iteracao:
    1. GERAR: N consultores produzem respostas iniciais
    2. AVALIAR: Cada resposta recebe score (0-10) de outro consultor
    3. CRITICAR: Top critico aponta falhas nas melhores respostas
    4. REFINAR: Na proxima iteracao, autores melhoram baseado na critica
    5. SINTETIZAR: Melhor sintetizador combina tudo
    6. META-AVALIAR: Score da sintese decide se faz mais uma iteracao

    Para quando: meta-score >= threshold OU max_iterations atingido.
    """

    def __init__(self, simulacao):
        self.sim = simulacao
        self.history = []

    def run(
        self,
        pergunta: str,
        n_consultores: int = 5,
        max_iterations: int = 3,
        quality_threshold: float = 8.0,
        categorias: list = None,
    ) -> dict:
        """Executa loop completo de auto-research."""

        start_time = time.time()

        agentes = self._selecionar_agentes(n_consultores, categorias)
        if not agentes:
            return {"erro": "Sem agentes disponiveis"}

        iterations = []
        best_synthesis = ""
        best_score = 0

        for i in range(max_iterations):
            iteration = self._run_iteration(
                pergunta=pergunta,
                agentes=agentes,
                iteration_num=i + 1,
                previous_synthesis=best_synthesis if i > 0 else None,
                previous_criticisms=iterations[-1].get("criticisms", []) if iterations else [],
            )
            iterations.append(iteration)

            # Manter a melhor sintese (pode regredir)
            if iteration["meta_score"] >= best_score:
                best_synthesis = iteration["synthesis"]
                best_score = iteration["meta_score"]
            elif not best_synthesis:
                best_synthesis = iteration["synthesis"]
                best_score = iteration["meta_score"]

            if iteration["meta_score"] >= quality_threshold:
                iteration["stopped_reason"] = "quality_threshold_reached"
                break

        elapsed = round(time.time() - start_time, 1)

        result = {
            "pergunta": pergunta,
            "resposta_final": best_synthesis,
            "score_final": best_score,
            "iterations": len(iterations),
            "max_iterations": max_iterations,
            "quality_threshold": quality_threshold,
            "convergiu": best_score >= quality_threshold,
            "consultores": [
                {"id": a.id, "nome": a.nome_exibicao, "categoria": a.categoria, "tier": a.tier}
                for a in agentes
            ],
            "detalhes_iteracoes": iterations,
            "tempo_total_segundos": elapsed,
            "timestamp": datetime.now().isoformat(),
        }

        self.history.append(result)
        return result

    def _run_iteration(self, pergunta, agentes, iteration_num, previous_synthesis, previous_criticisms):
        """Executa uma iteracao do loop."""

        # === FASE 1: GERAR ===
        responses = []
        for ag in agentes:
            context = f"Voce e {ag.nome_exibicao}, {ag.titulo}."
            if previous_synthesis:
                context += f"\n\nNa rodada anterior, a sintese foi:\n{previous_synthesis[:500]}"
                if previous_criticisms:
                    crits = "\n".join([f"- {c['critic']}: {c['criticism'][:200]}" for c in previous_criticisms[:3]])
                    context += f"\n\nCriticas recebidas:\n{crits}"
                context += "\n\nMELHORE sua resposta considerando as criticas acima."

            prompt = f"Responda com profundidade e especificidade: {pergunta}\nMax 200 palavras. Inclua dados concretos quando possivel."

            resp = chamar_llm_conversa(context, prompt, modelo="rapido", max_tokens=400)
            if resp:
                responses.append({"agent": ag, "response": resp})

        # === FASE 2: AVALIAR (cross-evaluation) ===
        scored_responses = []
        evaluator = random.choice(agentes)

        for r in responses:
            if r["agent"].id == evaluator.id:
                score = 6.0  # auto-avaliacao com desconto
            else:
                score_prompt = (
                    f'Avalie esta resposta sobre "{pergunta}" numa escala 0-10.\n'
                    f"Criterios: Especificidade, Acionabilidade, Originalidade, Fundamentacao.\n\n"
                    f"Resposta de {r['agent'].nome_exibicao}:\n{r['response'][:400]}\n\n"
                    f"Responda APENAS com um numero de 0 a 10."
                )

                score_resp = chamar_llm_conversa(
                    f"Voce e {evaluator.nome_exibicao}, avaliador rigoroso.",
                    score_prompt, modelo="rapido", max_tokens=10
                )
                try:
                    digits = "".join(c for c in (score_resp or "6") if c.isdigit() or c == ".")
                    score = float(digits) if digits else 6.0
                    score = min(10, max(0, score))
                except Exception:
                    score = 6.0

            scored_responses.append({
                "agent_id": r["agent"].id,
                "agent_name": r["agent"].nome_exibicao,
                "categoria": r["agent"].categoria,
                "response": r["response"],
                "score": score,
            })

        scored_responses.sort(key=lambda x: x["score"], reverse=True)

        # === FASE 3: CRITICAR ===
        critic = random.choice([a for a in agentes if a.id != evaluator.id])
        criticisms = []

        for sr in scored_responses[:3]:
            crit_prompt = (
                f'Como critico rigoroso, aponte UMA falha ou lacuna nesta resposta sobre "{pergunta}":\n\n'
                f"{sr['agent_name']}: {sr['response'][:300]}\n\n"
                f"Em 1-2 frases, qual o ponto cego ou erro?"
            )

            crit = chamar_llm_conversa(
                f"Voce e {critic.nome_exibicao}, critico implacavel mas construtivo.",
                crit_prompt, modelo="rapido", max_tokens=100
            )
            if crit:
                criticisms.append({
                    "critic": critic.nome_exibicao,
                    "target": sr["agent_name"],
                    "criticism": crit,
                })

        # === FASE 4: SINTETIZAR ===
        if not scored_responses:
            # Fallback: usar respostas da iteracao anterior se nenhuma nova
            return {
                "iteration": iteration_num,
                "responses": [],
                "criticisms": criticisms,
                "synthesis": previous_synthesis or "Sem respostas para sintetizar",
                "meta_score": 5.0,
                "evaluator": evaluator.nome_exibicao if evaluator else "?",
                "critic": critic.nome_exibicao if critic else "?",
            }

        all_responses = "\n\n".join([
            f"**{sr['agent_name']}** (score {sr['score']}):\n{sr['response'][:300]}"
            for sr in scored_responses
        ])
        all_criticisms = "\n".join([
            f"- {c['critic']} sobre {c['target']}: {c['criticism']}"
            for c in criticisms
        ])

        synth_prompt = (
            f"Sintetize as melhores ideias sobre: {pergunta}\n\n"
            f"RESPOSTAS DOS CONSULTORES:\n{all_responses}\n\n"
            f"CRITICAS:\n{all_criticisms}\n\n"
            f"Produza uma sintese executiva que:\n"
            f"1. Integre os melhores insights\n"
            f"2. Resolva as criticas apontadas\n"
            f"3. Seja acionavel e especifica\n"
            f"4. Max 300 palavras"
        )

        synthesis = chamar_llm_conversa(
            "Voce e o sintetizador da Vila INTEIA. Combine perspectivas divergentes em recomendacao coesa.",
            synth_prompt, modelo="rapido", max_tokens=600
        )

        # === FASE 5: META-AVALIAR ===
        meta_prompt = (
            f'Avalie esta sintese sobre "{pergunta}" de 0 a 10:\n'
            f"{(synthesis or '')[:500]}\n\n"
            f"Criterios: Completude, Acionabilidade, Fundamentacao, Clareza.\n"
            f"Responda APENAS com um numero."
        )

        meta_resp = chamar_llm_conversa(
            "Voce e um avaliador academico rigoroso.",
            meta_prompt, modelo="rapido", max_tokens=10
        )
        try:
            digits = "".join(c for c in (meta_resp or "6") if c.isdigit() or c == ".")
            meta_score = float(digits) if digits else 6.0
            meta_score = min(10, max(0, meta_score))
        except Exception:
            meta_score = 6.0

        return {
            "iteration": iteration_num,
            "responses": scored_responses,
            "criticisms": criticisms,
            "synthesis": synthesis or "Sintese indisponivel",
            "meta_score": meta_score,
            "evaluator": evaluator.nome_exibicao,
            "critic": critic.nome_exibicao,
        }

    def _selecionar_agentes(self, n, categorias=None):
        """Seleciona agentes diversos para o loop."""
        candidatos = list(self.sim.personas.values())
        if categorias:
            filtrados = [p for p in candidatos if p.categoria in categorias]
            if filtrados:
                candidatos = filtrados

        # Priorizar Tier S + diversidade de categorias
        tier_s = [p for p in candidatos if p.tier == "S"]
        outros = [p for p in candidatos if p.tier != "S"]
        random.shuffle(tier_s)
        random.shuffle(outros)

        selected = []
        cats_seen = set()
        for p in tier_s + outros:
            if len(selected) >= n:
                break
            if p.categoria not in cats_seen or len(selected) < n:
                selected.append(p)
                cats_seen.add(p.categoria)

        return selected
