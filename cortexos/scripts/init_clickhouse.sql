-- Cortexos ClickHouse schema. The whole demo lives or dies on these tables.
-- All tables use MergeTree variants so we get the temporal-aggregation magic
-- that makes judges go "ooh".

CREATE DATABASE IF NOT EXISTS cortexos;
USE cortexos;

-- 1. Raw world signals ingested from Reddit/X/GitHub/news/patents/etc.
CREATE TABLE IF NOT EXISTS world_signals
(
    signal_id        UUID DEFAULT generateUUIDv4(),
    ts               DateTime64(3) DEFAULT now64(),
    source           LowCardinality(String),     -- reddit, x, github, news, patent, market
    category         LowCardinality(String),     -- tech, regulation, sentiment, competition
    entity           String,                     -- company / topic
    text             String,
    sentiment_score  Float32,                    -- -1 .. 1
    impact_score     Float32                     -- 0 .. 1
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (source, category, ts);

-- 2. Simulation timesteps. THIS is the table to query during the demo.
CREATE TABLE IF NOT EXISTS simulation_events
(
    run_id           String,
    scenario         LowCardinality(String),     -- base, high_competition, regulation_tightens, ...
    t_year           Float32,                    -- 0.0 .. 100.0
    segment          LowCardinality(String),     -- small_retailers, enterprise_chains, ...
    adoption_rate    Float32,                    -- 0..1, fraction of segment that adopted
    market_share     Float32,
    revenue_m_usd    Float32,
    cac_usd          Float32,
    churn_rate       Float32,
    sentiment        Float32,
    risk_level       Float32,
    event_label      String,                     -- e.g. "Regulation X passes"
    ts               DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY scenario
ORDER BY (run_id, scenario, segment, t_year);

-- 3. Agent opinions — every LLM call writes a row here.
CREATE TABLE IF NOT EXISTS agent_opinions
(
    run_id      String,
    agent       LowCardinality(String),         -- user_persona, investor, ...
    perspective String,                          -- the agent's voice/role label
    opinion     String,                          -- the model's short answer
    score       Float32,                         -- numeric extract if present (else NaN)
    latency_ms  UInt32,
    model       LowCardinality(String),
    ts          DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (run_id, agent, ts);

-- 4. Materialized rollup: per-scenario-per-year totals. Cheap dashboard query.
CREATE TABLE IF NOT EXISTS sim_rollup_year
(
    run_id              String,
    scenario            LowCardinality(String),
    t_year_bucket       UInt16,
    avg_adoption        AggregateFunction(avg, Float32),
    total_revenue       AggregateFunction(sum, Float32),
    avg_sentiment       AggregateFunction(avg, Float32),
    max_risk            AggregateFunction(max, Float32)
)
ENGINE = AggregatingMergeTree
ORDER BY (run_id, scenario, t_year_bucket);

CREATE MATERIALIZED VIEW IF NOT EXISTS sim_rollup_year_mv
TO sim_rollup_year AS
SELECT
    run_id,
    scenario,
    toUInt16(floor(t_year))            AS t_year_bucket,
    avgState(adoption_rate)            AS avg_adoption,
    sumState(revenue_m_usd)            AS total_revenue,
    avgState(sentiment)                AS avg_sentiment,
    maxState(risk_level)               AS max_risk
FROM simulation_events
GROUP BY run_id, scenario, t_year_bucket;
