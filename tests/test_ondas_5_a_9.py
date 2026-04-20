"""Testes combinados Ondas 5, 6, 7, 8, 9 (smoke + integração rápida)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest.calibracao import grid_search_simples
from engine.mcp_server.tools import lista_tools_disponiveis, executar_tool
from engine.mcp_server.server import MCPServer
from engine.distribuido.tiers import TierClassifier, HOT, COLD
from engine.distribuido.ray_actors import PersonaActor, coordinator_step
from engine.distribuido.vllm_client import VLLMClient

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_calibracao_reduz_brier():
    r = grid_search_simples("seed_eleicao_municipal_sp_2024", grid_resolution=3)
    teste("calibração retorna estrutura", "brier_otimo" in r)
    teste("brier_otimo <= brier_default",
          r["brier_otimo"] <= r["brier_default"] + 1e-9,
          f"otimo={r['brier_otimo']} default={r['brier_default']}")


def t_mcp_tools_registradas():
    tools = lista_tools_disponiveis()
    nomes = {t["name"] for t in tools}
    teste("tool prever_trajetoria registrada", "vila.prever_trajetoria" in nomes)
    teste("tool extrair_grafo registrada", "vila.extrair_grafo" in nomes)
    teste("tool calibrar registrada", "vila.calibrar" in nomes)


def t_mcp_executar_tool():
    r = executar_tool("vila.extrair_grafo", {"texto": "Sun Tzu e Cleópatra debateram."})
    teste("tool retorna entidades", "entidades" in r and len(r["entidades"]) >= 2)


def t_mcp_server_initialize():
    s = MCPServer()
    resp = s.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    teste("initialize retorna capabilities",
          "result" in resp and "capabilities" in resp["result"])


def t_mcp_server_tools_list():
    s = MCPServer()
    resp = s.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    teste("tools/list retorna tools",
          "result" in resp and len(resp["result"]["tools"]) >= 3)


def t_mcp_server_call_tool():
    s = MCPServer()
    resp = s.handle_request({
        "jsonrpc": "2.0", "id": 3,
        "method": "tools/call",
        "params": {"name": "vila.extrair_grafo", "arguments": {"texto": "Sun Tzu e Napoleon."}},
    })
    teste("tools/call retorna content",
          "result" in resp and "content" in resp["result"])


def t_tier_classifier():
    tc = TierClassifier(fracao_hot=0.2)
    ids = [f"a{i}" for i in range(10)]
    tc.inicializar(ids)
    hot_count = sum(1 for i in ids if tc.tier_para(i) == HOT)
    teste("tier classifier aloca 20% em hot",
          hot_count == 2, f"got {hot_count}")


def t_persona_actor_fallback():
    actor = PersonaActor("p1", tier="cold")
    r = actor.step({})
    teste("actor.step retorna persona_id", r["persona_id"] == "p1")
    teste("actor.step em sync fallback", r["status"] in ("sync_fallback", "skeleton_only"))


def t_coordinator_step_serial():
    actors = [PersonaActor(f"p{i}") for i in range(3)]
    r = coordinator_step(actors, {})
    teste("coordinator retorna 3 resultados", len(r) == 3)


def t_vllm_client_sem_url():
    c = VLLMClient(url="")
    teste("vllm sem URL indisponível", c.disponivel == False)
    teste("vllm completar sem URL retorna None",
          c.completar([{"role": "user", "content": "x"}]) is None)


def main():
    print("=== test_ondas_5_a_9 ===")
    for fn in [t_calibracao_reduz_brier, t_mcp_tools_registradas, t_mcp_executar_tool,
               t_mcp_server_initialize, t_mcp_server_tools_list, t_mcp_server_call_tool,
               t_tier_classifier, t_persona_actor_fallback, t_coordinator_step_serial,
               t_vllm_client_sem_url]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
