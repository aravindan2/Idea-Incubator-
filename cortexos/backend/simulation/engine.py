"""Simulation engine.

For each (scenario × segment × year) we produce a row in ClickHouse with:
adoption_rate, market_share, revenue, CAC, churn, sentiment, risk, event_label.

The math is deterministic-ish (Bass + scenario multipliers) with stochastic
regime shocks (Markov). 4 scenarios × 4 segments × 101 yearly ticks × 10
sub-steps = ~16k rows by default. Plenty for ClickHouse aggregation queries.
"""
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Iterable

from ..clickhouse_client import insert_sim_events
from ..observability import metric, incr
from .bass import bass_cum_adoption, SEGMENT_BASS
from .markov import step as markov_step, REGIME_FACTOR
from .scenarios import SCENARIOS

log = logging.getLogger(__name__)

SEGMENTS = list(SEGMENT_BASS.keys())

# Per-segment economics — keep simple.
SEGMENT_ECON = {
    "Small Retailers":      {"size": 1_500_000, "arpu_usd": 480,   "base_cac": 120,  "churn": 0.18},
    "Tech-savvy Stores":    {"size":   220_000, "arpu_usd": 1_800, "base_cac": 400,  "churn": 0.12},
    "Enterprise Chains":    {"size":     3_000, "arpu_usd": 220_000, "base_cac": 35_000, "churn": 0.06},
    "Privacy Focused Orgs": {"size":    40_000, "arpu_usd": 1_400, "base_cac": 600,  "churn": 0.10},
}


@dataclass
class SimResult:
    run_id: str
    n_rows: int
    elapsed_s: float


def _yearly_event_label(year: int, scenario: str, regime: str) -> str:
    if year == 0:
        return f"Launch ({SCENARIOS[scenario]['label']})"
    if regime != "stable" and year % 5 == 0:
        return {
            "boom":      f"Year {year}: capital flooding into vertical AI",
            "bust":      f"Year {year}: funding winter cuts marketing budgets",
            "regulated": f"Year {year}: new rule constrains data use",
        }[regime]
    if scenario == "regulation_tightens" and year in (2, 7, 15):
        return f"Year {year}: regulatory escalation in {SCENARIOS[scenario]['label']}"
    if scenario == "tech_breakthrough" and year in (1, 4):
        return f"Year {year}: open-source breakthrough resets the cost curve"
    return ""


def _simulate_one(run_id: str, scenario: str, years: int, dt: float, seed: int) -> list[dict]:
    rng = random.Random(seed)
    cfg = SCENARIOS[scenario]
    rows: list[dict] = []

    regime = "stable"
    t = 0.0
    while t <= years + 1e-9:
        # Step regime once per year boundary
        if abs(t - round(t)) < 1e-6 and t > 0:
            regime = markov_step(regime, rng)
        regime_mult = REGIME_FACTOR[regime]

        for seg in SEGMENTS:
            bass = SEGMENT_BASS[seg]
            econ = SEGMENT_ECON[seg]
            p = bass["p"] * cfg["p_mult"]
            q = bass["q"] * cfg["q_mult"]
            ceiling = bass["ceiling"] * (1 - 0.35 * cfg["regulation"])

            adoption = bass_cum_adoption(t, p, q) * ceiling * regime_mult
            adoption = max(0.0, min(1.0, adoption))

            # Market share = fraction of adopters captured against competition
            share = adoption * (1 - 0.6 * cfg["competition"]) * (0.5 + 0.5 * cfg["tailwind"])
            share = max(0.0, min(1.0, share))

            customers = econ["size"] * share
            revenue_m = customers * econ["arpu_usd"] / 1_000_000.0

            cac = econ["base_cac"] * (1 + 0.4 * cfg["competition"]) / (0.6 + 0.4 * cfg["tailwind"])
            churn = econ["churn"] * (1 + 0.3 * (1 - cfg["tailwind"]))

            # Sentiment: positive tailwind lifts, regulation/competition drags
            sentiment = 0.4 * cfg["tailwind"] - 0.3 * cfg["regulation"] - 0.2 * cfg["competition"]
            sentiment += rng.uniform(-0.05, 0.05)
            sentiment = max(-1.0, min(1.0, sentiment))

            risk = 0.55 * cfg["regulation"] + 0.35 * cfg["competition"] + 0.1 * (1 - cfg["tailwind"])
            if regime == "regulated":
                risk = min(1.0, risk + 0.15)
            if regime == "bust":
                risk = min(1.0, risk + 0.10)

            event_label = _yearly_event_label(int(round(t)), scenario, regime) if abs(t - round(t)) < 1e-6 else ""

            rows.append({
                "run_id": run_id,
                "scenario": scenario,
                "t_year": float(t),
                "segment": seg,
                "adoption_rate": float(adoption),
                "market_share": float(share),
                "revenue_m_usd": float(revenue_m),
                "cac_usd": float(cac),
                "churn_rate": float(churn),
                "sentiment": float(sentiment),
                "risk_level": float(risk),
                "event_label": event_label,
            })

        t += dt
    return rows


def run_simulation(
    run_id: str,
    years: int = 100,
    dt: float = 0.5,
    scenarios: Iterable[str] | None = None,
    seed: int = 42,
) -> SimResult:
    """Run all scenarios and persist to ClickHouse."""
    start = time.perf_counter()
    scenarios = list(scenarios or SCENARIOS.keys())
    all_rows: list[dict] = []
    for i, sc in enumerate(scenarios):
        rows = _simulate_one(run_id, sc, years, dt, seed=seed + i)
        all_rows.extend(rows)
    log.info("Simulated %d rows across %d scenarios", len(all_rows), len(scenarios))

    # Batch insert
    insert_sim_events(all_rows)

    elapsed = time.perf_counter() - start
    metric("cortexos.sim.rows", len(all_rows))
    metric("cortexos.sim.duration_s", elapsed)
    incr("cortexos.sim.runs")
    return SimResult(run_id=run_id, n_rows=len(all_rows), elapsed_s=elapsed)
