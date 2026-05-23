# Cortexos Evolution Engine

AI-powered startup strategy & market evolution simulator (20–100 yr horizon).
Built for a 2-hour hackathon. Stack: **FastAPI + Streamlit + ClickHouse + Neo4j + Ollama (1B) + Datadog**.

## 60-second mental model

1. User submits a startup idea (e.g. "AI ad recs from in-store CCTV").
2. Six **perspective agents** (User, Investor, Competitor, Regulatory, Skeptic, Trend) generate opinions via local Ollama.
3. **Simulation engine** runs Bass diffusion + Markov scenarios over 0–100 years per segment.
4. Every event lands in **ClickHouse** (the temporal brain). Entities + relationships go to **Neo4j**.
5. **Streamlit** renders the executive dashboard.

## Run order (5 commands, ~3 min)

```bash
# 1. Bring up ClickHouse + Neo4j
docker compose up -d

# 2. Pull a 1B model in Ollama (in another terminal)
ollama pull llama3.2:1b

# 3. Install python deps + init schemas
pip install -r requirements.txt
python -m backend.ingest.seed

# 4. Start the API
uvicorn backend.main:app --reload --port 8000

# 5. Start the dashboard (new terminal)
streamlit run frontend/app.py
```

Open http://localhost:8501 — type an idea, hit "Run Evolution".

## Split of work (2 members, 2 hrs)

| Member | Owns | Files |
|---|---|---|
| **A — Backend/AI** | Agents, simulation, ClickHouse, Neo4j, FastAPI | `backend/**`, `scripts/init_*`, `docker-compose.yml` |
| **B — Frontend/Demo** | Streamlit dashboard, seed data, Datadog, demo script | `frontend/**`, `seed_data/**`, `backend/observability.py`, `DEMO_SCRIPT.md` |

Sync at the 60-min mark — by then A has `/simulate` returning JSON, B has the dashboard reading mock JSON. Last 30 min = wire real → mock swap and rehearse.

## Why this wins

- **ClickHouse star moment**: temporal aggregations over 1.2M+ simulated events (`AggregatingMergeTree`, materialized views, `quantilesTDigest`). Show the query inside the demo.
- **Neo4j**: pretty competitor/segment graph rendered live in the dashboard.
- **Datadog**: one screenshot of agent-call latency + sim throughput. Judges love it.
- **Story**: 100-year market evolution for any startup idea is a memorable hook.
