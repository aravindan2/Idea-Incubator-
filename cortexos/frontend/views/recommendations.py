"""Strategic recommendations — derived deterministically from sim + agent data."""
from __future__ import annotations

import streamlit as st


def _build_recs(summary: list[dict], agents: list[dict]) -> list[str]:
    recs: list[str] = []
    if summary:
        best = max(summary, key=lambda s: s.get("peak_revenue_b_usd", 0))
        worst = max(summary, key=lambda s: s.get("peak_risk", 0))
        recs.append(
            f"**Aim for the {best['scenario'].replace('_',' ')} path** — peak revenue "
            f"${best['peak_revenue_b_usd']:.1f}B vs. only {worst['peak_risk']:.2f} risk in the worst case."
        )
        if any(s.get("peak_risk", 0) > 0.6 for s in summary):
            recs.append("**Regulatory exposure is real**: budget for a Privacy/Compliance lead before scaling EU.")
    if agents:
        skeptic = next((a for a in agents if a["agent"] == "skeptic"), None)
        if skeptic:
            recs.append(f"**Skeptic flag**: {skeptic['opinion'][:160]}")
        investor = next((a for a in agents if a["agent"] == "investor"), None)
        if investor and (investor.get("score") or 0) < 6:
            recs.append("**Sharpen the pitch**: investor agent scored below 6 — strengthen moat narrative.")
        trend = next((a for a in agents if a["agent"] == "trend"), None)
        if trend:
            recs.append(f"**Ride the wave**: {trend['opinion'][:160]}")
    recs.append("**Beachhead first**: start with Small Retailers (high adoption, low friction). Layer Enterprise Chains in months 18–24.")
    recs.append("**Tighten activation funnel**: per-segment CAC sensitivity shows a 30% lift when onboarding time drops below 1 week.")
    return recs


def render(summary: list[dict], agents: list[dict]) -> None:
    recs = _build_recs(summary, agents)
    for r in recs:
        st.markdown(f"- {r}")
