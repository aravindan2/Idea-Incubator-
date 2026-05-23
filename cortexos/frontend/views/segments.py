"""Per-segment adoption curves."""
from __future__ import annotations

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st


@st.cache_data(ttl=120, show_spinner=False)
def _curves(api: str, run_id: str, scenario: str) -> pd.DataFrame:
    r = httpx.get(f"{api}/runs/{run_id}/segments", params={"scenario": scenario}, timeout=15)
    r.raise_for_status()
    return pd.DataFrame(r.json())


def render(api: str, run_id: str) -> None:
    scenario = st.selectbox(
        "Scenario",
        ["base", "high_competition", "regulation_tightens", "tech_breakthrough"],
        format_func=lambda s: s.replace("_", " ").title(),
    )
    df = _curves(api, run_id, scenario)
    if df.empty:
        st.info("No data yet.")
        return
    df["adoption_pct"] = df["adoption"] * 100
    fig = px.line(
        df, x="t_year", y="adoption_pct", color="segment",
        labels={"t_year": "Year", "adoption_pct": "Adoption (%)"},
        template="plotly_dark",
    )
    fig.update_layout(height=420, legend=dict(orientation="h", y=-0.18),
                      margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
