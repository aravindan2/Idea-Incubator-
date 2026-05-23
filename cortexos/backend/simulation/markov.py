"""Tiny Markov chain over discrete market regimes. Used to add story shocks."""
from __future__ import annotations

import random

# States: stable, boom, bust, regulated
TRANSITIONS = {
    "stable":    {"stable": 0.85, "boom": 0.06, "bust": 0.05, "regulated": 0.04},
    "boom":      {"stable": 0.35, "boom": 0.55, "bust": 0.05, "regulated": 0.05},
    "bust":      {"stable": 0.40, "boom": 0.05, "bust": 0.50, "regulated": 0.05},
    "regulated": {"stable": 0.20, "boom": 0.05, "bust": 0.05, "regulated": 0.70},
}

# Multipliers applied to adoption rate per regime
REGIME_FACTOR = {
    "stable": 1.0,
    "boom": 1.25,
    "bust": 0.65,
    "regulated": 0.55,
}


def step(state: str, rng: random.Random) -> str:
    probs = TRANSITIONS[state]
    r = rng.random()
    acc = 0.0
    for k, p in probs.items():
        acc += p
        if r <= acc:
            return k
    return state
