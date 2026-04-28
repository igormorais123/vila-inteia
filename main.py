"""
Vila INTEIA - Entry Point.

Modos de execução:
    1. CLI: python -m vila-inteia.main --steps 100
    2. API: python -m vila-inteia.main --serve
    3. Demo: python -m vila-inteia.main --demo
"""

from __future__ import annotations

import argparse
import sys
import os
import time

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.simulacao import SimulacaoVila
from config import config


def banner():
    """Exibe banner da Vila INTEIA."""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║    ██╗   ██╗██╗██╗      █████╗                   ║
    ║    ██║   ██║██║██║     ██╔══██╗                  ║
    ║    ██║   ██║██║██║     ███████║                  ║
    ║    ╚██╗ ██╔╝██║██║     ██╔══██║                  ║
    ║     ╚████╔╝ ██║███████╗██║  ██║                  ║
    ║      ╚═══╝  ╚═╝╚══════╝╚═╝  ╚═╝                  ║
    ║                                                  ║
    ║     I N T E I A  -  Think Tank Vivo              ║
    ║     144 Consultores Lendarios em Simulacao       ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝
    """)


def modo_cli(args):
    """Executa simulação via CLI com output no terminal."""
    banner()
    config.modo_debug = args.debug

    print(f"Inicializando com {args.agentes} agentes...")
    sim = SimulacaoVila(nome=args.nome)
    sim.inicializar(max_agentes=args.agentes)
    print(f"  {len(sim.personas)} agentes carregados")
    print(f"  19 locais no Campus INTEIA")
    print(f"  Hora inicial: {sim.hora_atual.strftime('%d/%m/%Y %H:%M')}")
    print()

    if args.topico:
        sim.injetar_topico(args.topico)
        print(f"  Topico injetado: '{args.topico}'")
        print()

    print(f"Executando {args.steps} steps...")
    print("=" * 60)

    for i in range(args.steps):
        resumo = sim.executar_step()

        # Exibir conversas
        for conv in resumo["conversas"]:
            print(f"\n  💬 CONVERSA em {conv['local_id']}:")
            print(f"     {conv['parceiro_nome']} ↔ {conv.get('tipo_relacao', 'colega')}")
            print(f"     Tópico: {conv['topico']}")
            for nome, fala in conv.get("turnos", [])[:3]:
                print(f"     {nome}: \"{fala[:80]}...\"" if len(fala) > 80 else f"     {nome}: \"{fala}\"")

        # Exibir insights
        for insight in resumo.get("insights", []):
            print(f"\n  🧠 SÍNTESE: {insight.get('topico', 'N/A')}")
            print(f"     Participantes: {', '.join(insight.get('participantes', [])[:5])}")
            print(f"     Confiança: {insight.get('confianca', 0):.0%}")

        # Status periódico
        if (i + 1) % 10 == 0:
            mapa = sim.mapa_calor()
            top_locais = sorted(mapa.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\n  📊 Step {sim.step} | {sim.hora_atual.strftime('%H:%M')} | "
                  f"Conversas: {sim.stats['total_conversas']} | "
                  f"Reflexões: {sim.stats['total_reflexoes']}")
            for local_id, count in top_locais:
                if count > 0:
                    print(f"     {local_id}: {count} agentes")

    print("\n" + "=" * 60)
    print(f"Simulação concluída: {sim.step} steps")
    print(f"  Conversas: {sim.stats['total_conversas']}")
    print(f"  Reflexões: {sim.stats['total_reflexoes']}")
    print(f"  Movimentos: {sim.stats['total_movimentos']}")
    print(f"  Sínteses: {sim.stats['total_sinteses']}")

    sim.salvar()
    print(f"\nEstado salvo em: {sim.dir_dados}")


def modo_serve(args):
    """Inicia servidor FastAPI."""
    banner()

    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
        from api.rotas_vila import router
        from api.rotas_rede_social import router as rede_router
        from api.rotas_colmeia import router as colmeia_router
        from api.rotas_harness import router as harness_router
        from api.rotas_vivos import router as vivos_router
        try:
            from api.rotas_gametheory import router as gametheory_router
        except ImportError:
            gametheory_router = None
        try:
            from api.rotas_psicohistoria import router as psicohistoria_router
        except ImportError:
            psicohistoria_router = None
        try:
            from api.rotas_proveniencia import router as proveniencia_router
        except ImportError:
            proveniencia_router = None
        try:
            from api.rotas_health import router as health_router
        except ImportError:
            health_router = None
        try:
            from api.rotas_grafo import router as grafo_router
        except ImportError:
            grafo_router = None
        try:
            from api.rotas_metrics import router as metrics_router
        except ImportError:
            metrics_router = None
        try:
            from api.rotas_llm import router as llm_router
        except ImportError:
            llm_router = None
        try:
            from api.rotas_mirofish import router as mirofish_router
        except ImportError:
            mirofish_router = None
    except ImportError as e:
        print(f"Erro: {e}")
        print("Instale as dependencias: pip install -r requirements.txt")
        sys.exit(1)

    app = FastAPI(
        title="Vila INTEIA - Think Tank Vivo",
        description="Simulação de 151 consultores lendários",
        version="1.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Onda 49: auth + rate limit middleware
    try:
        from engine.auth import middleware_auth_rate
        app.middleware("http")(middleware_auth_rate)
    except Exception:
        pass

    app.include_router(router)
    app.include_router(rede_router)
    app.include_router(colmeia_router)
    app.include_router(harness_router)
    app.include_router(vivos_router)
    if gametheory_router is not None:
        app.include_router(gametheory_router)
    if psicohistoria_router is not None:
        app.include_router(psicohistoria_router)
    if proveniencia_router is not None:
        app.include_router(proveniencia_router)
    if health_router is not None:
        app.include_router(health_router)
    if grafo_router is not None:
        app.include_router(grafo_router)
    if metrics_router is not None:
        app.include_router(metrics_router)
    if llm_router is not None:
        app.include_router(llm_router)
    if mirofish_router is not None:
        app.include_router(mirofish_router)

    # Servir frontend estatico
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    # PORT do ambiente (Render) sobrescreve argumento
    try:
        port = int(os.environ.get("PORT", args.port))
    except (ValueError, TypeError):
        port = args.port

    print(f"Servidor Vila INTEIA em http://localhost:{port}")
    print(f"  API docs: http://localhost:{port}/docs")
    print(f"  Frontend: http://localhost:{port}/")

    uvicorn.run(app, host="0.0.0.0", port=port)


def modo_demo(args):
    """Executa demo rápido com 10 agentes e 20 steps."""
    banner()
    print("MODO DEMO - 10 agentes, 20 steps\n")

    config.modo_debug = True

    sim = SimulacaoVila(nome="demo")
    sim.inicializar(max_agentes=10)

    # Injetar tópico
    sim.injetar_topico("futuro da inteligência artificial no Brasil")

    print(f"Agentes na demo:")
    for p in sim.personas.values():
        print(f"  {p.rascunho.acao.emoji} {p.nome_exibicao} ({p.categoria}) "
              f"→ {p.rascunho.local_atual}")
    print()

    sim.executar(n_steps=20)

    print(f"\n{'='*60}")
    print("RESULTADO DA DEMO")
    print(f"{'='*60}")

    estado = sim.estado_mundo()
    for local in estado["locais"]:
        if local["ocupacao"] > 0:
            print(f"\n📍 {local['nome']} ({local['ocupacao']} agentes):")
            for ag in local["agentes"]:
                print(f"   {ag['emoji']} {ag['nome']}: {ag['acao']}")

    if sim.conversas_recentes:
        print(f"\n💬 Conversas ({len(sim.conversas_recentes)}):")
        for conv in sim.conversas_recentes[-3:]:
            print(f"   • {conv['parceiro_nome']} sobre '{conv['topico']}'")

    print(f"\n📊 Stats: {sim.stats}")


def modo_mirofish(args):
    """Executa pipeline Mirofish-style: corpus → grafo → simulação → relatório.

    Onda 197: wrapping Vila backtest em API-compatible Mirofish.
    Produz JSON com {grafo, simulacao, relatorio}.
    """
    import json
    from pathlib import Path
    from engine.mirofish_style import pipeline_completo

    banner()
    print("MODO MIROFISH - pipeline corpus → grafo → sim → relatório\n")

    persona_ids = [p.strip() for p in args.personas.split(",")]
    sim = SimulacaoVila(nome="mirofish")
    sim.inicializar(max_agentes=len(persona_ids) * 2)

    # Garante que persona_ids requeridos estejam carregados (inicializar pode
    # pegar outros aleatórios). Se faltou, recarrega do banco.
    faltantes = [pid for pid in persona_ids if pid not in sim.personas]
    if faltantes:
        print(f"⚠  personas não carregadas por inicializar: {faltantes}")
        print("   recarregando direto do banco...")
        from engine.persona import Persona
        with open(Path(__file__).parent / "data" / "banco-consultores-lendarios.json") as f:
            banco = json.load(f)
        for p in banco:
            if p["id"] in faltantes:
                sim.personas[p["id"]] = Persona(dados_consultor=p)

    print(f"Personas panel: {persona_ids}")
    print(f"Datasets glob:  data/backtest/{args.datasets}")
    print()

    out = pipeline_completo(
        base_dir="data/backtest",
        dataset_glob=args.datasets,
        persona_ids=persona_ids,
        sim=sim,
        llm_fn=None,  # usa chamar_llm default (OmniRoute/Groq)
    )

    if "erro" in out:
        print(f"❌ erro: {out['erro']}")
        sys.exit(1)

    res = out["simulacao"]["resultado"]
    print(f"\n{'='*60}")
    print("RELATÓRIO EXECUTIVO")
    print(f"{'='*60}")
    print(out["relatorio"]["conteudo"])
    print(f"\n--- MÉTRICAS ---")
    bv = res.get("brier_vila_avg")
    bp = res.get("brier_prior_avg")
    sk = res.get("skill_brier_vs_prior")
    if bv is None:
        print("  ⚠  LLM offline ou sem chave (GROQ_API_KEY/CLAUDE_API_KEY)")
        print("     Configure provider ou injete llm_fn no pipeline_completo()")
    else:
        print(f"  acc: {100*res['acc_total']:.1f}%")
        print(f"  brier vila:  {bv:.4f}")
        print(f"  brier prior: {bp:.4f}" if bp is not None else "  brier prior: N/A")
        print(f"  skill:       {(sk or 0)*100:+.1f}%")
    print(f"\n--- INSIGHTS ---")
    for ins in out["relatorio"]["insights"]:
        print(f"  [{ins['tipo']}] {len(ins['items'])} items")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n✓ saída: {out_path}")


def modo_factor_bench(args):
    """Onda 242: factor models real bench Q1 2026 events."""
    from pathlib import Path
    from engine.micro_events import gerar_500_micro_events_q1_2026
    from engine.market_data import resolve_micro_events_market
    from engine.factor_models import evaluate_strategy_on_events

    banner()
    print("MODO FACTOR-BENCH - Vila vs market factor models\n")
    strategies = [s.strip() for s in args.strategies.split(",")]

    events = gerar_500_micro_events_q1_2026()
    market = [e for e in events if e.category in ("stock_price_up", "crypto_price_up")]
    print(f"Resolving {len(market)} market events via Yahoo Finance...")
    resolve_micro_events_market(market)
    resolved = [e for e in market if e.real_outcome is not None]
    print(f"Resolved: {len(resolved)}/{len(market)}\n")

    lines = ["# Vila Factor Models Benchmark", "", f"**N**: {len(resolved)} events Q1 2026", "",
             "| Strategy | Hits | Acc | Brier |", "|---|---|---|---|"]
    print(f"{'strategy':18s} hits   acc      brier")
    for s in strategies:
        try:
            r = evaluate_strategy_on_events(resolved, s)
        except ValueError:
            print(f"  {s:18s} unknown strategy")
            continue
        line = f"{s:18s} {r['hits']:>3d}/{r['n']:<3d} {r['acc']*100:>5.1f}%  {r['brier']:.4f}"
        print(line)
        lines.append(f"| {s} | {r['hits']}/{r['n']} | {r['acc']*100:.1f}% | {r['brier']:.4f} |")

    out_path = Path(args.out_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"\n✓ markdown: {out_path}")


def modo_factor_autoresearch(args):
    """Onda 242: Karpathy autoresearch ensemble weights grid sobre factor models."""
    import itertools
    from pathlib import Path
    from engine.micro_events import gerar_500_micro_events_q1_2026
    from engine.market_data import resolve_micro_events_market
    from engine.factor_models import (
        momentum_predictor, mean_reversion_predictor, rsi_predictor, _resolve_symbol,
    )

    banner()
    print("MODO FACTOR-AUTORESEARCH - Karpathy ensemble grid\n")
    step = args.grid_step

    events = gerar_500_micro_events_q1_2026()
    market = [e for e in events if e.category in ("stock_price_up", "crypto_price_up")]
    print(f"Resolving {len(market)} events...")
    resolve_micro_events_market(market)
    resolved = [e for e in market if e.real_outcome is not None]
    print(f"Resolved: {len(resolved)}\n")

    # Pre-compute strategy preds
    print("Pre-computing strategy preds...")
    preds = []
    for e in resolved:
        parts = e.event_id.split("_")
        if len(parts) < 2:
            continue
        sym = _resolve_symbol(e.category, parts[1])
        try:
            pm = momentum_predictor(sym, e.date)
            pmr = mean_reversion_predictor(sym, e.date)
            pr = rsi_predictor(sym, e.date)
            preds.append((pm, pmr, pr, e.real_outcome))
        except Exception:
            pass
    print(f"Computed {len(preds)} preds\n")

    # Grid search
    weights_set = set()
    n_steps = int(1 / step) + 1
    for w1, w2, w3, w4 in itertools.product([i * step for i in range(n_steps)], repeat=4):
        s = w1 + w2 + w3 + w4
        if s == 0:
            continue
        weights_set.add((round(w1/s, 4), round(w2/s, 4), round(w3/s, 4), round(w4/s, 4)))
    weights = sorted(weights_set)
    print(f"Karpathy autoresearch: {len(weights)} weight combos")

    best = (1.0, None, 0)
    for w_mom, w_mr, w_rsi, w_bl in weights:
        hits = 0; brier_sum = 0
        for pm, pmr, pr, real in preds:
            p = w_mom * pm + w_mr * pmr + w_rsi * pr + w_bl * 0.50
            if (p >= 0.5) == bool(real):
                hits += 1
            brier_sum += (p - real) ** 2
        avg_brier = brier_sum / len(preds)
        if avg_brier < best[0]:
            best = (avg_brier, (w_mom, w_mr, w_rsi, w_bl), hits)

    w = best[1]
    print(f"\n=== BEST ensemble ===")
    print(f"  weights: mom={w[0]:.3f} mr={w[1]:.3f} rsi={w[2]:.3f} bl={w[3]:.3f}")
    print(f"  acc: {best[2]}/{len(preds)} = {best[2]/len(preds)*100:.1f}%")
    print(f"  brier: {best[0]:.4f}")

    lines = [
        "# Vila Factor Autoresearch — Karpathy Ensemble", "",
        f"**N**: {len(preds)} events · **Combos**: {len(weights)}", "",
        f"## Best Ensemble Weights",
        f"- momentum: {w[0]:.3f}", f"- mean_reversion: {w[1]:.3f}",
        f"- rsi: {w[2]:.3f}", f"- baseline: {w[3]:.3f}", "",
        f"**Acc**: {best[2]}/{len(preds)} = {best[2]/len(preds)*100:.1f}%",
        f"**Brier**: {best[0]:.4f}",
    ]
    out_path = Path(args.out_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"\n✓ markdown: {out_path}")


def modo_benchmark(args):
    """Onda 228: Benchmark Vila vs 4 baselines (prior, chance, majority, random).

    Output: markdown report + JSON metrics estilo Mirofish public benchmarks.
    """
    import json
    from pathlib import Path
    from engine.benchmark import rodar_benchmark, formatar_relatorio
    from engine.persona import Persona

    banner()
    print("MODO BENCHMARK - Vila vs baselines\n")

    persona_ids = [p.strip() for p in args.personas.split(",")]
    sim = SimulacaoVila(nome="benchmark")
    sim.inicializar(max_agentes=len(persona_ids) * 2)

    # Garante personas requeridas
    faltantes = [pid for pid in persona_ids if pid not in sim.personas]
    if faltantes:
        with open(Path(__file__).parent / "data" / "banco-consultores-lendarios.json") as f:
            banco = json.load(f)
        for p in banco:
            if p["id"] in faltantes:
                sim.personas[p["id"]] = Persona(dados_consultor=p)

    persona_nomes = {pid: sim.personas[pid].nome_exibicao for pid in persona_ids}

    print(f"Personas: {persona_ids}")
    print(f"Datasets: data/backtest/*.csv\n")

    bench = rodar_benchmark(
        sim=sim, persona_ids=persona_ids, persona_nomes=persona_nomes,
        base_dir="data/backtest",
    )

    # Print report
    report_md = formatar_relatorio(bench)
    print(report_md)

    # Save outputs
    md_path = Path(args.out_md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(report_md)

    json_path = Path(args.out_json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    # Strip preds_real lists from output (too big)
    bench_clean = {**bench, "baselines": {k: {kk: vv for kk, vv in v.items()}
                                          for k, v in bench["baselines"].items()}}
    json_path.write_text(json.dumps(bench_clean, indent=2, default=str))

    print(f"\n✓ markdown: {md_path}")
    print(f"✓ json:     {json_path}")


def modo_live(args):
    """Vila INTEIA 24/7 — servidor + simulação contínua em background."""
    banner()

    import threading

    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
        from api.rotas_vila import router, obter_simulacao
        from api.rotas_rede_social import router as rede_router
        from api.rotas_colmeia import router as colmeia_router
        from api.rotas_harness import router as harness_router
        from api.rotas_vivos import router as vivos_router
        try:
            from api.rotas_gametheory import router as gametheory_router
        except ImportError:
            gametheory_router = None
        try:
            from api.rotas_psicohistoria import router as psicohistoria_router
        except ImportError:
            psicohistoria_router = None
        try:
            from api.rotas_proveniencia import router as proveniencia_router
        except ImportError:
            proveniencia_router = None
        try:
            from api.rotas_health import router as health_router
        except ImportError:
            health_router = None
        try:
            from api.rotas_grafo import router as grafo_router
        except ImportError:
            grafo_router = None
        try:
            from api.rotas_metrics import router as metrics_router
        except ImportError:
            metrics_router = None
        try:
            from api.rotas_llm import router as llm_router
        except ImportError:
            llm_router = None
        try:
            from api.rotas_mirofish import router as mirofish_router
        except ImportError:
            mirofish_router = None
    except ImportError as e:
        print(f"Erro: {e}")
        sys.exit(1)

    app = FastAPI(
        title="Vila INTEIA - Think Tank Vivo 24/7",
        version="2.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Onda 49: auth + rate limit
    try:
        from engine.auth import middleware_auth_rate
        app.middleware("http")(middleware_auth_rate)
    except Exception:
        pass
    app.include_router(router)
    app.include_router(rede_router)
    app.include_router(colmeia_router)
    app.include_router(harness_router)
    app.include_router(vivos_router)
    if gametheory_router is not None:
        app.include_router(gametheory_router)
    if psicohistoria_router is not None:
        app.include_router(psicohistoria_router)
    if proveniencia_router is not None:
        app.include_router(proveniencia_router)
    if health_router is not None:
        app.include_router(health_router)
    if grafo_router is not None:
        app.include_router(grafo_router)
    if metrics_router is not None:
        app.include_router(metrics_router)
    if llm_router is not None:
        app.include_router(llm_router)
    if mirofish_router is not None:
        app.include_router(mirofish_router)

    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    # Inicializar simulação
    sim = obter_simulacao()
    if args.topico:
        sim.injetar_topico(args.topico)

    # Thread de simulação contínua
    def loop_continuo():
        intervalo = args.intervalo  # segundos entre steps
        print(f"\n  Vila 24/7 ATIVA — 1 step a cada {intervalo}s")
        print(f"  {len(sim.personas)} agentes vivendo no Campus INTEIA")
        print(f"  Autoresearch a cada 100 steps")
        print(f"  Previsibilidade a cada 50 steps\n")

        erros_consecutivos = 0

        while True:
            if sim.pausada:
                time.sleep(1)
                continue

            try:
                # Timeout de segurança via thread auxiliar
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(sim.executar_step)
                    try:
                        resumo = future.result(timeout=max(intervalo * 3, 180))
                    except concurrent.futures.TimeoutError:
                        print(f"  TIMEOUT step {sim.step} — pulando")
                        erros_consecutivos += 1
                        time.sleep(intervalo)
                        continue

                erros_consecutivos = 0

                # Log compacto
                n_conv = len(resumo.get("conversas", []))
                n_ins = len(resumo.get("insights", []))
                extras = []
                if resumo.get("autoresearch"):
                    extras.append("PESQUISA")
                if resumo.get("briefing_preditivo"):
                    extras.append("PREVISAO")
                if n_conv > 0 or n_ins > 0 or extras:
                    ex = f" [{', '.join(extras)}]" if extras else ""
                    print(
                        f"  Step {sim.step} "
                        f"({sim.hora_atual.strftime('%d/%m %H:%M')}) "
                        f"| {n_conv} conv | {n_ins} ins{ex}"
                    )

            except Exception as e:
                erros_consecutivos += 1
                print(f"  ERRO step {sim.step}: {e}")
                if erros_consecutivos >= 5:
                    print(f"  5 erros seguidos — pausa de 5min")
                    time.sleep(300)
                    erros_consecutivos = 0

            time.sleep(intervalo)

    thread_sim = threading.Thread(target=loop_continuo, daemon=True)
    thread_sim.start()

    # Endpoint /api/v1/vila/live já está em rotas_vila.py (sem duplicação)

    try:
        port = int(os.environ.get("PORT", args.port))
    except (ValueError, TypeError):
        port = args.port

    print(f"  Servidor: http://localhost:{port}")
    print(f"  API docs: http://localhost:{port}/docs")
    print(f"  Live: http://localhost:{port}/api/v1/vila/live")

    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    parser = argparse.ArgumentParser(
        description="Vila INTEIA - Think Tank Vivo"
    )
    subparsers = parser.add_subparsers(dest="comando")

    # Comando: run
    run_parser = subparsers.add_parser("run", help="Executar simulação CLI")
    run_parser.add_argument("--steps", type=int, default=50, help="Número de steps")
    run_parser.add_argument("--agentes", type=int, default=140, help="Número de agentes")
    run_parser.add_argument("--nome", default="vila_inteia", help="Nome da simulação")
    run_parser.add_argument("--topico", help="Tópico inicial para discussão")
    run_parser.add_argument("--debug", action="store_true", help="Modo debug")

    # Comando: serve
    serve_parser = subparsers.add_parser("serve", help="Iniciar servidor API + Frontend")
    serve_parser.add_argument("--port", type=int, default=8100, help="Porta do servidor")

    # Comando: live (24/7)
    live_parser = subparsers.add_parser("live", help="Vila 24/7: servidor + simulação contínua")
    live_parser.add_argument("--port", type=int, default=8100, help="Porta do servidor")
    live_parser.add_argument("--intervalo", type=int, default=30, help="Segundos entre steps (default: 30)")
    live_parser.add_argument("--topico", help="Tópico inicial para discussão")

    # Comando: demo
    subparsers.add_parser("demo", help="Demo rápido com 10 agentes")

    # Comando: mirofish (Onda 197)
    mirofish_parser = subparsers.add_parser(
        "mirofish",
        help="Pipeline estilo Mirofish: corpus → grafo → simulação → relatório",
    )
    mirofish_parser.add_argument("--datasets", default="*.csv",
                                 help="glob em data/backtest/ (default: *.csv)")
    mirofish_parser.add_argument("--personas", default="CL001,CL002,CL007",
                                 help="IDs panel (default: Musk/Jobs/Bezos)")
    mirofish_parser.add_argument("--out", default="data/mirofish_output.json",
                                 help="arquivo JSON saída")

    # Comando: benchmark (Onda 228) — estilo Mirofish public benchmarks
    bench_parser = subparsers.add_parser(
        "benchmark",
        help="Vila vs baselines: prior humano, chance, majority, random",
    )
    bench_parser.add_argument("--personas", default="CL001,CL002,CL007",
                              help="IDs panel (default: Musk/Jobs/Bezos)")
    bench_parser.add_argument("--out-md", default="data/benchmark_report.md",
                              help="markdown report")
    bench_parser.add_argument("--out-json", default="data/benchmark.json",
                              help="JSON metrics")

    # Comando: factor-bench (Onda 242) — real market factor models
    factor_parser = subparsers.add_parser(
        "factor-bench",
        help="Factor models bench (momentum/mean_rev/rsi) vs baseline em market events Q1 2026",
    )
    factor_parser.add_argument("--strategies", default="baseline,momentum,mean_reversion,rsi",
                               help="Strategies CSV (default: all)")
    factor_parser.add_argument("--out-md", default="data/factor_bench.md",
                               help="markdown report")

    # Comando: factor-autoresearch (Onda 242) — Karpathy ensemble grid
    autores_parser = subparsers.add_parser(
        "factor-autoresearch",
        help="Karpathy autoresearch ensemble weights grid sobre factor models",
    )
    autores_parser.add_argument("--grid-step", type=float, default=0.25,
                                help="Step size grid (0.25 → 5^4 combos)")
    autores_parser.add_argument("--out-md", default="data/factor_autoresearch.md",
                                help="markdown report")

    args = parser.parse_args()

    if args.comando == "run":
        modo_cli(args)
    elif args.comando == "serve":
        modo_serve(args)
    elif args.comando == "live":
        modo_live(args)
    elif args.comando == "demo":
        modo_demo(args)
    elif args.comando == "mirofish":
        modo_mirofish(args)
    elif args.comando == "benchmark":
        modo_benchmark(args)
    elif args.comando == "factor-bench":
        modo_factor_bench(args)
    elif args.comando == "factor-autoresearch":
        modo_factor_autoresearch(args)
    else:
        parser.print_help()
        print("\nExemplos:")
        print("  python -m vila_inteia.main demo")
        print("  python -m vila_inteia.main run --steps 100 --topico 'eleições 2026'")
        print("  python -m vila_inteia.main serve --port 8100")
        print("  python -m vila_inteia.main live --intervalo 30 --topico 'IA no Brasil'")
        print("  python -m vila_inteia.main mirofish --personas CL001,CL002,CL007")
        print("  python -m vila_inteia.main benchmark")
        print("  python -m vila_inteia.main factor-bench")
        print("  python -m vila_inteia.main factor-autoresearch --grid-step 0.25")


if __name__ == "__main__":
    main()
