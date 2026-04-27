"""Testes Ondas 37-39: health + grafo export + MANIFEST."""

from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# ========== Onda 37: Health ==========

def t_rotas_health_importa():
    from api import rotas_health
    teste("rotas_health importa", rotas_health.router is not None)
    teste("prefix correto", rotas_health.router.prefix == "/api/v1/vila")


def t_health_retorna_todos_subsistemas():
    from api.rotas_health import endpoint_health
    r = endpoint_health()
    teste("health retorna 'subsistemas'", "subsistemas" in r)
    esperados = ["rastreador", "auto_calibrador", "persistencia", "event_log",
                  "grafo_conhecimento", "crencas", "plataformas", "mcp"]
    for sub in esperados:
        teste(f"subsistema {sub} presente", sub in r["subsistemas"])


def t_health_total_subsistemas():
    from api.rotas_health import endpoint_health
    r = endpoint_health()
    teste("total_subsistemas >= 8", r.get("total_subsistemas", 0) >= 8)


# ========== Onda 38: Grafo export ==========

def t_rotas_grafo_importa():
    from api import rotas_grafo
    teste("rotas_grafo importa", rotas_grafo.router is not None)


def t_export_grafo_vazio():
    # Limpa grafo
    from engine.memoria.grafo import GRAFO_GLOBAL
    GRAFO_GLOBAL.nos.clear()
    GRAFO_GLOBAL._arestas_todas.clear()
    GRAFO_GLOBAL.arestas_por_origem.clear()
    GRAFO_GLOBAL.arestas_por_destino.clear()
    from api.rotas_grafo import endpoint_export_grafo
    r = endpoint_export_grafo(limite_nos=10)
    teste("export grafo vazio: nodes=[]", r["nodes"] == [])
    teste("n_total_nos=0", r["n_total_nos"] == 0)


def t_export_grafo_com_dados():
    from engine.memoria.grafo import GRAFO_GLOBAL, indexar_texto
    GRAFO_GLOBAL.nos.clear()
    GRAFO_GLOBAL._arestas_todas.clear()
    GRAFO_GLOBAL.arestas_por_origem.clear()
    GRAFO_GLOBAL.arestas_por_destino.clear()
    indexar_texto(GRAFO_GLOBAL, "Sun Tzu e Cleópatra conversaram sobre Alexandre.")
    from api.rotas_grafo import endpoint_export_grafo, endpoint_stats_grafo
    r = endpoint_export_grafo()
    teste("export: nós presentes", len(r["nodes"]) >= 3)
    teste("export: format D3", "id" in r["nodes"][0] and "label" in r["nodes"][0])
    s = endpoint_stats_grafo()
    teste("stats: top_10_nos presente", "top_10_nos_por_grau" in s)


# ========== Onda 39: MANIFEST ==========

def t_manifest_existe():
    p = Path("MANIFEST.md")
    teste("MANIFEST.md existe", p.exists())


def t_manifest_tem_secoes_core():
    p = Path("MANIFEST.md")
    if not p.exists():
        teste("MANIFEST existe", False, "arquivo não encontrado")
        return
    conteudo = p.read_text(encoding="utf-8")
    secoes = ["Ondas", "Módulos engine", "Endpoints API", "Frontend UI",
               "MCP Tools", "Datasets", "Testes", "Artigos", "CLI"]
    for s in secoes:
        teste(f"MANIFEST tem seção '{s}'", s in conteudo)


def t_manifest_menciona_32_ondas():
    p = Path("MANIFEST.md")
    conteudo = p.read_text(encoding="utf-8")
    # Deve listar Ondas 5 até pelo menos 39
    teste("MANIFEST menciona Onda 5", "| 5 |" in conteudo)
    teste("MANIFEST menciona Onda 39", "| 39 |" in conteudo)


def main():
    print("=== test_ondas_37_39 ===")
    for fn in [t_rotas_health_importa, t_health_retorna_todos_subsistemas,
               t_health_total_subsistemas,
               t_rotas_grafo_importa, t_export_grafo_vazio, t_export_grafo_com_dados,
               t_manifest_existe, t_manifest_tem_secoes_core, t_manifest_menciona_32_ondas]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
