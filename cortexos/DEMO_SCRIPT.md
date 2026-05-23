# Cortexos — 90-Second Demo Script

**Goal:** Win the ClickHouse + Neo4j sponsor prize and the "best storytelling" award.

## Setup checklist (do BEFORE the demo, not on stage)

- [ ] ClickHouse Cloud service running; `.env` filled in
- [ ] `GEMINI_API_KEY` set in `.env`; smoke-test with `python -c "from backend.gemini_client import generate; print(generate('say hi', max_tokens=20))"`
- [ ] Neo4j AuraDB (or local docker neo4j) reachable
- [ ] `python -m backend.ingest.seed` ran clean
- [ ] `uvicorn backend.main:app --port 8000` running, hit `/health` once
- [ ] `streamlit run frontend/app.py` open in browser, idea pre-filled
- [ ] Open a 2nd tab to `http://localhost:8123/play` (ClickHouse Play) with this query pre-typed:

  ```sql
  SELECT
    scenario,
    toUInt16(floor(t_year)) AS year,
    round(avg(adoption_rate), 3) AS adoption,
    round(sum(revenue_m_usd), 1) AS revenue_m,
    round(avg(sentiment), 2) AS sentiment
  FROM cortexos.simulation_events
  WHERE run_id = '<paste-after-run>'
  GROUP BY scenario, year
  ORDER BY scenario, year;
  ```

- [ ] Open Neo4j Browser at `http://localhost:7474` with this query ready:

  ```cypher
  MATCH p = (s:Segment)-[r]-(x) RETURN p LIMIT 50
  ```

- [ ] Open the Datadog dashboard with `cortexos.*` metrics filtered

---

## 90-second talk track

> **0:00 — Hook (10s)**
> "Every founder pitches a 5-year vision. We built the engine that simulates the next **100**. Cortexos takes one sentence — a startup idea — and renders the entire market evolution around it."

> **0:10 — Type the idea, hit Run (5s)**
> Type "AI ad recs from CCTV in retail" → click **Run Evolution**.

> **0:15 — While it runs, narrate the architecture (20s)**
> "Under the hood: six perspective agents — a user persona, an investor, a competitor, a regulator, a skeptic, a trend analyst — all running on **Gemini 2.0 Flash** in parallel. While they think, a Bass-diffusion + Markov-chain simulator generates 16,000 timesteps across four scenarios. Every event lands in **ClickHouse Cloud**. Entities and relationships go to **Neo4j**."

> **0:35 — Dashboard returns (5s)**
> Point at the **viability score** (top-left, big number) and the **scenario summary**.

> **0:40 — Market Evolution tab (15s)**
> Click through Adoption → Revenue → Sentiment → Risk. Hover the inflection-point markers: "Year 7, regulation tightens." "Year 12, open-source breakthrough." The model isn't generating these — the simulation is.

> **0:55 — ClickHouse moment (15s)** ⭐ *this is the sponsor money shot*
> Switch tab to ClickHouse Play. Paste the run_id. Run the temporal aggregation. Show it returns in **<50ms** over ~16k rows. Say: "This is what makes ClickHouse the right primary store for any agentic system — every agent action, every simulation tick, every world signal lives here, and you can ask it any temporal question in milliseconds."

> **1:10 — Neo4j moment (10s)**
> Flip to the Knowledge Graph tab in Streamlit (or Neo4j browser). "Segments, competitors, regulations — all related. We use Neo4j to answer 'which regulation constrains which segment.'"

> **1:20 — Agent Opinions tab (5s)**
> Show the six cards. "Six personas. Six scores. One investor's hot take. All in under 2 seconds via Gemini Flash."

> **1:25 — Strategic Recommendations (5s)**
> "And it ends with what a founder actually needs: where to start, what to fear, when to scale."

> **1:30 — Close**
> "100 years of strategy. 90 seconds of demo. All powered by ClickHouse, Neo4j, and a tiny local model. Thank you."

---

## If something breaks on stage

- **Gemini hangs / rate-limits** → close the tab; the agents will return stub text and the dashboard still works. Pivot to ClickHouse.
- **ClickHouse refuses connection** → run on the same machine; show the Streamlit charts which cache aggressively.
- **Neo4j down** → skip the tab; mention it in passing.
- **Sim takes too long** → drop horizon to 25 years in the sidebar.

## What to point at for each sponsor

- **ClickHouse** → temporal query in Play, `AggregatingMergeTree` schema, `quantilesTDigest` future use
- **Neo4j** → the live graph viz + the Cypher constraints
- **Datadog** → `cortexos.gemini.latency_ms`, `cortexos.sim.rows`, `cortexos.agent.calls` metrics
- **Obsidian** *(stretch)* → mention as the "living wiki" of run summaries — show README.
- **Nimble** *(stretch)* → mention orchestration layer in the architecture slide.
