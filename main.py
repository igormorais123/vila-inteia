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

    app.include_router(router)
    app.include_router(rede_router)
    app.include_router(colmeia_router)
    app.include_router(harness_router)
    app.include_router(vivos_router)

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
    app.include_router(router)
    app.include_router(rede_router)
    app.include_router(colmeia_router)
    app.include_router(harness_router)
    app.include_router(vivos_router)

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

    args = parser.parse_args()

    if args.comando == "run":
        modo_cli(args)
    elif args.comando == "serve":
        modo_serve(args)
    elif args.comando == "live":
        modo_live(args)
    elif args.comando == "demo":
        modo_demo(args)
    else:
        parser.print_help()
        print("\nExemplos:")
        print("  python -m vila_inteia.main demo")
        print("  python -m vila_inteia.main run --steps 100 --topico 'eleições 2026'")
        print("  python -m vila_inteia.main serve --port 8100")
        print("  python -m vila_inteia.main live --intervalo 30 --topico 'IA no Brasil'")


if __name__ == "__main__":
    main()
