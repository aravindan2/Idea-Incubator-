"""Datadog metrics. No-ops if DD_API_KEY is unset, so dev still works."""
from __future__ import annotations

import logging
import os
from typing import Iterable

from .config import settings

log = logging.getLogger(__name__)

_dd_ready = False
try:
    if settings.dd_api_key:
        from datadog import initialize, statsd  # type: ignore
        initialize(
            api_key=settings.dd_api_key,
            statsd_host=os.getenv("DD_AGENT_HOST", "localhost"),
            statsd_port=int(os.getenv("DD_DOGSTATSD_PORT", "8125")),
        )
        _dd_ready = True
        log.info("Datadog metrics initialised for service=%s env=%s", settings.dd_service, settings.dd_env)
except Exception as e:  # noqa: BLE001
    log.warning("Datadog init failed (%s) — metrics will be no-ops", e)


def _tags(extra: Iterable[str] | None) -> list[str]:
    base = [f"service:{settings.dd_service}", f"env:{settings.dd_env}"]
    return base + list(extra or [])


def metric(name: str, value: float, tags: Iterable[str] | None = None) -> None:
    if _dd_ready:
        try:
            statsd.gauge(name, value, tags=_tags(tags))  # type: ignore[name-defined]
        except Exception:  # noqa: BLE001
            pass


def incr(name: str, value: float = 1, tags: Iterable[str] | None = None) -> None:
    if _dd_ready:
        try:
            statsd.increment(name, value, tags=_tags(tags))  # type: ignore[name-defined]
        except Exception:
            pass
