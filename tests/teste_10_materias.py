"""
Teste prático: 10 matérias rodando na Vila INTEIA.
Valida previsibilidade, autoresearch, echo detection, feedback loop.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
os.environ["OMNIROUTE_API_KEY"] = ""  # Desabilitar IA para teste rapido
os.environ["CLAUDE_API_KEY"] = ""

from engine.simulacao import SimulacaoVila
from config import config

MATERIAS = [
    "IA vai substituir advogados no Brasil ate 2030",
    "Reforma tributaria e o impacto nas startups brasileiras",
    "Elon Musk deveria ser regulado como monopolio global",
    "Educacao publica brasileira precisa de revolucao tecnologica",
    "Criptomoedas vao substituir o Real em 10 anos",
    "Democracia direta digital e viavel para o Brasil",
    "Aquecimento global vai transformar o Nordeste em deserto",
    "China ja superou os EUA em inteligencia artificial",
    "Saude mental e a maior crise do seculo 21",
    "Brasil pode ser potencia militar com drones autonomos",
]


def rodar():
    print("\n" + "=" * 70)
    print("  TESTE PRÁTICO — 10 MATÉRIAS NA VILA INTEIA")
    print("=" * 70)

    sim = SimulacaoVila(nome="teste_10_materias")
    sim.inicializar(max_agentes=50)
    print(f"\n  {len(sim.personas)} agentes carregados")

    # Injetar as 10 matérias
    for i, materia in enumerate(MATERIAS):
        sim.injetar_topico(materia, importancia=8)
        print(f"  [{i+1:2d}] {materia}")

    print(f"\n  Rodando 150 steps...")
    print(f"  Previsibilidade a cada 50 steps")
    print(f"  Autoresearch a cada 100 steps")
    print(f"  Sintese a cada 10 steps")
    print("-" * 70)

    resultados = {
        "conversas": 0,
        "sinteses": [],
        "posts_feed": 0,
        "autoresearch": [],
        "tendencias": [],
        "echo_detectados": 0,
        "briefings": [],
    }

    t0 = time.time()

    for step_num in range(150):
        resumo = sim.executar_step()

        n_conv = len(resumo.get("conversas", []))
        resultados["conversas"] += n_conv

        # Sinteses
        for ins in resumo.get("insights", []):
            tema = ins.get("topico", "?")
            conf = ins.get("confianca", 0)
            divs = ins.get("divergencias", [])
            echo = any("ECHO" in d for d in divs)
            if echo:
                resultados["echo_detectados"] += 1
            resultados["sinteses"].append({
                "step": sim.step,
                "topico": tema[:40],
                "confianca": round(conf, 2),
                "echo": echo,
                "participantes": len(ins.get("participantes", [])),
            })
            print(f"  Step {sim.step:3d} | SINTESE: {tema[:35]:35s} | conf={conf:.2f} {'ECHO!' if echo else ''}")

        # Briefing preditivo
        if resumo.get("briefing_preditivo"):
            b = resumo["briefing_preditivo"]
            resultados["briefings"].append(b)
            emergentes = [t["topico"] for t in b.get("emergentes", [])]
            saturando = [t["topico"] for t in b.get("saturando", [])]
            if emergentes or saturando:
                print(f"  Step {sim.step:3d} | BRIEFING: emergentes={emergentes[:2]} saturando={saturando[:2]}")

        # Autoresearch
        if resumo.get("autoresearch"):
            ar = resumo["autoresearch"]
            resultados["autoresearch"].append({
                "step": sim.step,
                "tema": ar.get("tema_original", "?"),
                "ciclos": ar.get("total_ciclos", 0),
                "descoberta": ar.get("descoberta_principal", "?")[:80],
            })
            print(f"  Step {sim.step:3d} | AUTORESEARCH: {ar.get('tema_original','?')[:40]}")
            print(f"           | Descoberta: {ar.get('descoberta_principal','?')[:60]}")

    tempo = time.time() - t0
    resultados["posts_feed"] = sim.rede_social.total_posts
    resultados["tendencias"] = [
        t.to_dict() for t in sim.motor_previsibilidade.tendencias[:5]
    ]

    # Relatório final
    print("\n" + "=" * 70)
    print("  RELATÓRIO FINAL")
    print("=" * 70)

    print(f"\n  Tempo total: {tempo:.1f}s ({tempo/150:.2f}s/step)")
    print(f"  Steps: {sim.step}")
    print(f"  Conversas: {resultados['conversas']}")
    print(f"  Posts no feed: {resultados['posts_feed']}")
    print(f"  Comentarios: {sim.rede_social.total_comentarios}")
    print(f"  Reacoes: {sim.rede_social.total_reacoes}")
    print(f"  Sinteses geradas: {len(resultados['sinteses'])}")
    print(f"  Echo/groupthink detectado: {resultados['echo_detectados']}x")
    print(f"  Autoresearch executados: {len(resultados['autoresearch'])}")
    print(f"  Briefings preditivos: {len(resultados['briefings'])}")
    print(f"  Topicos ativos final: {len(config.topicos_ativos)}")

    # Top sinteses
    if resultados["sinteses"]:
        print(f"\n  --- SÍNTESES ({len(resultados['sinteses'])}) ---")
        for s in resultados["sinteses"][:10]:
            echo_tag = " [ECHO!]" if s["echo"] else ""
            print(f"    Step {s['step']:3d} | {s['topico']:35s} | conf={s['confianca']:.2f} | {s['participantes']}p{echo_tag}")

    # Autoresearch
    if resultados["autoresearch"]:
        print(f"\n  --- AUTORESEARCH ({len(resultados['autoresearch'])}) ---")
        for ar in resultados["autoresearch"]:
            print(f"    Step {ar['step']:3d} | {ar['tema'][:40]}")
            print(f"             | {ar['descoberta']}")

    # Tendencias
    if resultados["tendencias"]:
        print(f"\n  --- TENDÊNCIAS ---")
        for t in resultados["tendencias"]:
            print(f"    {t['direcao']:12s} | {t['topico']:25s} | forca={t['forca']:.2f}")

    # Topicos ativos
    print(f"\n  --- TÓPICOS ATIVOS ({len(config.topicos_ativos)}) ---")
    for t in config.topicos_ativos[:15]:
        print(f"    • {t[:60]}")

    # Salvar resultado completo
    output = {
        "materias_originais": MATERIAS,
        "stats": sim.stats,
        "resultados": resultados,
        "topicos_ativos_final": config.topicos_ativos,
    }
    with open("resultado_10_materias.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Resultado salvo em resultado_10_materias.json")

    return resultados


if __name__ == "__main__":
    rodar()
