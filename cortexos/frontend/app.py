"""Streamlit dashboard — the face of the demo.

Run:  streamlit run frontend/app.py
"""
from __future__ import annotations

import os
import time

import httpx
import streamlit as st

from views import dashboard, scenarios as scenarios_view, segments as segments_view
from views import network as network_view, recommendations as recs_view, opinions as opinions_view

API = os.getenv("CORTEXOS_API", "http://localhost:8000")

st.set_page_config(
    page_title="Cortexos Evolution Engine",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ------------------------------------------------------------
st.markdown(
    """
    <div style='display:flex;align-items:center;gap:14px;'>
      <div style='font-size:34px;'>◎</div>
      <div>
        <div style='font-size:28px;font-weight:700;color:#9be7ff;letter-spacing:1px;'>CORTEXOS EVOLUTION ENGINE</div>
        <div style='font-size:13px;color:#888;'>AI-Powered Startup Strategy &amp; Market Evolution Simulator (20–100 Years)</div>
      </div>
    </div>
    <hr style='margin:8px 0 18px 0;border-color:#222;' />
    """,
    unsafe_allow_html=True,
)

# --- Sidebar: Idea input ----------------------------------------------
with st.sidebar:
    st.subheader("Founder / User Provides")
    idea = st.text_area(
        "Startup / Idea",
        value="AI-powered advertising recommendation system using CCTV analytics for retail stores.",
        height=140,
    )
    st.caption("Problem · Target Market · Constraints · Pricing · Goals")
    years = st.slider("Horizon (years)", 10, 100, 100, 10)
    dt = st.select_slider("Time step", options=[1.0, 0.5, 0.25], value=0.5)
    run_btn = st.button("▶ Run Evolution", type="primary", use_container_width=True)
    st.divider()
    st.caption("Backend: " + API)

# --- State -------------------------------------------------------------
if "run_id" not in st.session_state:
    st.session_state.run_id = None
if "agents" not in st.session_state:
    st.session_state.agents = []
if "summary" not in st.session_state:
    st.session_state.summary = []

if run_btn:
    with st.spinner("Running 6 agents + 4 scenarios × 4 segments × {y} years…".format(y=years)):
        t0 = time.perf_counter()
        try:
            r = httpx.post(
                f"{API}/simulate",
                json={"idea": idea, "years": years, "dt": dt},
                timeout=120.0,
            )
            r.raise_for_status()
            payload = r.json()
            st.session_state.run_id = payload["run_id"]
            st.session_state.agents = payload["agents"]
            st.session_state.summary = payload["scenario_summary"]
            st.success(
                f"Simulation complete · {payload['sim_rows']:,} rows in "
                f"{payload['elapsed_s']:.2f}s · agents responded in {time.perf_counter() - t0:.1f}s wall"
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"Failed: {e}")

if not st.session_state.run_id:
    st.info("Enter an idea on the left and click **Run Evolution** to start.")
    st.stop()

run_id = st.session_state.run_id

# --- Top: executive dashboard -----------------------------------------
dashboard.render(API, run_id, st.session_state.summary, st.session_state.agents)

st.divider()

tabs = st.tabs([
    "📈 Market Evolution Timeline",
    "🆚 Scenario Comparison",
    "👥 Segment Adoption Curves",
    "🕸 Knowledge Graph",
    "🧠 Agent Opinions",
    "🎯 Strategic Recommendations",
])

with tabs[0]:
    scenarios_view.render(API, run_id)
with tabs[1]:
    scenarios_view.render_compare(st.session_state.summary)
with tabs[2]:
    segments_view.render(API, run_id)
with tabs[3]:
    network_view.render(API)
with tabs[4]:
    opinions_view.render(st.session_state.agents)
with tabs[5]:
    recs_view.render(st.session_state.summary, st.session_state.agents)
