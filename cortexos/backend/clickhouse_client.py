"""Thin ClickHouse wrapper. Connection is lazy + memoised."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable, Sequence

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from .config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def client() -> Client:
    log.info("Connecting to ClickHouse %s:%s db=%s", settings.ch_host, settings.ch_port, settings.ch_db)
    return clickhouse_connect.get_client(
        host=settings.ch_host,
        port=settings.ch_port,
        username=settings.ch_user,
        password=settings.ch_password,
        database=settings.ch_db,
        secure=settings.ch_secure,
    )


def insert(table: str, rows: Sequence[Sequence], column_names: Sequence[str]) -> None:
    if not rows:
        return
    client().insert(table=table, data=list(rows), column_names=list(column_names))


def insert_signals(rows: Iterable[dict]) -> None:
    cols = ["source", "category", "entity", "text", "sentiment_score", "impact_score"]
    data = [[r[c] for c in cols] for r in rows]
    insert("world_signals", data, cols)


def insert_sim_events(rows: Iterable[dict]) -> None:
    cols = [
        "run_id", "scenario", "t_year", "segment",
        "adoption_rate", "market_share", "revenue_m_usd",
        "cac_usd", "churn_rate", "sentiment", "risk_level", "event_label",
    ]
    data = [[r[c] for c in cols] for r in rows]
    insert("simulation_events", data, cols)


def insert_opinion(row: dict) -> None:
    cols = ["run_id", "agent", "perspective", "opinion", "score", "latency_ms", "model"]
    insert("agent_opinions", [[row[c] for c in cols]], cols)


def insert_nimble_extraction(row: dict) -> None:
    cols = [
        "request_id", "source", "status_code", "ok", "latency_ms",
        "request_json", "response_json", "error",
    ]
    insert("nimble_extractions", [[row[c] for c in cols]], cols)


def query(sql: str, params: dict | None = None) -> list[dict]:
    res = client().query(sql, parameters=params or {})
    return [dict(zip(res.column_names, r)) for r in res.result_rows]


# Pre-baked queries used by the dashboard. Keep them here so the demo
# stays snappy and the SQL is easy to point at when judges ask.
def sim_rollup(run_id: str, scenario: str) -> list[dict]:
    return query(
        """
        SELECT
            t_year_bucket                                 AS year,
            avgMerge(avg_adoption)                        AS adoption,
            sumMerge(total_revenue)                       AS revenue_m,
            avgMerge(avg_sentiment)                       AS sentiment,
            maxMerge(max_risk)                            AS risk
        FROM sim_rollup_year
        WHERE run_id = {run_id:String} AND scenario = {scenario:String}
        GROUP BY year
        ORDER BY year
        """,
        {"run_id": run_id, "scenario": scenario},
    )


def scenario_summary(run_id: str) -> list[dict]:
    return query(
        """
        SELECT
            scenario,
            round(avgMerge(avg_adoption), 3)            AS avg_adoption,
            round(sumMerge(total_revenue) / 1000, 2)    AS peak_revenue_b_usd,
            round(maxMerge(max_risk), 3)                AS peak_risk
        FROM sim_rollup_year
        WHERE run_id = {run_id:String}
        GROUP BY scenario
        ORDER BY peak_revenue_b_usd DESC
        """,
        {"run_id": run_id},
    )


def segment_curves(run_id: str, scenario: str) -> list[dict]:
    return query(
        """
        SELECT
            segment,
            t_year,
            avg(adoption_rate) AS adoption
        FROM simulation_events
        WHERE run_id = {run_id:String} AND scenario = {scenario:String}
        GROUP BY segment, t_year
        ORDER BY segment, t_year
        """,
        {"run_id": run_id, "scenario": scenario},
    )
