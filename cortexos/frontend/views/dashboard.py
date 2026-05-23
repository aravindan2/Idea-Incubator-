"""Executive dashboard row: viability gauge, KPIs, sponsor stripe."""
from __future__ import annotations

import httpx
import streamlit as st


def _viability_score(summary: list[dict], agents: list[dict]) -> int:
    """0..100 — a hand-wavy aggregate the founder sees first."""
    base = 0
    if summary:
        # Highest peak revenue scenario contributes
        peak = max(s.get("peak_revenue_b_usd", 0) for s in summary) or 0
        base += min(50, peak)  # 50 points cap from revenue
    if agents:
        scores = [a.get("score", 0) for a in agents if a.get("score")]
        if scores:
            base += int((sum(scores) / len(scores)) * 5)  # up to 50 from agent average
    return max(0, min(100, int(base)))


def render(api: str, run_id: str, summary: list[dict], agents: list[dict]) -> None:
    score = _viability_score(summary, agents)
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"

    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        st.markdown(
            f"<div style='font-size:13px;color:#888'>OVERALL VIABILITY</div>"
            f"<div style='font-size:54px;font-weight:800;color:{color};line-height:1'>{score}<span style='font-size:18px;color:#888'>/100</span></div>",
            unsafe_allow_html=True,
        )
    if summary:
        best = max(summary, key=lambda s: s.get("peak_revenue_b_usd", 0))
        worst = max(summary, key=lambda s: s.get("peak_risk", 0))
        avg_adopt = sum(s.get("avg_adoption", 0) for s in summary) / max(len(summary), 1)
        with c2:
            st.metric("Best scenario", best["scenario"], f"${best['peak_revenue_b_usd']:.1f}B peak")
        with c3:
            st.metric("Highest risk scenario", worst["scenario"], f"{worst['peak_risk']:.2f} risk")
        with c4:
            st.metric("Avg adoption (all scenarios)", f"{avg_adopt:.1%}")
    else:
        c2.info("Summary not yet available")

    # Tiny sponsor stripe — judges notice
    st.markdown(
        "<div style='margin-top:8px;font-size:11px;color:#666'>"
        "Powered by <b style='color:#FFCC00'>ClickHouse</b> · "
        "<b style='color:#018BFF'>Neo4j</b> · "
        "<b style='color:#774AA4'>Obsidian</b> · "
        "<b style='color:#632CA6'>Datadog</b> · "
        "<b style='color:#23B26D'>Nimble</b>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Run ID badge
    st.caption(f"Run ID: `{run_id}` — query in ClickHouse: `SELECT * FROM simulation_events WHERE run_id = '{run_id}'`")
