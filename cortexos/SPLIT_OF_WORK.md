# 2-hour Split of Work

Two members, 4 person-hours. Sync every 30 min.

## Member A — Backend / AI (≈2 hrs)

**Owns:** everything that produces data. If the demo can't query ClickHouse or call an agent, A failed.

| Time | Task | File |
|---|---|---|
| 0:00 – 0:15 | `docker compose up -d`, `ollama pull llama3.2:1b`, `pip install -r requirements.txt` | — |
| 0:15 – 0:25 | Run `python -m backend.ingest.seed` and confirm `world_signals` count in ClickHouse | `backend/ingest/seed.py` |
| 0:25 – 0:50 | Bring up FastAPI, test `/health` and `/simulate` with a curl | `backend/main.py` |
| 0:50 – 1:15 | Tune `SCENARIOS` multipliers in `backend/simulation/scenarios.py` until the four lines on the dashboard look visibly different | `backend/simulation/scenarios.py` |
| 1:15 – 1:30 | Make sure `run_all_agents` returns inside 25s on the demo laptop (drop `max_tokens` if not) | `backend/agents/base.py`, `backend/ollama_client.py` |
| 1:30 – 1:45 | Pre-warm ClickHouse with a "demo" run so the dashboard renders instantly on first load | `curl -X POST localhost:8000/simulate -d '{"idea":"..."}'` |
| 1:45 – 2:00 | Buffer / fix whatever B finds | — |

## Member B — Frontend / Story (≈2 hrs)

**Owns:** what judges actually see. The story, the polish, the demo run-through.

| Time | Task | File |
|---|---|---|
| 0:00 – 0:15 | Install deps, `streamlit run frontend/app.py` against mocked JSON | `frontend/app.py` |
| 0:15 – 0:45 | Refine the visual hierarchy of the executive header + scenario tabs. Replace any boring text with founder-facing copy | `frontend/views/dashboard.py`, `frontend/views/recommendations.py` |
| 0:45 – 1:00 | Wire the Neo4j graph viz once A confirms `/graph` works | `frontend/views/network.py` |
| 1:00 – 1:20 | Set up Datadog dashboard with three tiles: `cortexos.ollama.latency_ms`, `cortexos.sim.rows`, `cortexos.agent.calls`. Take a screenshot — that's your sponsor evidence slide | `backend/observability.py` |
| 1:20 – 1:45 | Write/rehearse the 90-second demo from `DEMO_SCRIPT.md` — say it out loud twice | `DEMO_SCRIPT.md` |
| 1:45 – 2:00 | Make sure the ClickHouse Play tab and Neo4j Browser tab are open and prepped | — |

## Shared 30-min check-ins

- **0:30:** A confirms `/simulate` returns valid JSON. B switches to real API.
- **1:00:** Full end-to-end click works. Lock down major UI changes.
- **1:30:** Dress rehearsal of the demo. Time it.
- **1:50:** Final boot of all services. Don't change anything else.
