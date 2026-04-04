"""Entrypoint para uvicorn — Vila INTEIA standalone server."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from vila_inteia.api.rotas_vila import router

# Force LLM provider detection at startup
try:
    from vila_inteia.engine.ia_client import _detectar_provider
    _detectar_provider()
except Exception as e:
    print(f"Warning: ia_client init failed: {e}")

app = FastAPI(
    title="Vila INTEIA - Think Tank Vivo",
    description="Simulacao de 144 consultores lendarios com IA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Rede social routes if available
try:
    from vila_inteia.api.rotas_rede_social import router as rede_router
    app.include_router(rede_router)
except ImportError:
    pass

# Extra routes (oficinas, workspace, desafio, economia)
try:
    from vila_inteia.api.rotas_extras import router as extras_router
    app.include_router(extras_router)
except ImportError:
    pass

# Health endpoint
# Auto-step: simulation runs in background
import asyncio
import threading

_auto_step_running = False
_auto_step_interval = 30  # seconds between steps

_auto_save_counter = 0

def _auto_step_loop():
    """Background thread that runs simulation steps + auto-save."""
    import time
    global _auto_step_running, _auto_save_counter
    while _auto_step_running:
        try:
            from vila_inteia.api.rotas_vila import obter_simulacao
            sim = obter_simulacao()
            sim.executar_step()
            _auto_save_counter += 1
            # Auto-save a cada 10 steps
            if _auto_save_counter % 10 == 0:
                try:
                    sim.salvar()
                    print(f"[Auto-save] Step {sim.step} salvo")
                except Exception as e2:
                    print(f"[Auto-save] Erro: {e2}")
        except Exception as e:
            print(f"Auto-step error: {e}")
        time.sleep(_auto_step_interval)

@app.post("/api/v1/vila/auto-step/iniciar")
def iniciar_auto_step(intervalo: int = 30):
    """Inicia simulacao automatica em background."""
    global _auto_step_running, _auto_step_interval
    if _auto_step_running:
        return {"status": "ja rodando", "intervalo": _auto_step_interval}
    _auto_step_interval = max(10, min(intervalo, 300))
    _auto_step_running = True
    t = threading.Thread(target=_auto_step_loop, daemon=True)
    t.start()
    return {"status": "iniciado", "intervalo": _auto_step_interval}

@app.post("/api/v1/vila/auto-step/parar")
def parar_auto_step():
    """Para simulacao automatica."""
    global _auto_step_running
    _auto_step_running = False
    return {"status": "parado"}

@app.get("/api/v1/vila/auto-step/status")
def status_auto_step():
    return {"rodando": _auto_step_running, "intervalo": _auto_step_interval}

# Helena Rec 1: Auto-warmup on startup
import threading

def _auto_warmup():
    """Roda 10 steps + injeta topico no startup para Vila ter vida."""
    import time
    time.sleep(5)  # esperar server iniciar
    try:
        from vila_inteia.api.rotas_vila import obter_simulacao
        sim = obter_simulacao()
        # Injetar topico default
        sim.injetar_topico("O futuro da inteligencia artificial no Brasil")
        # Rodar 10 steps silenciosamente
        for _ in range(10):
            try:
                sim.executar_step()
            except:
                pass
        print(f"[WARMUP] Vila aquecida: step {sim.step}, {sim.stats.get('total_conversas',0)} conversas")
        # Auto-step: manter Vila viva continuamente
        global _auto_step_running, _auto_step_interval
        _auto_step_running = True
        _auto_step_interval = 45
        t2 = threading.Thread(target=_auto_step_loop, daemon=True)
        t2.start()
        print("[WARMUP] Auto-step iniciado (45s)")
        # Gerar conteudo inicial na rede social
        try:
            from vila_inteia.engine.gatilhos import MotorGatilhos
            from vila_inteia.engine.rede_social import RedeSocial
            rede = sim.rede_social
            motor = sim.motor_gatilhos
            # Processar gatilhos para gerar posts
            motor.processar(sim.step, sim.personas, sim.hora_atual)
            print(f"[WARMUP] Rede social: {len(rede.posts)} posts gerados")
        except Exception as e:
            print(f"[WARMUP] Rede social falhou: {e}")
    except Exception as e:
        print(f"[WARMUP] Falha: {e}")

_warmup_thread = threading.Thread(target=_auto_warmup, daemon=True)
_warmup_thread.start()

@app.get("/health")
def health():
    return {"status": "ok", "service": "vila-inteia", "version": "1.0.0"}

# Frontend estatico
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
