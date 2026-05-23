"""Render the six agent opinions as cards."""
from __future__ import annotations

import streamlit as st

ICONS = {
    "user_persona": "U",
    "investor": "$",
    "competitor": "X",
    "regulatory": "L",
    "skeptic": "?",
    "trend": "^",
}


def render(agents: list[dict]) -> None:
    if not agents:
        st.info("No agent opinions yet.")
        return
    cols = st.columns(3)
    for i, a in enumerate(agents):
        with cols[i % 3]:
            icon = ICONS.get(a["agent"], "*")
            score = a.get("score", 0) or 0
            bar_color = "#22c55e" if score >= 7 else "#f59e0b" if score >= 4 else "#ef4444"
            agent_label = a["agent"].replace("_", " ").title()
            opinion_text = a["opinion"]
            perspective_text = a["perspective"]
            latency = a.get("latency_ms", 0)
            html = (
                "<div class='card' style='margin-bottom:12px;'>"
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<div style='font-weight:600;color:#9be7ff;'>[{icon}] {agent_label}</div>"
                f"<div style='font-size:13px;color:{bar_color};font-weight:700;'>{score:.1f}/10</div>"
                "</div>"
                f"<div style='font-size:11px;color:#888;margin-bottom:6px;'>{perspective_text}</div>"
                f"<div style='font-size:13px;color:#ddd;'>{opinion_text}</div>"
                f"<div style='font-size:10px;color:#555;margin-top:6px;'>{latency} ms - Ollama</div>"
                "</div>"
            )
            st.markdown(html, unsafe_allow_html=True)
