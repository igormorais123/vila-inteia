#!/usr/bin/env python3
"""Phase 3: Cross-country generalization of Vila MRP architecture.

Tests Vila MRP on US 2016, US 2020, UK 2019 to validate beyond BR.

Pipeline per country:
  1. Build poll-state events from real public sources:
       - FiveThirtyEight historical poll averages (US 2016 from
         pres_pollaverages_1968-2016.csv; US 2020 from a Wayback snapshot of
         presidential_poll_averages_2020.csv).
       - Wikipedia 2019 UK general-election polling page (regional sub-pages).
  2. Filter T <= 30 days from election (matches BR pipeline DAYS_FILTER).
  3. Year-fold leak-safe CV: for each country/cycle, fit (uf, regime) baseline
     on past cycles available locally, then evaluate w_state in {0, 0.36}.
  4. Save metrics per country to data/cross_country_results.json.

Output:
  data/backtest/us_2016_president.csv
  data/backtest/us_2020_president.csv
  data/backtest/uk_2019_general.csv
  data/cross_country_results.json
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.political_cohort import (
    fit_cohorts_political,
    predict_political,
    state_baseline_p,
    lead_bin,
    days_bin,
)

RAW_DIR = ROOT / "data" / "cross_country" / "raw"
OUT_DIR = ROOT / "data" / "backtest"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ROOT / "data" / "cross_country_results.json"

DAYS_FILTER = 30
W_STATE = 0.36
W_LINZER = 0.5
SIGMA_INT = 4.0
SIGMA_SLO = 0.05
STEIN_SHRINK = 0.05

# ------------------------------------------------------------------ helpers ---

US_STATE_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC",
    "Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL",
    "Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA",
    "Maine":"ME","Maine CD-1":"ME1","Maine CD-2":"ME2","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
    "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nebraska CD-1":"NE1",
    "Nebraska CD-2":"NE2","Nebraska CD-3":"NE3","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
    "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
    "Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI",
    "Wyoming":"WY","National":"US",
}


def parse_538_date(s: str) -> date | None:
    """538 modeldate is M/D/YYYY."""
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%-m/%-d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# Ground truth for 2016 (winner per state, 2-party).
# Source: official 2016 federal election results.
US_2016_TRUTH = {
    "AL":"R","AK":"R","AZ":"R","AR":"R","CA":"D","CO":"D","CT":"D","DE":"D",
    "DC":"D","FL":"R","GA":"R","HI":"D","ID":"R","IL":"D","IN":"R","IA":"R",
    "KS":"R","KY":"R","LA":"R","ME":"D","ME1":"D","ME2":"R","MD":"D","MA":"D",
    "MI":"R","MN":"D","MS":"R","MO":"R","MT":"R","NE":"R","NE1":"R","NE2":"R",
    "NE3":"R","NV":"D","NH":"D","NJ":"D","NM":"D","NY":"D","NC":"R","ND":"R",
    "OH":"R","OK":"R","OR":"D","PA":"R","RI":"D","SC":"R","SD":"R","TN":"R",
    "TX":"R","UT":"R","VT":"D","VA":"D","WA":"D","WV":"R","WI":"R","WY":"R",
}

US_2020_TRUTH = {
    "AL":"R","AK":"R","AZ":"D","AR":"R","CA":"D","CO":"D","CT":"D","DE":"D",
    "DC":"D","FL":"R","GA":"D","HI":"D","ID":"R","IL":"D","IN":"R","IA":"R",
    "KS":"R","KY":"R","LA":"R","ME":"D","ME1":"D","ME2":"R","MD":"D","MA":"D",
    "MI":"D","MN":"D","MS":"R","MO":"R","MT":"R","NE":"R","NE1":"R","NE2":"D",
    "NE3":"R","NV":"D","NH":"D","NJ":"D","NM":"D","NY":"D","NC":"R","ND":"R",
    "OH":"R","OK":"R","OR":"D","PA":"D","RI":"D","SC":"R","SD":"R","TN":"R",
    "TX":"R","UT":"R","VT":"D","VA":"D","WA":"D","WV":"R","WI":"D","WY":"R",
}


# ------------------------------------------------------- US extractor (538) ---

def build_us_2party_csv(in_csv: Path, out_csv: Path, cycle: int,
                        truth: dict[str, str], election_iso: str) -> dict:
    """From 538 poll averages, build paired (winner=1, runner=0) rows by state.
    Filter to T <= DAYS_FILTER.

    538 candidates of interest:
      2016: 'Hillary Rodham Clinton' (D), 'Donald Trump' (R)
      2020: 'Joseph R. Biden Jr.' (D),    'Donald Trump' (R)
    """
    election_dt = date.fromisoformat(election_iso)
    if cycle == 2016:
        DEM_NAME = "Hillary Rodham Clinton"
        REP_NAME = "Donald Trump"
        dem_label, rep_label = "Hillary Clinton", "Donald Trump"
        dem_party, rep_party = "DEM", "REP"
    else:  # 2020
        DEM_NAME = "Joseph R. Biden Jr."
        REP_NAME = "Donald Trump"
        dem_label, rep_label = "Joe Biden", "Donald Trump"
        dem_party, rep_party = "DEM", "REP"

    by_state_date: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    n_in = 0
    with in_csv.open(encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            try:
                if int(row["cycle"]) != cycle:
                    continue
            except (KeyError, ValueError):
                continue
            state = row.get("state", "").strip()
            if state not in US_STATE_ABBR:
                continue
            uf = US_STATE_ABBR[state]
            if uf == "US":
                continue
            cand = row.get("candidate_name", "").strip()
            d = parse_538_date(row.get("modeldate", ""))
            if d is None:
                continue
            days_to = (election_dt - d).days
            if days_to < 0 or days_to > DAYS_FILTER:
                continue
            try:
                pct = float(row.get("pct_trend_adjusted") or row.get("pct_estimate") or 0)
            except ValueError:
                continue
            key = (uf, d.isoformat())
            if cand == DEM_NAME:
                by_state_date[key]["dem"] = pct
                by_state_date[key]["days_to"] = days_to
            elif cand == REP_NAME:
                by_state_date[key]["rep"] = pct
                by_state_date[key]["days_to"] = days_to
            n_in += 1

    out_rows = []
    skipped_no_truth = 0
    n_pairs = 0
    for (uf, datestr), v in by_state_date.items():
        if "dem" not in v or "rep" not in v:
            continue
        if uf not in truth:
            skipped_no_truth += 1
            continue
        days_to = int(v["days_to"])
        dem_pct, rep_pct = v["dem"], v["rep"]
        winner = truth[uf]
        # Build 2 rows for this poll-date-state pair (winner=1, runner=0).
        # poll_lead_pp encoded from candidate's perspective.
        for who, name, party in (("DEM", dem_label, dem_party),
                                 ("REP", rep_label, rep_party)):
            their_pct  = dem_pct if who == "DEM" else rep_pct
            other_pct  = rep_pct if who == "DEM" else dem_pct
            lead       = their_pct - other_pct
            outcome    = 1 if winner == ("D" if who == "DEM" else "R") else 0
            incumbent  = 0  # neither Clinton nor Biden was incumbent; Trump 2016 not incumbent
            # In 2020 Trump was incumbent.
            if cycle == 2020 and who == "REP":
                incumbent = 1
            evento_id = f"us{cycle}_{datestr}_538_{uf}_{who.lower()}"
            ctx = f"{name} ({party}) vs {'Donald Trump' if who=='DEM' else dem_label} in {uf} ({cycle} US presidential)"
            out_rows.append({
                "evento_id": evento_id,
                "data": datestr,
                "contexto": ctx,
                "uf": uf,
                "ano": cycle,
                "turno": 1,
                "vencedor": (dem_label if winner == "D" else rep_label),
                "partido": party,
                "incumbente": incumbent,
                "poll_lead_pp": round(lead, 2),
                "outcome_real": outcome,
                "probabilidade_prior": round(0.5 + (lead / 80.0), 3),  # rough prior
                "outcome_framing": ctx,
            })
        n_pairs += 1

    fieldnames = ["evento_id","data","contexto","uf","ano","turno","vencedor",
                  "partido","incumbente","poll_lead_pp","outcome_real",
                  "probabilidade_prior","outcome_framing"]
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)
    return {"n_input_rows": n_in, "n_state_date_pairs": n_pairs,
            "n_csv_rows": len(out_rows), "skipped_no_truth": skipped_no_truth}


# ----------------------------------------------- UK extractor (Wikipedia HTML) ---

UK_REGIONS = [
    "Scotland", "Wales", "Northern Ireland", "London",
    "North East England", "North West England", "Yorkshire and the Humber",
    "East Midlands", "West Midlands", "East of England",
    "South East England", "South West England",
]
UK_REGION_CODE = {
    "Scotland": "SCT", "Wales": "WLS", "Northern Ireland": "NIR",
    "London": "LDN", "North East England": "NEE", "North West England": "NWE",
    "Yorkshire and the Humber": "YHB", "East Midlands": "EMD",
    "West Midlands": "WMD", "East of England": "EAS",
    "South East England": "SEE", "South West England": "SWE",
}

# Ground truth: party with the most VOTES in each region in the 2019 GE.
# Source: BBC results-by-region (well-documented public record).
UK_2019_TRUTH = {
    "SCT": "SNP",
    "WLS": "LAB",
    "NIR": "DUP",
    "LDN": "LAB",
    "NEE": "LAB",
    "NWE": "LAB",
    "YHB": "CON",
    "EMD": "CON",
    "WMD": "CON",
    "EAS": "CON",
    "SEE": "CON",
    "SWE": "CON",
}

# Region -> regime taxonomy used by Vila political cohort. UK is multi-party so
# we keep regime labels distinct from US.
UK_REGIME_BY_PARTY = {
    "CON": "right",        # Conservative -> right
    "LAB": "left",         # Labour -> left
    "LD":  "center",       # LibDem -> center
    "SNP": "left",         # Scottish nationalists -> center-left
    "PC":  "center",       # Plaid Cymru
    "DUP": "right",
    "SF":  "left",
    "GRN": "left",
    "BRX": "right",
    "UKIP":"right",
}


def _strip_html(s: str) -> str:
    s = re.sub(r"<sup[^>]*>.*?</sup>", "", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&#160;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_uk_date(s: str) -> date | None:
    s = s.strip()
    # often "5–6 Dec 2019" or "5 Dec 2019" - take last day-month-year
    m = re.search(r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})", s)
    if not m:
        return None
    months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
              "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    try:
        return date(int(m.group(3)), months[m.group(2)], int(m.group(1)))
    except (KeyError, ValueError):
        return None


def _parse_pct(s: str) -> float | None:
    s = _strip_html(s).replace("%", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def build_uk_2019_csv(html_path: Path, out_csv: Path,
                      election_iso: str = "2019-12-12") -> dict:
    """Parse Wikipedia 2019 UK polling page, regional sub-section.

    For each polling row in a regional section, produce 2 CSV rows: winner +
    runner-up (using the actual 2019 regional truth, not poll lead).
    """
    election_dt = date.fromisoformat(election_iso)
    html = html_path.read_text()

    # Walk html, track current h3 region
    items = []
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", html, flags=re.DOTALL):
        items.append((m.start(), "h3", _strip_html(m.group(1))))
    for m in re.finditer(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>',
                         html, flags=re.DOTALL):
        items.append((m.start(), "tab", m.group()))
    items.sort()

    region = None
    region_polls: dict[str, list[dict]] = defaultdict(list)
    for _, typ, payload in items:
        if typ == "h3":
            region = payload if payload in UK_REGIONS else None
            continue
        if region is None:
            continue
        # parse table
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", payload, flags=re.DOTALL)
        if not rows:
            continue
        # first row is header; figure column index for date, sample, party shares
        header_cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", rows[0], flags=re.DOTALL)
        if not header_cells:
            continue
        # We expect: Date(s), Pollster, Sample size, then party columns (Con, Lab, ...)
        # Build column idx -> column name
        col_names = [_strip_html(c) for c in header_cells]
        col_idx = {name: i for i, name in enumerate(col_names) if name}

        def find_col(*aliases) -> int | None:
            for a in aliases:
                if a in col_idx:
                    return col_idx[a]
            return None

        i_date  = find_col("Date(s) conducted", "Date(s)", "Date conducted", "Date")
        i_con   = find_col("Con")
        i_lab   = find_col("Lab")
        i_ld    = find_col("LD")
        i_snp   = find_col("SNP")
        i_pc    = find_col("PC")
        i_grn   = find_col("Grn")
        i_dup   = find_col("DUP")
        i_sf    = find_col("SF")

        if i_date is None:
            continue

        for raw_row in rows[1:]:
            cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", raw_row, flags=re.DOTALL)
            needed = [i for i in (i_date, i_con, i_lab, i_ld) if i is not None]
            if not needed or len(cells) < max(needed) + 1:
                continue
            d = _parse_uk_date(_strip_html(cells[i_date]))
            if d is None:
                continue
            days_to = (election_dt - d).days
            if days_to < 0 or days_to > 365 * 2:  # filter clearly garbage
                continue
            shares = {}
            for code, idx in (("CON", i_con), ("LAB", i_lab), ("LD", i_ld),
                              ("SNP", i_snp), ("PC", i_pc), ("GRN", i_grn),
                              ("DUP", i_dup), ("SF", i_sf)):
                if idx is None:
                    continue
                if idx >= len(cells):
                    continue
                v = _parse_pct(cells[idx])
                if v is not None:
                    shares[code] = v
            if not shares:
                continue
            region_polls[region].append({
                "date": d,
                "days_to": days_to,
                "shares": shares,
            })

    # Emit CSV rows: per region, per poll-date, build winner=1 + runner-up=0
    out_rows = []
    n_used = 0
    fieldnames = ["evento_id","data","contexto","uf","ano","turno","vencedor",
                  "partido","incumbente","poll_lead_pp","outcome_real",
                  "probabilidade_prior","outcome_framing"]
    for region, polls in region_polls.items():
        uf = UK_REGION_CODE[region]
        truth_party = UK_2019_TRUTH.get(uf)
        if not truth_party:
            continue
        for p in polls:
            if p["days_to"] > DAYS_FILTER:
                continue
            shares = p["shares"]
            # main contenders: top-2 by share
            sorted_ps = sorted(shares.items(), key=lambda kv: -kv[1])
            if len(sorted_ps) < 2:
                continue
            top1, top2 = sorted_ps[0], sorted_ps[1]
            # winner from real outcome (truth_party). Runner-up = whichever of
            # (top1, top2) is not the truth winner. If truth winner not in
            # poll's shares, skip.
            if truth_party not in shares:
                continue
            runner_party = top2[0] if top1[0] == truth_party else top1[0]
            datestr = p["date"].isoformat()
            for party_code, is_winner in (
                (truth_party, 1),
                (runner_party, 0),
            ):
                if party_code not in shares:
                    continue
                their = shares[party_code]
                other = shares[runner_party] if is_winner else shares[truth_party]
                lead = their - other
                regime = UK_REGIME_BY_PARTY.get(party_code, "center")
                evento_id = f"uk2019_{datestr}_wiki_{uf}_{party_code.lower()}"
                ctx = f"{party_code} vence {region} (UK 2019 GE)"
                out_rows.append({
                    "evento_id": evento_id,
                    "data": datestr,
                    "contexto": ctx,
                    "uf": uf,
                    "ano": 2019,
                    "turno": 1,
                    "vencedor": party_code,
                    "partido": party_code,
                    "incumbente": 1 if party_code == "CON" else 0,  # CON was incumbent govt
                    "poll_lead_pp": round(lead, 2),
                    "outcome_real": is_winner,
                    "probabilidade_prior": round(0.5 + lead / 80.0, 3),
                    "outcome_framing": ctx,
                })
            n_used += 1
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    return {"n_polls_used": n_used, "n_csv_rows": len(out_rows),
            "regions_covered": sorted(set(r["uf"] for r in out_rows))}


# ----------------------------- regime + event construction (cross-country) ---

US_REGIME_BY_PARTY = {"DEM": "dem", "REP": "rep"}


def _row_to_event(r: dict, country: str) -> dict:
    """Build event dict consumed by political_cohort.predict_political."""
    ano = int(r["ano"])
    if country == "US":
        election = {2016: "2016-11-08", 2020: "2020-11-03"}.get(ano, "2020-11-03")
    elif country == "UK":
        election = "2019-12-12"
    else:
        election = "2022-10-02"
    election_dt = date.fromisoformat(election)
    poll_dt = date.fromisoformat(r["data"][:10])
    days = max(0, (election_dt - poll_dt).days)
    lead = float(r["poll_lead_pp"])
    partido = r["partido"]
    if country == "US":
        regime = US_REGIME_BY_PARTY.get(partido, "center")
    elif country == "UK":
        regime = UK_REGIME_BY_PARTY.get(partido, "center")
    else:
        regime = "center"
    return {
        "evento_id": r["evento_id"],
        "uf": r["uf"],
        "ano": ano,
        "data": r["data"],
        "outcome": int(r["outcome_real"]),
        "p_prior": float(r.get("probabilidade_prior", 0.5)),
        "cargo": "presidente" if country == "US" else "deputado_federal",
        "lead_bin": lead_bin(lead),
        "days_bin": days_bin(days),
        "incumbente": int(r.get("incumbente", 0)),
        "regime": regime,
        "context": r.get("outcome_framing", ""),
        "poll_lead_pp": lead,
        "days_to": days,
    }


def load_country_csv(path: Path, country: str) -> list[dict]:
    if not path.exists():
        return []
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return [_row_to_event(r, country) for r in rows]


# ------------------------------------------------- evaluation: MRP vs none ---

def _lead_to_p(lead_pp: float, days: int) -> float:
    sigma = SIGMA_INT + SIGMA_SLO * max(0, days)
    z = lead_pp / max(sigma, 1.0)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def predict_one(e: dict, rates: dict, w_state: float) -> float:
    pred = predict_political(e, rates)
    p_coh = pred["p_raw"]
    p_lnz = _lead_to_p(e.get("poll_lead_pp", 0.0), e.get("days_to", 30))
    p = (1.0 - W_LINZER) * p_coh + W_LINZER * p_lnz
    if w_state > 0:
        p_state = state_baseline_p(rates, e.get("uf", ""), e["regime"])
        if p_state is not None:
            p = (1.0 - w_state) * p + w_state * p_state
    return float(p)


def evaluate(events: list[dict], rates: dict, w_state: float) -> dict:
    if not events:
        return {"n": 0}
    n = len(events)
    brier_sum = 0.0
    hits = 0
    by_uf: dict[str, list[int]] = defaultdict(list)
    for e in events:
        p = predict_one(e, rates, w_state)
        y = int(e["outcome"])
        brier_sum += (p - y) ** 2
        hit = int((p >= 0.5) == bool(y))
        hits += hit
        by_uf[e["uf"]].append(hit)
    return {
        "n": n,
        "brier": brier_sum / n,
        "acc": hits / n,
        "by_uf_acc": {u: round(sum(v) / len(v), 4) for u, v in by_uf.items()},
        "n_per_uf": {u: len(v) for u, v in by_uf.items()},
    }


def evaluate_country(events: list[dict], country: str) -> dict:
    """Year-fold-style: train cohort on the events themselves (single cycle)
    after splitting via leave-one-state-out is impractical (too few states per
    regime). Here we fit on ALL events of that country (in-sample), then
    additionally evaluate a leave-one-state-out (LOSO) baseline to provide a
    leak-safe number. Both numbers are reported."""
    out = {}
    if not events:
        return {"n": 0, "note": "no events"}

    # In-sample (full-fit) for diagnostic only
    rates_full = fit_cohorts_political(events, stein_shrink=STEIN_SHRINK)
    base_full = evaluate(events, rates_full, w_state=0.0)
    mrp_full  = evaluate(events, rates_full, w_state=W_STATE)
    out["in_sample"] = {
        "no_mrp": {"acc": base_full["acc"], "brier": base_full["brier"], "n": base_full["n"]},
        "mrp_w36": {"acc": mrp_full["acc"], "brier": mrp_full["brier"], "n": mrp_full["n"]},
    }

    # LOSO: for each held-out state, fit on others, eval on that state
    states = sorted({e["uf"] for e in events})
    base_acc_sum = 0; base_brier_sum = 0; base_n = 0
    mrp_acc_sum  = 0; mrp_brier_sum  = 0; mrp_n  = 0
    per_state = {}
    for s in states:
        train = [e for e in events if e["uf"] != s]
        test  = [e for e in events if e["uf"] == s]
        if not train or not test:
            continue
        rates = fit_cohorts_political(train, stein_shrink=STEIN_SHRINK)
        base_e = evaluate(test, rates, w_state=0.0)
        mrp_e  = evaluate(test, rates, w_state=W_STATE)
        per_state[s] = {
            "n": base_e["n"],
            "no_mrp_acc": round(base_e["acc"], 4),
            "mrp_acc":    round(mrp_e["acc"], 4),
            "no_mrp_brier": round(base_e["brier"], 4),
            "mrp_brier":    round(mrp_e["brier"], 4),
        }
        base_acc_sum   += base_e["acc"] * base_e["n"]
        base_brier_sum += base_e["brier"] * base_e["n"]
        base_n         += base_e["n"]
        mrp_acc_sum    += mrp_e["acc"] * mrp_e["n"]
        mrp_brier_sum  += mrp_e["brier"] * mrp_e["n"]
        mrp_n          += mrp_e["n"]
    if base_n:
        out["loso"] = {
            "no_mrp": {"acc": base_acc_sum / base_n,
                       "brier": base_brier_sum / base_n,
                       "n": base_n},
            "mrp_w36": {"acc": mrp_acc_sum / mrp_n,
                        "brier": mrp_brier_sum / mrp_n,
                        "n": mrp_n},
            "per_state": per_state,
        }
    out["n_states"] = len(states)
    return out


# ------------------------------------------------------------------ main ---

def main():
    print("=== Vila MRP cross-country validation (Phase 3) ===\n")

    # ---- 1. Build CSVs from raw sources ---------------------------------
    src_2016 = RAW_DIR / "fivethirtyeight_pres_pollavgs_1968-2016.csv"
    src_2020 = RAW_DIR / "fivethirtyeight_pres_pollavgs_2020.csv"
    src_uk   = RAW_DIR / "wiki_uk_2019_polls.html"

    out_2016 = OUT_DIR / "us_2016_president.csv"
    out_2020 = OUT_DIR / "us_2020_president.csv"
    out_uk   = OUT_DIR / "uk_2019_general.csv"

    fetch_status = {}

    if src_2016.exists():
        m = build_us_2party_csv(src_2016, out_2016, 2016, US_2016_TRUTH, "2016-11-08")
        m["source"] = "FiveThirtyEight pres_pollaverages_1968-2016 (GitHub)"
        m["status"] = "ok"
        fetch_status["us_2016"] = m
        print(f"US 2016: {m}")
    else:
        fetch_status["us_2016"] = {"status": "data unavailable",
                                   "note": "538 1968-2016 CSV missing"}

    if src_2020.exists():
        m = build_us_2party_csv(src_2020, out_2020, 2020, US_2020_TRUTH, "2020-11-03")
        m["source"] = "FiveThirtyEight 2020 averages (Wayback Machine snapshot)"
        m["status"] = "ok"
        fetch_status["us_2020"] = m
        print(f"US 2020: {m}")
    else:
        fetch_status["us_2020"] = {"status": "data unavailable",
                                   "note": "538 2020 CSV (Wayback) missing"}

    if src_uk.exists():
        m = build_uk_2019_csv(src_uk, out_uk, "2019-12-12")
        m["source"] = ("Wikipedia: Opinion polling for the 2019 UK general "
                       "election (regional sub-sections)")
        m["status"] = "ok"
        fetch_status["uk_2019"] = m
        print(f"UK 2019: {m}")
    else:
        fetch_status["uk_2019"] = {"status": "data unavailable",
                                   "note": "Wiki UK 2019 HTML missing"}

    # ---- 2. Apply Vila MRP per country ----------------------------------
    print("\n=== Applying Vila MRP architecture per country ===\n")

    results: dict = {"_fetch": fetch_status}

    # 2a. LOSO per country (one-cycle data, leak-safe across STATES)
    country_events = {}
    for label, csv_path, country in (
        ("us_2016", out_2016, "US"),
        ("us_2020", out_2020, "US"),
        ("uk_2019", out_uk,   "UK"),
    ):
        events = load_country_csv(csv_path, country)
        country_events[label] = events
        print(f"-- {label}: {len(events)} events from {csv_path.name}")
        if not events:
            results[label] = {"n": 0, "status": "no events parsed"}
            continue
        evald = evaluate_country(events, country)
        evald["n_events"] = len(events)
        evald["data_path"] = str(csv_path.relative_to(ROOT))
        results[label] = evald
        if "loso" in evald:
            print(f"   LOSO no-MRP: acc={evald['loso']['no_mrp']['acc']:.4f}  "
                  f"brier={evald['loso']['no_mrp']['brier']:.4f}  "
                  f"n={evald['loso']['no_mrp']['n']}")
            print(f"   LOSO MRP w=0.36: acc={evald['loso']['mrp_w36']['acc']:.4f}  "
                  f"brier={evald['loso']['mrp_w36']['brier']:.4f}  "
                  f"n={evald['loso']['mrp_w36']['n']}")

    # 2b. Cross-cycle for US: train on 2016, test on 2020 (and vice versa).
    # This is where MRP's (state, regime) baseline can transfer across cycles.
    print("\n-- US cross-cycle (year-fold) --")
    us_xc = {}
    for train_lab, test_lab in (("us_2016", "us_2020"), ("us_2020", "us_2016")):
        tr = country_events.get(train_lab) or []
        te = country_events.get(test_lab)  or []
        if not tr or not te:
            us_xc[f"train_{train_lab}_test_{test_lab}"] = {"note": "missing data"}
            continue
        rates = fit_cohorts_political(tr, stein_shrink=STEIN_SHRINK)
        base = evaluate(te, rates, w_state=0.0)
        mrp  = evaluate(te, rates, w_state=W_STATE)
        us_xc[f"train_{train_lab}_test_{test_lab}"] = {
            "n_train": len(tr), "n_test": len(te),
            "no_mrp": {"acc": base["acc"], "brier": base["brier"], "n": base["n"]},
            "mrp_w36": {"acc": mrp["acc"], "brier": mrp["brier"], "n": mrp["n"]},
            "delta_acc_mrp_minus_baseline": mrp["acc"] - base["acc"],
        }
        print(f"   train={train_lab} test={test_lab}: "
              f"no-MRP acc={base['acc']:.4f}  MRP acc={mrp['acc']:.4f}  "
              f"delta={mrp['acc']-base['acc']:+.4f}")
    results["us_year_fold_cross_cycle"] = us_xc

    # ---- 3. Aggregate average across non-BR cycles ----------------------
    accs = []
    briers = []
    weights = []
    for k in ("us_2016", "us_2020", "uk_2019"):
        v = results.get(k, {})
        loso = v.get("loso") if isinstance(v, dict) else None
        if loso:
            accs.append(loso["mrp_w36"]["acc"])
            briers.append(loso["mrp_w36"]["brier"])
            weights.append(loso["mrp_w36"]["n"])
    if accs:
        wsum = sum(weights)
        results["avg_non_br"] = {
            "acc_unweighted":   sum(accs) / len(accs),
            "acc_weighted":     sum(a * w for a, w in zip(accs, weights)) / wsum,
            "brier_unweighted": sum(briers) / len(briers),
            "brier_weighted":   sum(b * w for b, w in zip(briers, weights)) / wsum,
            "n_total":          wsum,
        }
    else:
        results["avg_non_br"] = {"note": "no usable LOSO results"}

    # BR comparison from existing artifact
    br_compare = {}
    bp = ROOT / "data" / "political_autoresearch_results.json"
    if bp.exists():
        try:
            data = json.loads(bp.read_text())
            best = data.get("best", {})
            br_compare = {
                "br_avg_acc_year_fold_cv":   best.get("avg_acc"),
                "br_avg_brier_year_fold_cv": best.get("avg_brier"),
                "br_per_year_acc":           best.get("per_year_acc", {}),
                "source": "data/political_autoresearch_results.json (best config)",
            }
        except Exception as exc:
            br_compare = {"note": f"BR comparison parse failed: {exc}"}
    results["br_2024_for_comparison"] = br_compare

    RESULT_PATH.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved -> {RESULT_PATH.relative_to(ROOT)}")

    # short summary
    print("\n=== SUMMARY ===")
    for k in ("us_2016", "us_2020", "uk_2019"):
        v = results.get(k, {})
        loso = v.get("loso") if isinstance(v, dict) else None
        if loso:
            print(f"  {k:<8} n={v.get('n_events')}  "
                  f"no-MRP acc={loso['no_mrp']['acc']:.4f}  "
                  f"MRP acc={loso['mrp_w36']['acc']:.4f}  "
                  f"delta={loso['mrp_w36']['acc']-loso['no_mrp']['acc']:+.4f}")
        else:
            print(f"  {k}: no LOSO results")
    avg = results.get("avg_non_br", {})
    if "acc_weighted" in avg:
        print(f"  avg_non_br (weighted): acc={avg['acc_weighted']:.4f}  "
              f"brier={avg['brier_weighted']:.4f}  n={avg['n_total']}")
    if "br_avg_acc_year_fold_cv" in br_compare:
        print(f"  BR year-fold CV avg acc: {br_compare['br_avg_acc_year_fold_cv']}")


if __name__ == "__main__":
    main()
