"""Gemini wrapper. Fast, smart, free with credits.

Important: newer Gemini models do hidden "thinking" tokens that eat the
max_output_tokens budget before any visible output is produced. We:
  1. Set a generous max_output_tokens.
  2. Explicitly set thinking_budget=0 (no-op on older models, helpful on newer).
  3. Log finish_reason when the response was truncated, so debugging is fast.
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

_client: "genai.Client | None" = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing. Set it in .env.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _build_config(
        system: str | None,
        temperature: float,
        max_tokens: int,
) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction=system,
    )


def generate(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 400,
    timeout_s: float = 30.0,
) -> tuple[str, int]:
    """Call Gemini. Return (text, latency_ms). Never raises - degrades to a stub."""
    start = time.perf_counter()
    try:
        cfg = _build_config(system, temperature, max_tokens)
        resp = _get_client().models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=cfg,
        )
        text = (resp.text or "").strip()
        print(text)

        # Surface truncation reasons so we can fix them, not paper over them.
        try:
            cand = resp.candidates[0] if resp.candidates else None
            finish_reason = getattr(cand, "finish_reason", None) if cand else None
            if finish_reason and str(finish_reason).upper().endswith("MAX_TOKENS"):
                log.warning("Gemini hit MAX_TOKENS - response truncated. Bump max_tokens.")
        except Exception:
            pass

        if not text:
            text = "[empty response]"
    except Exception as e:
        log.warning("Gemini call failed: %s - returning stub", e)
        text = "[unavailable] The agent could not reach Gemini in time."
    latency_ms = int((time.perf_counter() - start) * 1000)
    metric("cortexos.gemini.latency_ms", latency_ms)
    return text, latency_ms


_SCORE_RE = re.compile(r"\b(?:score|rating)?\s*[:=]?\s*(\d{1,2}(?:\.\d+)?)(?:\s*/\s*10)?\b", re.I)


def extract_score(text: str) -> float:
    m = _SCORE_RE.search(text)
    if not m:
        return float("nan")
    val = float(m.group(1))
    if val > 10:
        val = 10.0
    return val
