"""FastAPI app — the glue between the dashboard and everything else."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agents import run_all_agents
from .clickhouse_client import (
    insert_nimble_extraction,
    scenario_summary,
    segment_curves,
    sim_rollup,
    query as ch_query,
)
from .neo4j_client import fetch_graph
from .simulation import run_simulation, SCENARIOS, SEGMENTS
from .observability import incr
from .nimble_client import extract as nimble_extract

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("cortexos")

app = FastAPI(title="Cortexos Evolution Engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class SimulateRequest(BaseModel):
    idea: str = Field(..., min_length=4, max_length=500)
    years: int = Field(default=100, ge=5, le=100)
    dt: float = Field(default=0.5, gt=0.0, le=2.0)
    run_id: str | None = None


class SimulateResponse(BaseModel):
    run_id: str
    sim_rows: int
    elapsed_s: float
    agents: list[dict]
    scenario_summary: list[dict]


class NimbleExtractRequest(BaseModel):
    source: str = Field(default="unknown", min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


class NimbleExtractResponse(BaseModel):
    request_id: str
    ok: bool
    status_code: int
    latency_ms: int
    data: dict[str, Any] | None = None
    error: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "scenarios": list(SCENARIOS.keys()), "segments": SEGMENTS}


@app.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest) -> SimulateResponse:
    incr("cortexos.api.simulate")
    run_id = req.run_id or f"run_{uuid.uuid4().hex[:10]}"
    log.info("Simulate run_id=%s idea=%r", run_id, req.idea)

    sim = run_simulation(run_id=run_id, years=req.years, dt=req.dt)

    try:
        agents = [a.to_dict() for a in run_all_agents(run_id, req.idea)]
    except Exception as e:  # noqa: BLE001
        log.warning("Agent run failed: %s", e)
        agents = []

    return SimulateResponse(
        run_id=run_id,
        sim_rows=sim.n_rows,
        elapsed_s=sim.elapsed_s,
        agents=agents,
        scenario_summary=scenario_summary(run_id),
    )


@app.post("/nimble/extract", response_model=NimbleExtractResponse)
def nimble_extract_endpoint(req: NimbleExtractRequest) -> NimbleExtractResponse:
    incr("cortexos.api.nimble_extract")
    if not req.payload:
        raise HTTPException(400, "payload is required")

    result = nimble_extract(req.payload)
    request_id = f"nimble_{uuid.uuid4().hex[:10]}"

    try:
        insert_nimble_extraction({
            "request_id": request_id,
            "source": req.source,
            "status_code": result.status_code,
            "ok": 1 if result.ok else 0,
            "latency_ms": result.latency_ms,
            "request_json": json.dumps(req.payload, ensure_ascii=True),
            "response_json": json.dumps(result.data, ensure_ascii=True) if result.data is not None else "",
            "error": result.error or "",
        })
    except Exception as e:  # noqa: BLE001
        log.warning("Failed to persist Nimble extraction: %s", e)

    return NimbleExtractResponse(
        request_id=request_id,
        ok=result.ok,
        status_code=result.status_code,
        latency_ms=result.latency_ms,
        data=result.data,
        error=result.error,
    )


@app.get("/runs/{run_id}/rollup")
def rollup(run_id: str, scenario: str = "base") -> list[dict]:
    if scenario not in SCENARIOS:
        raise HTTPException(400, f"Unknown scenario {scenario}")
    return sim_rollup(run_id, scenario)


@app.get("/runs/{run_id}/segments")
def segments(run_id: str, scenario: str = "base") -> list[dict]:
    return segment_curves(run_id, scenario)


@app.get("/runs/{run_id}/summary")
def summary(run_id: str) -> list[dict]:
    return scenario_summary(run_id)


@app.get("/runs/{run_id}/opinions")
def opinions(run_id: str) -> list[dict]:
    return ch_query(
        "SELECT agent, perspective, opinion, score, latency_ms "
        "FROM agent_opinions WHERE run_id = {run_id:String} ORDER BY ts",
        {"run_id": run_id},
    )


@app.get("/runs/{run_id}/events")
def events(run_id: str, scenario: str = "base", limit: int = 200) -> list[dict]:
    return ch_query(
        "SELECT t_year, segment, event_label FROM simulation_events "
        "WHERE run_id = {run_id:String} AND scenario = {scenario:String} "
        "AND event_label != '' ORDER BY t_year LIMIT {limit:UInt32}",
        {"run_id": run_id, "scenario": scenario, "limit": limit},
    )


@app.get("/graph")
def graph() -> dict:
    return fetch_graph()
