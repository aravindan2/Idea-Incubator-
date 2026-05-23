"""Neo4j knowledge graph — segments, competitors, regulations."""
from __future__ import annotations

import httpx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

LABEL_COLOR = {
    "Segment": "#22d3ee",
    "Competitor": "#f43f5e",
    "Regulation": "#f59e0b",
}


@st.cache_data(ttl=300, show_spinner=False)
def _fetch(api: str) -> dict:
    r = httpx.get(f"{api}/graph", timeout=10)
    r.raise_for_status()
    return r.json()


def render(api: str) -> None:
    try:
        g = _fetch(api)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Graph not available: {e}")
        return

    net = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="white", directed=True)
    net.barnes_hut(gravity=-12000, central_gravity=0.4)
    for n in g["nodes"]:
        label = n["props"].get("name", str(n["id"]))
        color = LABEL_COLOR.get(n["label"], "#9be7ff")
        title = f"{n['label']}: " + ", ".join(f"{k}={v}" for k, v in n["props"].items())
        net.add_node(n["id"], label=label, color=color, title=title)
    for e in g["edges"]:
        net.add_edge(e["src"], e["dst"], label=e["type"], color="#555")
    html = net.generate_html(notebook=False)
    components.html(html, height=520, scrolling=False)
