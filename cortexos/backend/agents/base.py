"""Perspective agents. Each is a structured-format call to Gemini Flash.

Design choices:
- Force the model into a 2-line VERDICT/SCORE format.
- Strip markdown formatting before parsing (Gemini loves bold).
- Multiple regex fallbacks so we always extract *some* score.
"""
from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Callable

from ..gemini_client import generate
from ..ollama_client import generate as ollama_generate
from ..config import settings
from ..clickhouse_client import insert_opinion
from ..observability import incr

log = logging.getLogger(__name__)


FORMAT_INSTRUCTION = (
    "You MUST respond in this exact plain-text format with no markdown, no asterisks, no bold:\n"
    "VERDICT: <one full sentence, 20-35 words, in your character voice>\n"
    "SCORE: <integer 0 to 10>/10\n"
    "Do not write anything before VERDICT or after the score line."
)

# Permissive regexes. Tolerate **bold**, missing colon, extra spaces, etc.
_VERDICT_RE = re.compile(r"VERDICT[^A-Za-z0-9]{0,5}(.+?)(?=\n\s*SCORE|\Z)", re.IGNORECASE | re.DOTALL)
_SCORE_RE = re.compile(r"SCORE[^\d]{0,10}(\d{1,2}(?:\.\d+)?)", re.IGNORECASE)
# Fallback: "7/10" anywhere
_OUT_OF_TEN_RE = re.compile(r"\b(\d{1,2}(?:\.\d+)?)\s*/\s*10\b")


def _strip_markdown(s: str) -> str:
    """Drop **bold**, __underline__, # headers, leading bullets — anything that
    confuses a literal-match regex."""
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"_{2,}", "", s)
    s = re.sub(r"(?m)^#+\s*", "", s)
    s = re.sub(r"(?m)^[-•]\s*", "", s)
    return s


def _parse(raw: str) -> tuple[str, float]:
    clean = _strip_markdown(raw)

    v = _VERDICT_RE.search(clean)
    verdict = (v.group(1) if v else clean).strip()
    verdict = re.sub(r"\s+", " ", verdict).strip(".:- ")
    if verdict and not verdict.endswith("."):
        verdict += "."

    s = _SCORE_RE.search(clean) or _OUT_OF_TEN_RE.search(clean)
    score = float(s.group(1)) if s else float("nan")
    if score == score:  # not NaN
        score = max(0.0, min(10.0, score))
    return verdict, score


@dataclass
class AgentResult:
    agent: str
    perspective: str
    opinion: str
    score: float
    latency_ms: int

    def to_dict(self) -> dict:
        return asdict(self)


def _run_agent(run_id: str, agent_name: str, perspective: str, system: str, user_prompt: str) -> AgentResult:
    incr("cortexos.agent.calls", tags=[f"agent:{agent_name}"])
    full_system = f"{system}\n\n{FORMAT_INSTRUCTION}"

    if settings.use_ollama == 1:
        raw, latency = ollama_generate(prompt=user_prompt, system=full_system, temperature=0.7, max_tokens=1500)
        model_name = settings.ollama_model
    else:
        raw, latency = generate(prompt=user_prompt, system=full_system, temperature=0.7, max_tokens=1500)
        model_name = settings.gemini_model

    # Log the raw model output once per call — invaluable when scores look wrong.
    log.info("agent=%s raw=%r", agent_name, raw[:400])

    verdict, score = _parse(raw)
    result = AgentResult(
        agent=agent_name,
        perspective=perspective,
        opinion=verdict or raw[:200],
        score=0.0 if score != score else score,
        latency_ms=latency,
    )
    try:
        insert_opinion({
            "run_id": run_id, "agent": agent_name, "perspective": perspective,
            "opinion": result.opinion, "score": result.score,
            "latency_ms": latency, "model": model_name,
        })
    except Exception as e:
        log.warning("Failed to persist opinion for %s: %s", agent_name, e)
    return result


AGENTS: list[tuple[str, str, str, Callable[[str], str]]] = [
    ("user_persona",
     "Maria, independent grocery owner (Small Retailers)",
     "You are Maria, a busy independent grocery owner. You speak bluntly. You care about cost, time-to-value, and not annoying your customers.",
     lambda idea: f"Startup idea: {idea}\n\nWould YOU, Maria, adopt this? Why or why not?"),
    ("investor",
     "Series A VC focused on vertical AI",
     "You are a Series A venture investor. You score by market size, moat, founder edge, and unit economics.",
     lambda idea: f"Startup idea: {idea}\n\nGive your verdict on investability."),
    ("competitor",
     "Head of product at AdTechCorp (incumbent)",
     "You run product at the dominant incumbent in this space.",
     lambda idea: f"A new entrant pitches: {idea}\n\nHow worried are you?"),
    ("regulatory",
     "EU data-protection counsel",
     "You are an EU data-protection lawyer. Flag biometric, consent, retention, cross-border risks.",
     lambda idea: f"Proposed product: {idea}\n\nWhat is the single biggest regulatory risk?"),
    ("skeptic",
     "Devil's-advocate staff engineer",
     "You poke holes in startup pitches for a living.",
     lambda idea: f"Proposed product: {idea}\n\nWhat is the most likely way this fails in production?"),
    ("trend",
     "Macro-trend analyst",
     "You read 100 newsletters a week.",
     lambda idea: f"Proposed product: {idea}\n\nName the macro trend most relevant and whether it's tailwind or headwind."),
]


def run_all_agents(run_id: str, idea: str) -> list[AgentResult]:
    results: dict[str, AgentResult] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(_run_agent, run_id, n, p, s, b(idea)): n for n, p, s, b in AGENTS}
        for f in as_completed(futs):
            r = f.result()
            results[r.agent] = r
    return [results[n] for n, *_ in AGENTS if n in results]
