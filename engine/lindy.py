"""
Onda 256: Lindy Effect (Mandelbrot 1982; popularized by Taleb 2012).

Para entidades non-perishable (institutions, recurring events, technologies):
expected remaining lifetime ∝ current age.

Aplicação a forecasting de eventos:
- Recurring scheduled events (Olympics, MWC, World Cup, summits) com história
  longa têm probabilidade alta de recorrer
- Eventos novos (recém-lançados) têm baixa Lindy probability

Formal: P(survive next period | survived t periods) ≈ t / (t + period)
       Equivalent: P(end in next period) ≈ period / (t + period)

Para eventos: P(scheduled event ocorre Q1 2026 | running há N years) =
              1 - (1 / (1 + N))   [period normalizado]

Combina com classifier: para scheduled_event categoria, usa Lindy boost
em vez do prior fixo 0.92, baseado em years_running do event.

Sem memorization: usa só year_started field (public info), não outcome data.
"""

from __future__ import annotations

import re
from typing import Optional


def lindy_probability(years_running: float, horizon_years: float = 1.0) -> float:
    """P(event recorre dentro de horizon_years | rodou há years_running).

    Lindy: hazard rate decai como 1/t. Sobrevivência segue Pareto-like.
    Aproximação simples: P(end) = horizon / (years_running + horizon)
    P(survive) = years_running / (years_running + horizon)
    """
    if years_running <= 0:
        return 0.5
    return years_running / (years_running + horizon_years)


def parse_year_from_context(contexto: str) -> Optional[int]:
    """Extract first 4-digit year (1900-2030) from contexto string."""
    matches = re.findall(r"\b(18\d{2}|19\d{2}|20[0-2]\d)\b", contexto)
    if not matches:
        return None
    return int(matches[0])


KNOWN_LINDY_EVENTS = {
    # Recurring scheduled events with first edition year
    # Source: public knowledge, no Q1 2026 outcome data
    "olympic": 1896,           # Modern Olympics
    "world cup": 1930,         # FIFA WC
    "super bowl": 1967,
    "wimbledon": 1877,
    "kentucky derby": 1875,
    "preakness": 1873,
    "wrestlemania": 1985,
    "wef": 1971,               # Davos
    "davos": 1971,
    "mwc": 2006,               # Mobile World Congress (Barcelona era)
    "mobile world congress": 2006,
    "ces": 1967,
    "wwdc": 1983,
    "gtc": 2009,               # NVIDIA
    "nfl": 1920,
    "f1": 1950,                # Formula 1 World Championship
    "nba": 1946,
    "fomc": 1933,              # Fed Open Market Committee
    "berkshire annual": 1965,
    "indianapolis 500": 1911,
    "tour de france": 1903,
    "six nations": 2000,       # Modern format
    "champions league": 1955,
}


def lindy_for_event(framing: str, contexto: str = "",
                    current_year: int = 2026,
                    horizon_years: float = 1.0) -> Optional[float]:
    """If framing matches known Lindy event, return Lindy prob; else None.

    Uses survival approximation: probability event still recurring after t years.
    """
    text = (framing + " " + contexto).lower()
    for key, start_year in KNOWN_LINDY_EVENTS.items():
        if key in text:
            age = max(1, current_year - start_year)
            return lindy_probability(age, horizon_years)
    return None
