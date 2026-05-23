"""Tiny Ollama wrapper. 1B models need short, focused prompts and tolerant parsing."""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from .config import settings
from .observability import metric

log = logging.getLogger(__name__)


def generate(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 220,
    timeout_s: float = 30.0,
) -> tuple[str, int]:
    """Call Ollama. Return (text, latency_ms). Never raises — degrades to a stub."""
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if system:
        payload["system"] = system

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout_s) as h:
            r = h.post(f"{settings.ollama_host}/api/generate", json=payload)
            r.raise_for_status()
            text = (r.json().get("response") or "").strip()
    except Exception as e:
        log.warning("Ollama call failed: %s — returning stub", e)
        text = "[unavailable] The agent could not reach the local model in time."
    latency_ms = int((time.perf_counter() - start) * 1000)
    metric("cortexos.ollama.latency_ms", latency_ms)
    return text, latency_ms


_SCORE_RE = re.compile(r"\b(?:score|rating)?\s*[:=]?\s*(\d{1,2}(?:\.\d+)?)(?:\s*/\s*10)?\b", re.I)


def extract_score(text: str) -> float:
    """Pull a 0..10 score out of model output. Best-effort."""
    m = _SCORE_RE.search(text)
    if not m:
        return float("nan")
    val = float(m.group(1))
    if val > 10:
        val = 10.0
    return val
