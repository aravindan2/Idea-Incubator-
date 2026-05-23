"""Render the six agent opinions as cards."""
from __future__ import annotations

import streamlit as st

ICONS = {
    "user_persona": "🧑",
    "investor": "💼",
    "competitor": "🥊",
    "regulatory": "⚖️",
    "skeptic": "🧪",
    "trend": "📈",
}


def render(agents: list[dict]) -> None:
    if not agents:
        st.info("No agent opinions yet.")
        return
    cols = st.columns(3)
    for i, a in enumerate(agents):
        with cols[i % 3]:
            icon = ICONS.get(a["agent"], "•")
            score = a.get("score", 0) or 0
            bar_color = "#22c55e" if score >= 7 else "#f59e0b" if score >= 4 else "#ef4444"
            st.markdown(
                f"""
                <div style='border:1px solid #2a2a2a;border-radius:10px;padding:14px;margin-bottom:12px;background:#0f1216;'>
                  <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div style='font-weight:600;color:#9be7ff;'>{icon} {a["agent"].replace("_", " ").title()}</div>
                    <div style='font-size:13px;color:{bar_color};font-weight:700;'>{score:.1f}/10</div>
                  </div>
                  <div style='font-size:11px;color:#888;margin-bottom:6px;'>{a["perspective"]}</div>
                  <div style='font-size:13px;color:#ddd;'>{a["opinion"]}</div>
                  <div style='font-size:10px;color:#555;margin-top:6px;'>{a.get("latency_ms", 0)} ms · local 1B</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
