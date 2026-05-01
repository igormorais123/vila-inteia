"""Tests for engine.domain_router — Onda 285 autoroute."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.domain_router import route, route_stats


def test_geopolitics_routes_to_llm():
    assert route("Trump assinará nova ordem executiva sobre sanções à China?") == "llm"
    assert route("Eleição presidencial 2026 terá segundo turno?") == "llm"
    assert route("Israel e Gaza chegarão a cessar-fogo até dez 2026?") == "llm"


def test_btc_specific_routes_to_vila():
    assert route("BTC price acima de $80k em jul 2026?") == "vila"
    assert route("BTC funding rate negativo por 7 dias?") == "vila"
    assert route("Hashrate acima de 600 EH/s?") == "vila"


def test_corporate_launch_routes_to_llm():
    assert route("Apple lançará iPhone 18 com chip M5 em set 2026?") == "llm"
    assert route("Lançamento da Tesla Cybercab até abr 2027?") == "llm"


def test_judicial_political_routes_to_llm():
    assert route("STF julgará Bolsonaro até nov 2026?") == "llm"
    assert route("CPI da gasolina será instaurada em 2026?") == "llm"
    assert route("Operação da PF prenderá ex-ministro?") == "llm"


def test_war_geopolitics_routes_to_llm():
    assert route("Rússia anunciará nova mobilização militar?") == "llm"
    assert route("OTAN expandirá presença na Ucrânia?") == "llm"


def test_generic_routes_to_hybrid():
    """Eventos sem keywords específicas → hybrid (default)."""
    assert route("Brasil ganhará a Copa do Mundo 2026?") == "hybrid"
    assert route("Temperatura média global subirá 0.1C?") == "hybrid"
    assert route("Festival X terá mais de 10k pessoas?") == "hybrid"


def test_vila_takes_precedence_over_llm():
    """Se evento tem keyword Vila E keyword LLM, Vila ganha."""
    # 'eleição' (LLM) + 'BTC price' (Vila) → vila por precedência
    framing = "BTC price subirá após eleição americana 2026?"
    assert route(framing) == "vila"


def test_route_stats_aggregates():
    events = [
        {"outcome_framing": "Eleição 2026 terá X?", "contexto": ""},
        {"outcome_framing": "BTC price acima de Y?", "contexto": ""},
        {"outcome_framing": "Festival genérico Z?", "contexto": ""},
        {"outcome_framing": "Guerra na Ucrânia em 2027?", "contexto": ""},
    ]
    s = route_stats(events)
    assert s["total"] == 4
    assert s["llm"] == 2  # eleição + guerra
    assert s["vila"] == 1  # BTC price
    assert s["hybrid"] == 1  # genérico
    assert s["pct"]["llm"] == 0.5


def test_empty_framing_routes_to_hybrid():
    assert route("") == "hybrid"
    assert route("", "") == "hybrid"


def test_case_insensitive():
    assert route("ELEIÇÃO PRESIDENCIAL 2026?") == "llm"
    assert route("BTC PRICE acima de 80k?") == "vila"


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
