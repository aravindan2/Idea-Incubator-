"""Nimble API wrapper for content extraction."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .config import settings
from .observability import incr, metric

log = logging.getLogger(__name__)


@dataclass
class NimbleResult:
    ok: bool
    status_code: int
    latency_ms: int
    data: dict[str, Any] | None
    error: str | None


def _build_url() -> str:
    base = settings.nimble_base_url.rstrip("/")
    path = settings.nimble_extract_path.lstrip("/")
    return f"{base}/{path}"


def _build_headers() -> dict[str, str]:
    if not settings.nimble_api_key:
        return {}
    prefix = settings.nimble_auth_prefix.strip()
    token = settings.nimble_api_key.strip()
    value = f"{prefix} {token}".strip() if prefix else token
    return {settings.nimble_auth_header: value}


def extract(payload: dict[str, Any]) -> NimbleResult:
    """Call Nimble. Return a structured result and never raise."""
    if not settings.nimble_api_key:
        return NimbleResult(False, 0, 0, None, "NIMBLE_API_KEY is missing")

    url = _build_url()
    headers = _build_headers()

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=settings.nimble_timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
        status = resp.status_code
        try:
            data = resp.json()
        except json.JSONDecodeError:
            data = {"raw": resp.text}
        ok = 200 <= status < 300
        error = None
        if not ok:
            error = (data.get("error") if isinstance(data, dict) else None) or resp.text
    except Exception as exc:  # noqa: BLE001
        status = 0
        data = None
        ok = False
        error = f"Nimble request failed: {exc}"

    latency_ms = int((time.perf_counter() - start) * 1000)
    metric("cortexos.nimble.latency_ms", latency_ms)
    incr("cortexos.nimble.calls", tags=[f"ok:{str(ok).lower()}"])
    return NimbleResult(ok, status, latency_ms, data, error)

