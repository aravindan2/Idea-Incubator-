"""Gemini wrapper. Fast, smart, free with credits.

Same interface as the old ollama_client so agents/base.py only changes its import.
Uses google-genai (the newer unified SDK).
"""
from __future__ import annotations

import logging
import re
import time

from google import genai
from google.genai import types

from .config import settings
from .observability import metric

log = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing. Set it in .env.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def generate(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 220,
    timeout_s: float = 30.0,  # kept for signature compat; genai handles its own timeouts
) -> tuple[str, int]:
    """Call Gemini. Return (text, latency_ms). Never raises — degrades to a stub."""
    start = time.perf_counter()
    try:
        cfg = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system,
        )
        resp = _get_client().models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=cfg,
        )
        text = (resp.text or "").strip()
        if not text:
            text = "[empty response]"
    except Exception as e:  # noqa: BLE001
        log.warning("Gemini call failed: %s — returning stub", e)
        text = "[unavailable] The agent could not reach Gemini in time."
    latency_ms = int((time.perf_counter() - start) * 1000)
    metric("cortexos.gemini.latency_ms", latency_ms)
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
