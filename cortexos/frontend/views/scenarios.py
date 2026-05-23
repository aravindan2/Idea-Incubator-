"""Market evolution timeline + scenario comparison."""
from __future__ import annotations

import httpx
import logging
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

SCENARIO_LABELS = {
    "base": "Base Case",
    "high_competition": "High Competition",
    "regulation_tightens": "Regulation Tightens",
    "tech_breakthrough": "Tech Breakthrough",
}
COLORS = {
    "base": "#22d3ee",
    "high_competition": "#f43f5e",
    "regulation_tightens": "#f59e0b",
    "tech_breakthrough": "#a855f7",
}
log = logging.getLogger(__name__)


@st.cache_data(ttl=120, show_spinner=False)
def _rollup(api: str, run_id: str, scenario: str) -> pd.DataFrame:
    try:
        r = httpx.get(f"{api}/runs/{run_id}/rollup", params={"scenario": scenario}, timeout=15)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except httpx.HTTPError as exc:
        log.warning("Rollup request failed for run_id=%s scenario=%s: %s", run_id, scenario, exc)
        return pd.DataFrame()


def render(api: str, run_id: str) -> None:
    metric = st.radio(
        "Metric",
        ["adoption", "revenue_m", "sentiment", "risk"],
        horizontal=True,
        format_func=lambda m: {"adoption": "Adoption %", "revenue_m": "Revenue ($M)", "sentiment": "Sentiment", "risk": "Risk"}[m],
    )
    fig = go.Figure()
    for sc, label in SCENARIO_LABELS.items():
        df = _rollup(api, run_id, sc)
        if df.empty:
            continue
        y = df[metric] * (100 if metric == "adoption" else 1)
        fig.add_trace(go.Scatter(
            x=df["year"], y=y, mode="lines+markers",
            name=label, line=dict(color=COLORS[sc], width=2.5),
            marker=dict(size=4),
        ))
    fig.update_layout(
        height=420,
        template="plotly_dark",
        xaxis_title="Year",
        yaxis_title={"adoption": "Adoption (%)", "revenue_m": "Revenue ($M)", "sentiment": "Sentiment", "risk": "Risk"}[metric],
        legend=dict(orientation="h", y=-0.18),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Event markers — show key inflection points for the chosen scenario
    chosen = st.selectbox("Show events for", list(SCENARIO_LABELS.keys()),
                          format_func=lambda s: SCENARIO_LABELS[s])
    try:
        r = httpx.get(f"{api}/runs/{run_id}/events", params={"scenario": chosen, "limit": 60}, timeout=10)
        events = r.json()
    except Exception:  # noqa: BLE001
        events = []
    if events:
        st.markdown("**Key events**")
        for e in events[:12]:
            st.markdown(f"- **Yr {int(e['t_year'])}** · _{e['segment']}_ — {e['event_label']}")


def render_compare(summary: list[dict]) -> None:
    if not summary:
        st.info("Run a simulation first.")
        return
    df = pd.DataFrame(summary)
    df["scenario_label"] = df["scenario"].map(SCENARIO_LABELS).fillna(df["scenario"])
    df = df.rename(columns={
        "avg_adoption": "Avg adoption",
        "peak_revenue_b_usd": "Peak revenue ($B)",
        "peak_risk": "Peak risk",
    })
    st.dataframe(
        df[["scenario_label", "Avg adoption", "Peak revenue ($B)", "Peak risk"]],
        hide_index=True,
        use_container_width=True,
    )
