"""
Onda 233: Micro events — pós-january 2026.

Strategy honesta: para cada micro event Q1 2026 (preços ações, cripto,
votos políticos, esportes diários), Vila usa BASE RATE POR CATEGORIA
em vez de tentar predizer specific outcome.

Não-memorização: predições derivam de:
  - Empirical base rates (prices up vs down ~50% market efficient)
  - Polling trend (election margin extrapolation)
  - Volatility-based prior (high vol = more spread)

Categorias de micro events:
  - stock_price_up: prob 0.50 (random walk)
  - crypto_price_up: prob 0.50 (random walk)
  - sports_favorite_wins: prob 0.65 (favorite home advantage)
  - election_incumbent_wins: prob 0.55 (incumbency advantage)
  - poll_lead_holds: prob 0.65 (lead holds short-term)
  - geopolitical_escalation: prob 0.30 (rare extreme)
  - tech_release_on_time: prob 0.40 (delays common)
  - earnings_beat: prob 0.55 (companies guide low)
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Base rates calibrados via Q1 2026 honest backtest (Onda 231)
BASE_RATES: dict[str, float] = {
    # Markets (efficient, ~50/50)
    "stock_price_up": 0.50,
    "stock_price_down": 0.50,
    "crypto_price_up": 0.50,
    "crypto_price_down": 0.50,
    # Sports (favorite advantage)
    "sports_favorite_wins": 0.65,
    "sports_home_wins": 0.55,
    "sports_underdog_wins": 0.35,
    # Politics
    "election_incumbent_wins": 0.55,
    "poll_lead_holds": 0.65,  # short-term
    "approval_change_5pct": 0.30,  # rare
    # Geopolitics
    "geopolitical_escalation_extreme": 0.30,
    "war_continues": 0.85,
    "treaty_signed": 0.20,
    # Tech / corporate
    "tech_release_on_time": 0.40,
    "earnings_beat_estimate": 0.55,
    "ipo_pop_first_day": 0.55,
    "merger_completes": 0.65,
    # Default
    "default": 0.50,
}


@dataclass
class MicroEvent:
    event_id: str
    category: str
    framing: str
    date: str
    real_outcome: int | None = None  # None se ainda não resolvido
    prior: float = 0.50

    def predict(self) -> float:
        """Predição honesta = base rate da categoria."""
        return BASE_RATES.get(self.category, BASE_RATES["default"])


def gerar_dataset_stock_prices(
    tickers: list[str], dates: list[str]
) -> list[MicroEvent]:
    """Gera N eventos: 'ticker X subiu no dia Y?'.

    Sem real_outcome — precisa preencher via market data API
    posteriormente (ex: yfinance, Alpha Vantage).
    """
    events = []
    for tk in tickers:
        for d in dates:
            events.append(MicroEvent(
                event_id=f"stk_{tk}_{d.replace('-', '')}",
                category="stock_price_up",
                framing=f"{tk} fechou em alta no dia {d}?",
                date=d,
            ))
    return events


def gerar_dataset_cripto_prices(
    coins: list[str], dates: list[str]
) -> list[MicroEvent]:
    events = []
    for c in coins:
        for d in dates:
            events.append(MicroEvent(
                event_id=f"crypto_{c}_{d.replace('-', '')}",
                category="crypto_price_up",
                framing=f"{c} fechou em alta no dia {d}?",
                date=d,
            ))
    return events


def avaliar_predictor_honesto(events: list[MicroEvent]) -> dict:
    """Eval predictor (=base rate por categoria).

    Para events com real_outcome=None, ignora.
    """
    resolved = [e for e in events if e.real_outcome is not None]
    if not resolved:
        return {"n": 0, "n_resolved": 0, "hits": 0, "acc": 0, "brier": 0}

    hits = 0
    brier_sum = 0.0
    for e in resolved:
        p = e.predict()
        if (p >= 0.5) == bool(e.real_outcome):
            hits += 1
        brier_sum += (p - e.real_outcome) ** 2

    return {
        "n": len(events),
        "n_resolved": len(resolved),
        "hits": hits,
        "acc": hits / len(resolved),
        "brier": brier_sum / len(resolved),
    }


def gerar_500_micro_events_q1_2026() -> list[MicroEvent]:
    """Gera ~500 micro events Q1 2026 (Jan-Mar).

    Returns lista pronta para preenchimento de real_outcome via API.
    """
    # 50 stock tickers × 3 datas mensais = 150
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM",
        "V", "WMT", "DIS", "NFLX", "PYPL", "INTC", "AMD", "CSCO", "ORCL",
        "IBM", "CRM", "ADBE", "PFE", "JNJ", "KO", "PEP", "MCD", "BA",
        "XOM", "CVX", "GS", "MS", "BAC", "C", "WFC", "UBER", "LYFT",
        "SPOT", "SHOP", "SQ", "COIN", "PLTR", "SNAP", "TWTR", "ROKU",
        "ZM", "DOCU", "CRWD", "SNOW", "DDOG", "NET", "TWLO",
    ]
    stock_dates = ["2026-01-30", "2026-02-27", "2026-03-31"]
    events = gerar_dataset_stock_prices(tickers, stock_dates)

    # 20 cryptos × 3 datas = 60
    coins = [
        "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX",
        "MATIC", "DOT", "LTC", "BCH", "LINK", "ATOM", "UNI", "ICP",
        "FIL", "NEAR", "APT", "TRUMP",
    ]
    crypto_dates = ["2026-01-15", "2026-02-15", "2026-03-15"]
    events += gerar_dataset_cripto_prices(coins, crypto_dates)

    # 100 sports games (NBA/NFL/MLB/F1 — placeholder)
    for i in range(1, 101):
        events.append(MicroEvent(
            event_id=f"sport_{i:03d}",
            category="sports_favorite_wins",
            framing=f"Sport game #{i} Q1 2026 — favorite venceu?",
            date=f"2026-{(i % 3) + 1:02d}-{(i % 28) + 1:02d}",
        ))

    # 50 election/poll events
    for i in range(1, 51):
        events.append(MicroEvent(
            event_id=f"elec_{i:03d}",
            category="election_incumbent_wins" if i % 2 == 0 else "poll_lead_holds",
            framing=f"Election/poll #{i} Q1 2026 — incumbent/lead won?",
            date=f"2026-{(i % 3) + 1:02d}-{(i % 28) + 1:02d}",
        ))

    # 50 corporate (earnings, IPOs, mergers)
    for i in range(1, 51):
        events.append(MicroEvent(
            event_id=f"corp_{i:03d}",
            category=["earnings_beat_estimate", "ipo_pop_first_day", "merger_completes"][i % 3],
            framing=f"Corporate #{i} Q1 2026 — outcome positivo?",
            date=f"2026-{(i % 3) + 1:02d}-{(i % 28) + 1:02d}",
        ))

    # 50 geopolitical
    for i in range(1, 51):
        events.append(MicroEvent(
            event_id=f"geo_{i:03d}",
            category="geopolitical_escalation_extreme" if i % 4 == 0 else "war_continues",
            framing=f"Geopolitical #{i} Q1 2026 — escalation/continuação?",
            date=f"2026-{(i % 3) + 1:02d}-{(i % 28) + 1:02d}",
        ))

    return events
