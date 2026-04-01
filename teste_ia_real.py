"""
Teste com IA real via proxy de producao.
3 materias, 5 consultores, autoresearch completo.
"""

import sys
import os
import json
import time
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Usar proxy de producao em vez de OmniRoute local
PROXY_URL = "https://api.inteia.com.br/api/v1/vila-inteia/chat"

import requests

def chamar_ia_producao(system_prompt, user_prompt, max_tokens=150):
    """Chama IA via proxy de producao."""
    try:
        msgs = [{"role": "user", "content": f"[INSTRUCAO]\n{system_prompt}\n\n[TAREFA]\n{user_prompt}"}]
        r = requests.post(PROXY_URL, json={
            "model": "BestFREE",
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": 0.8,
            "stream": False,
        }, timeout=15)
        if r.status_code == 200:
            d = r.json()
            if d.get("choices") and d["choices"][0]["message"].get("content"):
                return d["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"    [ERRO IA] {e}")
        return None


from engine.persona import carregar_todas_personas

MATERIAS = [
    "IA vai substituir advogados no Brasil ate 2030",
    "Democracia direta digital e viavel para o Brasil",
    "Saude mental e a maior crise do seculo 21",
]


def rodar():
    print("\n" + "=" * 70)
    print("  TESTE COM IA REAL — 3 MATÉRIAS VIA PROXY PRODUÇÃO")
    print("=" * 70)

    # Carregar personas
    caminhos = [
        "data/banco-consultores-lendarios.json",
        os.path.join(os.path.dirname(__file__), "data", "banco-consultores-lendarios.json"),
    ]
    personas_lista = None
    for c in caminhos:
        if os.path.exists(c):
            personas_lista = carregar_todas_personas(c)
            break
    if not personas_lista:
        print("  ERRO: banco de consultores nao encontrado")
        return

    personas = {p.id: p for p in personas_lista[:50]}
    print(f"  {len(personas)} consultores carregados\n")

    for idx, materia in enumerate(MATERIAS):
        print(f"  {'='*60}")
        print(f"  MATÉRIA {idx+1}: {materia}")
        print(f"  {'='*60}")

        # Selecionar 5 consultores relevantes
        palavras = set(w for w in materia.lower().split() if len(w) > 3)
        scored = []
        for pid, p in personas.items():
            if pid == "IGOR001":
                continue
            d = p.dados_consultor
            exp = " ".join(d.get("areas_expertise") or []).lower()
            tags = " ".join(d.get("tags") or []).lower()
            bio = (d.get("biografia_resumida") or "").lower()
            score = sum(3.0 if w in exp else 2.0 if w in tags else 1.0 if w in bio else 0 for w in palavras)
            score += {"S": 2, "A": 1, "B": 0.3}.get(d.get("tier", "C"), 0)
            if score > 0:
                scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        respondentes = [p for p, _ in scored[:5]]

        if len(respondentes) < 3:
            # Fallback: pegar os 5 tier S
            tier_s = [p for p in personas.values() if p.dados_consultor.get("tier") == "S"][:5]
            respondentes = tier_s

        print(f"\n  Consultores selecionados:")
        for r in respondentes:
            print(f"    • {r.nome_exibicao} ({r.categoria}, tier {r.dados_consultor.get('tier','?')})")

        # Coletar respostas
        print(f"\n  Coletando respostas...")
        respostas = []
        for r in respondentes:
            system = (
                f"Voce e {r.nome_exibicao}. {r.dados_consultor.get('titulo','')}. "
                f"{r.dados_consultor.get('personalidade_resumo','')} "
                f"Responda na sua voz unica, direto ao ponto."
            )
            user = (
                f"PESQUISA PROFUNDA sobre: \"{materia}\"\n\n"
                f"Responda em 3-4 frases. Inclua: (1) sua analise, "
                f"(2) um dado ou referencia, (3) uma pergunta que aprofunde."
            )
            resp = chamar_ia_producao(system, user)
            if resp:
                respostas.append({"nome": r.nome_exibicao, "cat": r.categoria, "texto": resp})
                print(f"    [{r.nome_exibicao[:15]:15s}] {resp[:80]}...")
            else:
                print(f"    [{r.nome_exibicao[:15]:15s}] (sem resposta)")

        if len(respostas) < 2:
            print("  Poucas respostas, pulando materia\n")
            continue

        # Helena sintetiza
        print(f"\n  Helena sintetizando {len(respostas)} respostas...")
        ctx = "\n\n".join(f"{r['nome']}: {r['texto']}" for r in respostas)
        sintese = chamar_ia_producao(
            "Voce e Helena Strategos, cientista-chefe da INTEIA. Neutra, analitica, Socratica.",
            f"SINTESE DE PESQUISA sobre \"{materia}\".\n\nRespostas:\n{ctx}\n\n"
            f"Gere: (1) DESCOBERTA PRINCIPAL em 1 frase, (2) CONVERGENCIAS, "
            f"(3) DIVERGENCIAS, (4) NIVEL DE SATURACAO (0-100%), "
            f"(5) 2 PERGUNTAS para proximo ciclo.",
            max_tokens=200,
        )

        if sintese:
            print(f"\n  SÍNTESE HELENA:")
            for linha in sintese.split("\n"):
                if linha.strip():
                    print(f"    {linha.strip()}")

            # Detectar echo
            textos = [r["texto"].lower().split() for r in respostas]
            sims = []
            for i in range(len(textos)):
                for j in range(i+1, len(textos)):
                    a, b = set(textos[i]), set(textos[j])
                    u = a | b
                    sims.append(len(a & b) / len(u) if u else 0)
            media_sim = sum(sims) / len(sims) if sims else 0
            echo = media_sim > 0.4
            print(f"\n    Similaridade média: {media_sim:.0%} {'ECHO!' if echo else 'OK — diversidade real'}")

            # Extrair perguntas
            perguntas = [l.strip() for l in sintese.split("\n") if "?" in l and len(l) > 20][:2]
            if perguntas:
                print(f"    Perguntas para próximo ciclo:")
                for p in perguntas:
                    print(f"      → {p[:70]}")
        else:
            print("  (Helena nao conseguiu sintetizar)")

        print()

    print(f"\n{'='*70}")
    print(f"  TESTE CONCLUÍDO — {len(MATERIAS)} matérias processadas com IA real")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    rodar()
