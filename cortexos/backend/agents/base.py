"""Perspective agents. Each one is a tiny prompt against the local 1B model.

Design choices:
- Keep prompts short — 1B models are sensitive to length.
- Ask for a one-sentence opinion AND a 0..10 score. Scores get parsed best-effort.
- All agents run in parallel via threads; total wall time ≈ slowest agent.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Callable

from ..ollama_client import generate, extract_score
from ..config import settings
from ..clickhouse_client import insert_opinion
from ..observability import incr

log = logging.getLogger(__name__)


@dataclass
class AgentResult:
    agent: str
    perspective: str
    opinion: str
    score: float
    latency_ms: int

    def to_dict(self) -> dict:
        return asdict(self)


def _run_agent(
    run_id: str,
    agent_name: str,
    perspective: str,
    system: str,
    user_prompt: str,
) -> AgentResult:
    incr("cortexos.agent.calls", tags=[f"agent:{agent_name}"])
    text, latency = generate(prompt=user_prompt, system=system, temperature=0.7, max_tokens=180)
    score = extract_score(text)
    result = AgentResult(
        agent=agent_name,
        perspective=perspective,
        opinion=text,
        score=0.0 if score != score else score,  # NaN -> 0
        latency_ms=latency,
    )
    try:
        insert_opinion({
            "run_id": run_id,
            "agent": agent_name,
            "perspective": perspective,
            "opinion": text,
            "score": result.score,
            "latency_ms": latency,
            "model": settings.ollama_model,
        })
    except Exception as e:  # noqa: BLE001
        log.warning("Failed to persist opinion for %s: %s", agent_name, e)
    return result


# Each agent is a (name, perspective_label, system_prompt, user_prompt_builder)
AGENTS: list[tuple[str, str, str, Callable[[str], str]]] = [
    (
        "user_persona",
        "Maria, independent grocery owner (Small Retailers)",
        "You are Maria, a small-shop owner. You care about cost and ease. Be blunt.",
        lambda idea: f"Idea: {idea}\nIn ONE sentence, would you adopt it and why? Then say 'Score: X/10'.",
    ),
    (
        "investor",
        "Series A VC focused on vertical AI",
        "You are a venture investor. You score by market size × moat × team. Be skeptical but fair.",
        lambda idea: f"Idea: {idea}\nGive a one-line verdict and a 'Score: X/10' for investability.",
    ),
    (
        "competitor",
        "Head of product at incumbent AdTechCorp",
        "You run product at the dominant incumbent. Be candid about threat level.",
        lambda idea: f"Threat: {idea}\nOne-line reaction and 'Score: X/10' for how threatening this is to your business.",
    ),
    (
        "regulatory",
        "EU data-protection counsel",
        "You are an EU data-protection lawyer. Flag biometric, consent, retention risks.",
        lambda idea: f"Idea: {idea}\nIn one sentence: the biggest regulatory risk and 'Score: X/10' for how exposed it is.",
    ),
    (
        "skeptic",
        "Devil's advocate engineer",
        "You poke holes for a living. Find the strongest failure mode in one line.",
        lambda idea: f"Idea: {idea}\nIn one sentence: why this fails in production, and 'Score: X/10' for how fragile it is.",
    ),
    (
        "trend",
        "Macro-trend analyst",
        "You read 100 newsletters a week. Spot the wave that will lift or sink this.",
        lambda idea: f"Idea: {idea}\nName the macro trend most relevant in one line, and 'Score: X/10' for tailwind strength.",
    ),
]


def run_all_agents(run_id: str, idea: str) -> list[AgentResult]:
    """Fan-out all six agents, return ordered results."""
    results: dict[str, AgentResult] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {
            pool.submit(_run_agent, run_id, name, persp, sys, builder(idea)): name
            for name, persp, sys, builder in AGENTS
        }
        for f in as_completed(futs):
            r = f.result()
            results[r.agent] = r
    # Preserve canonical order
    return [results[name] for name, *_ in AGENTS if name in results]
