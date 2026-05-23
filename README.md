# Idea Incubators

A workspace containing the Cortexos Evolution Engine: an AI-powered startup strategy and market evolution simulator.

## Components

- `cortexos/backend`: FastAPI service, agents, simulation engine, ClickHouse + Neo4j clients, Nimble extraction.
- `cortexos/frontend`: Streamlit dashboard and views.
- `cortexos/scripts`: database init and helper scripts.
- `cortexos/seed_data`: sample personas and signals.

## Architecture Overview

- **LLM agents**: Perspective agents generate structured opinions on a startup idea.
- **Simulation engine**: Bass diffusion + Markov scenarios simulate adoption and market evolution.
- **Data layer**: ClickHouse stores simulation events and agent opinions; Neo4j stores the graph.
- **UI**: Streamlit dashboard for interactive analysis and visualization.
- **Extraction**: Nimble integration for web content extraction via API.

## Quick Start

From `cortexos/`:

```bash
# 1. Create .env
copy .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize ClickHouse + seed data
python -m backend.ingest.seed

# 4. Start API
uvicorn backend.main:app --reload --port 8000

# 5. Start dashboard (new terminal)
streamlit run frontend/app.py
```

Open the dashboard at `http://localhost:8501`.

## Environment Variables

Core services (set in `cortexos/.env`):

- `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_DB`, `CLICKHOUSE_SECURE`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `GEMINI_API_KEY`, `GEMINI_MODEL`
- `OLLAMA_HOST`, `OLLAMA_MODEL`
- `NIMBLE_API_KEY`, `NIMBLE_BASE_URL`, `NIMBLE_EXTRACT_PATH`, `NIMBLE_AUTH_HEADER`, `NIMBLE_AUTH_PREFIX`, `NIMBLE_TIMEOUT_S`
- `DD_API_KEY`, `DD_SITE`, `DD_SERVICE`, `DD_ENV`

Note: agents are currently hardcoded to use Ollama in `cortexos/backend/agents/base.py`.

## Nimble Extraction

Call the Nimble proxy endpoint exposed by the backend:

```bash
curl -X POST http://localhost:8000/nimble/extract \
  -H "Content-Type: application/json" \
  -d '{"source":"manual","payload":{"url":"https://example.com"}}'
```

The backend logs extraction requests and responses in ClickHouse (`nimble_extractions`).

## Project Layout

```
Idea_incubators/
  README.md
  cortexos/
    backend/
    frontend/
    scripts/
    seed_data/
```

## Development Notes

- Streamlit UI entrypoint: `cortexos/frontend/app.py`
- API entrypoint: `cortexos/backend/main.py`
- ClickHouse schema: `cortexos/scripts/init_clickhouse.sql`

## Troubleshooting

- If Streamlit shows connection resets, ensure the FastAPI server is running and reachable at `CORTEXOS_API`.
- For missing ClickHouse data, re-run `python -m backend.ingest.seed` after confirming credentials.

## License

Internal project workspace. Add a license if needed.
