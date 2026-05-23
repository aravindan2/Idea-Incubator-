"""Bass diffusion model — the canonical S-curve for product adoption.

F(t) = (1 - exp(-(p+q)t)) / (1 + (q/p) * exp(-(p+q)t))

p = innovation coefficient, q = imitation coefficient.
"""
from __future__ import annotations

import math


def bass_cum_adoption(t: float, p: float, q: float) -> float:
    """Cumulative fraction adopted by time t (years)."""
    if t <= 0:
        return 0.0
    try:
        e = math.exp(-(p + q) * t)
    except OverflowError:
        return 1.0
    num = 1.0 - e
    den = 1.0 + (q / max(p, 1e-9)) * e
    return max(0.0, min(1.0, num / den))


# Per-segment Bass parameters tuned so curves look distinct and demo-friendly.
SEGMENT_BASS = {
    "Small Retailers":      {"p": 0.04, "q": 0.55, "ceiling": 0.78},
    "Tech-savvy Stores":    {"p": 0.06, "q": 0.45, "ceiling": 0.72},
    "Enterprise Chains":    {"p": 0.01, "q": 0.32, "ceiling": 0.60},
    "Privacy Focused Orgs": {"p": 0.005, "q": 0.20, "ceiling": 0.30},
}
