"""Scenario-level multipliers/biases on the base simulation."""
from __future__ import annotations

# Each scenario tweaks the base sim. Keep keys simple.
SCENARIOS: dict[str, dict] = {
    "base": {
        "label": "Base Case",
        "p_mult": 1.0, "q_mult": 1.0,
        "competition": 0.5, "regulation": 0.3, "tailwind": 0.5,
        "narrative_seed": "Stable macro; competition emerges by year 3.",
    },
    "high_competition": {
        "label": "High Competition",
        "p_mult": 0.85, "q_mult": 0.80,
        "competition": 0.9, "regulation": 0.3, "tailwind": 0.45,
        "narrative_seed": "Two well-funded incumbents fight you on every deal.",
    },
    "regulation_tightens": {
        "label": "Regulation Tightens",
        "p_mult": 0.7, "q_mult": 0.75,
        "competition": 0.4, "regulation": 0.95, "tailwind": 0.35,
        "narrative_seed": "EU AI Act + state privacy laws cap biometric use.",
    },
    "tech_breakthrough": {
        "label": "Tech Breakthrough",
        "p_mult": 1.4, "q_mult": 1.25,
        "competition": 0.5, "regulation": 0.3, "tailwind": 0.9,
        "narrative_seed": "Open-source 1B vision models hit phone-grade silicon.",
    },
}
