"""Testes Ondas 22-24: multi-plataforma orquestrador + GraphRAG hook + datasets."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.plataformas import OrquestradorPlataformas, ORQUESTRADOR_GLOBAL
from engine.memoria.grafo import GRAFO_GLOBAL, indexar_texto
from engine.backtest import carregar_dataset, rodar_backtest

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# ========== Onda 22 ==========

def t_orquestrador_registra_em_todas():
    o = OrquestradorPlataformas()
    o.registrar_habitante("p1", "Sun Tzu", "estrategista militar")
    teste("perfil em twitter", "p1" in o.twitter.perfis)
    teste("perfil em reddit", "p1" in o.reddit.perfis)
    teste("perfil em linkedin", "p1" in o.linkedin.perfis)
    teste("perfil em tiktok", "p1" in o.tiktok.perfis)


def t_orquestrador_adapta_nomes():
    o = OrquestradorPlataformas()
    o.registrar_habitante("p1", "Steve Jobs", "CEO Apple")
    teste("TikTok: handle", o.tiktok.perfis["p1"].nome_exibicao == "@stevejobs")
    teste("Reddit: u/prefix", o.reddit.perfis["p1"].nome_exibicao == "u/steve")
    teste("LinkedIn: full name", o.linkedin.perfis["p1"].nome_exibicao == "Steve Jobs")


def t_orquestrador_post_primario():
    o = OrquestradorPlataformas()
    o.registrar_habitante("p1", "X", "")
    pid = o.postar_em("twitter", "p1", "primeiro tweet")
    teste("post id retornado", pid is not None and pid.startswith("twitter_"))


def t_orquestrador_spillover_forcado():
    o = OrquestradorPlataformas()
    o.registrar_habitante("p1", "X", "")
    r = o.postar_primario_com_spillover(
        "twitter", "p1", "conteudo viral",
        taxa_spillover={"reddit": 1.0, "linkedin": 1.0, "tiktok": 1.0},
    )
    teste("post origem criado", r["post_id_origem"] is not None)
    teste("3 spillovers", len(r["spillovers"]) == 3,
          f"got {r['spillovers']}")


def t_orquestrador_spillover_zero():
    o = OrquestradorPlataformas()
    o.registrar_habitante("p1", "X", "")
    r = o.postar_primario_com_spillover(
        "twitter", "p1", "teste",
        taxa_spillover={"reddit": 0.0, "linkedin": 0.0, "tiktok": 0.0},
    )
    teste("0 spillovers com prob 0", len(r["spillovers"]) == 0)


def t_orquestrador_stats():
    o = OrquestradorPlataformas()
    o.registrar_habitante("p1", "X", "")
    o.postar_em("twitter", "p1", "teste")
    stats = o.stats_todas()
    teste("4 plataformas em stats", len(stats) == 4)
    tw = next((s for s in stats if s.nome == "twitter"), None)
    teste("twitter: 1 post", tw and tw.n_posts == 1)


# ========== Onda 23 ==========

def t_graphrag_indexa_texto():
    # Limpa
    GRAFO_GLOBAL.nos.clear()
    GRAFO_GLOBAL._arestas_todas.clear()
    GRAFO_GLOBAL.arestas_por_origem.clear()
    GRAFO_GLOBAL.arestas_por_destino.clear()
    texto = "Sun Tzu ensinou Cleópatra sobre Alexandre Magno."
    r = indexar_texto(GRAFO_GLOBAL, texto)
    teste("indexa ≥3 entidades", r["n_entidades"] >= 3, f"got {r}")
    teste("cria co-ocorrência", r["n_arestas"] >= 1)


def t_graphrag_busca_por_rotulo():
    GRAFO_GLOBAL.nos.clear()
    GRAFO_GLOBAL._arestas_todas.clear()
    GRAFO_GLOBAL.arestas_por_origem.clear()
    GRAFO_GLOBAL.arestas_por_destino.clear()
    indexar_texto(GRAFO_GLOBAL, "Albert Einstein e Nikola Tesla debateram.")
    r = GRAFO_GLOBAL.buscar_por_rotulo("Einstein")
    teste("busca rotulo case-insensitive", len(r) == 1)


def t_graphrag_subgrafo_2hops():
    GRAFO_GLOBAL.nos.clear()
    GRAFO_GLOBAL._arestas_todas.clear()
    GRAFO_GLOBAL.arestas_por_origem.clear()
    GRAFO_GLOBAL.arestas_por_destino.clear()
    indexar_texto(GRAFO_GLOBAL,
                  "Aristóteles influenciou Alexandre. Alexandre conquistou Pérsia.")
    # 2 sentenças, 2 cliques
    r = GRAFO_GLOBAL.buscar_por_rotulo("Alexandre")
    if r:
        vizinhos = GRAFO_GLOBAL.vizinhos(r[0].id, hops=2)
        teste("2-hops alcança outros", len(vizinhos) >= 1,
              f"got {vizinhos}")
    else:
        teste("busca Alexandre encontrou", False, "não extraiu")


# ========== Onda 24 ==========

def t_datasets_4_novos():
    datasets = [
        "seed_eleicao_municipal_sp_2024",
        "lancamento_apple_vpro_2024",
        "americanas_crise_2023",
        "impeachment_dilma_2016",
        "tiktok_viral_2024",
    ]
    for d in datasets:
        try:
            ds = carregar_dataset(d, base_dir="data/backtest")
            teste(f"dataset {d}: {ds.n} eventos", ds.n == 10)
        except FileNotFoundError as e:
            teste(f"dataset {d} existe", False, str(e))


def t_backtest_all_datasets():
    datasets = [
        "lancamento_apple_vpro_2024",
        "americanas_crise_2023",
        "impeachment_dilma_2016",
        "tiktok_viral_2024",
    ]
    for d in datasets:
        try:
            r = rodar_backtest(d, n_sims=1, base_dir="data/backtest")
            teste(f"backtest {d}: Brier em [0, 1]",
                  0 <= r.brier <= 1, f"brier={r.brier}")
        except FileNotFoundError as e:
            teste(f"backtest {d}: existe", False, str(e))


def main():
    print("=== test_ondas_22_24 ===")
    for fn in [t_orquestrador_registra_em_todas, t_orquestrador_adapta_nomes,
               t_orquestrador_post_primario, t_orquestrador_spillover_forcado,
               t_orquestrador_spillover_zero, t_orquestrador_stats,
               t_graphrag_indexa_texto, t_graphrag_busca_por_rotulo,
               t_graphrag_subgrafo_2hops,
               t_datasets_4_novos, t_backtest_all_datasets]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
