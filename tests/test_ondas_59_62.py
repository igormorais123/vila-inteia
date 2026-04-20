"""Testes Ondas 59-62: tier gate + cache + budget."""

from __future__ import annotations
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ia_cache import LRUCache, cache_chave, CACHE_GLOBAL
from engine.llm_tier_gate import LLMTierGate
from engine.budget_tracker import BudgetTracker, PRECOS_MODELO

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# Onda 60 — Cache

def t_cache_miss_entao_hit():
    c = LRUCache(capacity=10)
    teste("miss inicial", c.get("k1") is None)
    c.put("k1", "resp1")
    teste("hit após put", c.get("k1") == "resp1")
    teste("stats: hits=1", c.stats()["hits"] == 1)
    teste("stats: misses=1", c.stats()["misses"] == 1)


def t_cache_ttl_expira():
    c = LRUCache(capacity=10, ttl_segundos=1)
    c.put("k", "v")
    teste("hit antes TTL", c.get("k") == "v")
    time.sleep(1.2)
    teste("miss após TTL", c.get("k") is None)


def t_cache_lru_evicao():
    c = LRUCache(capacity=3)
    c.put("a", "1"); c.put("b", "2"); c.put("c", "3")
    c.get("a")   # toca 'a' → move ao fim
    c.put("d", "4")  # evicta 'b' (oldest)
    teste("a sobreviveu (foi acessado)", c.get("a") == "1")
    teste("b evicted", c.get("b") is None)
    teste("d presente", c.get("d") == "4")


def t_cache_chave_determinista():
    k1 = cache_chave("sys", "user", "rapido")
    k2 = cache_chave("sys", "user", "rapido")
    k3 = cache_chave("sys", "user", "analise")
    teste("mesma entrada = mesma chave", k1 == k2)
    teste("modelo diferente = chave diferente", k1 != k3)
    teste("chave tem 32 chars", len(k1) == 32)


# Onda 59 — Tier gate

def t_tier_sem_inicializar_permite():
    g = LLMTierGate(fracao_hot=0.05)
    teste("sem init permite LLM", g.pode_chamar_llm("qualquer"))


def t_tier_inicializa_top_5pct():
    g = LLMTierGate(fracao_hot=0.05)
    agentes = [f"a{i}" for i in range(100)]
    g.inicializar(agentes)
    s = g.stats()
    teste("5% de 100 = 5 hot", s["n_hot"] == 5)
    teste("100 total", s["n_total"] == 100)


def t_tier_cold_bloqueia():
    g = LLMTierGate(fracao_hot=0.05)
    agentes = [f"a{i}" for i in range(20)]
    g.inicializar(agentes)
    # a0 está em hot; a19 está em cold
    teste("a0 hot permite", g.pode_chamar_llm("a0"))
    teste("a19 cold bloqueia", not g.pode_chamar_llm("a19"))


def t_tier_rotacao():
    g = LLMTierGate(fracao_hot=0.10, rotate_steps=10)
    agentes = [f"a{i}" for i in range(20)]
    g.inicializar(agentes)
    hot_antes = set()
    for i in range(2):
        if g.pode_chamar_llm(f"a{i}"):
            hot_antes.add(f"a{i}")
    # Step 5 não rotaciona
    rot = g.talvez_rotacionar(5)
    teste("step<10: não rotaciona", not rot)
    # Step 15 rotaciona
    rot = g.talvez_rotacionar(15)
    teste("step>=10: rotaciona", rot)


# Onda 62 — Budget

def t_budget_registra_custo():
    b = BudgetTracker(limite_usd=float("inf"))
    c = b.registrar("gemini-2.5-flash-lite", tokens_in=1000, tokens_out=500)
    # 1000 in: 1000/1M * 0.10 = 0.0001
    # 500 out: 500/1M * 0.40 = 0.0002
    # total: 0.0003
    teste("custo gemini-lite (1k in + 500 out) ≈ 0.0003",
          abs(c - 0.0003) < 1e-9, f"got {c}")


def t_budget_modelo_gratis():
    b = BudgetTracker()
    c = b.registrar("BestFREE", tokens_in=10000, tokens_out=5000)
    teste("modelo BestFREE custa 0", c == 0.0)


def t_budget_limite_bloqueia():
    b = BudgetTracker(limite_usd=0.001)
    b.registrar("claude-sonnet-4-20250514", tokens_in=1_000, tokens_out=1_000)
    # 1k in * 3 + 1k out * 15 = 18 / 1M = 0.000018... pequeno
    # Forçar excesso:
    b.registrar("claude-opus-4-7", tokens_in=100_000, tokens_out=100_000)
    teste("orçamento esgotou", not b.pode_chamar())
    teste("stats: exausto=True", b.stats()["exausto"])


def t_budget_stats_agrupado():
    b = BudgetTracker()
    b.registrar("gemini-2.5-flash", 1000, 100)
    b.registrar("gemini-2.5-flash-lite", 1000, 100)
    s = b.stats()
    teste("stats por modelo (2 entradas)",
          len(s["custo_por_modelo_usd"]) == 2)


def t_budget_resetar():
    b = BudgetTracker()
    b.registrar("claude-haiku-4-5-20251001", 10000, 1000)
    b.resetar()
    teste("após reset: total 0", b.stats()["total_usd"] == 0)
    teste("após reset: 0 chamadas", b.stats()["n_chamadas"] == 0)


def main():
    print("=== test_ondas_59_62 ===")
    for fn in [t_cache_miss_entao_hit, t_cache_ttl_expira, t_cache_lru_evicao,
               t_cache_chave_determinista,
               t_tier_sem_inicializar_permite, t_tier_inicializa_top_5pct,
               t_tier_cold_bloqueia, t_tier_rotacao,
               t_budget_registra_custo, t_budget_modelo_gratis,
               t_budget_limite_bloqueia, t_budget_stats_agrupado, t_budget_resetar]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
