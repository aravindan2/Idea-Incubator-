# Cortexos Evolution Engine

AI-powered startup strategy & market evolution simulator (20–100 yr horizon).
Built for a 2-hour hackathon. Stack: **FastAPI + Streamlit + ClickHouse Cloud + Neo4j + Gemini 2.0 Flash + Datadog**.

## 60-second mental model

1. User submits a startup idea (e.g. "AI ad recs from in-store CCTV").
2. Six **perspective agents** (User, Investor, Competitor, Regulatory, Skeptic, Trend) generate opinions via Gemini 2.0 Flash.
3. **Simulation engine** runs Bass diffusion + Markov scenarios over 0–100 years per segment.
4. Every event lands in **ClickHouse** (the temporal brain). Entities + relationships go to **Neo4j**.
5. **Streamlit** renders the executive dashboard.

## Run order (5 commands, ~3 min)

```bash
# 1. Set up .env with ClickHouse Cloud + Gemini credentials
cp .env.example .env   # then fill in CLICKHOUSE_* and GEMINI_API_KEY

# 2. Install python deps + init schemas (creates tables in ClickHouse Cloud)
pip install -r requirements.txt
python -m backend.ingest.seed

# 3. Start the API
uvicorn backend.main:app --reload --port 8000

# 4. Start the dashboard (new terminal)
streamlit run frontend/app.py
```

> Get a Gemini API key for free at https://aistudio.google.com/apikey.
> For Neo4j, easiest path is the AuraDB Free tier at https://console.neo4j.io
> (or `docker compose up -d neo4j` if you have Docker running).

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
