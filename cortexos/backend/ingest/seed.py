"""One-shot bootstrap: seed signals into ClickHouse + seed graph into Neo4j.

Usage:
    python -m backend.ingest.seed
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from ..clickhouse_client import client as ch_client, insert_signals
from ..neo4j_client import bootstrap

ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = ROOT / "seed_data"
NEO_CYPHER = ROOT / "scripts" / "init_neo4j.cypher"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("seed")


def seed_clickhouse() -> None:
    log.info("Ensuring ClickHouse schema is in place")
    # init.sql is auto-run by the docker entrypoint for fresh containers; for
    # warm containers (or ClickHouse Cloud) we apply it ourselves here.
    sql = (ROOT / "scripts" / "init_clickhouse.sql").read_text(encoding="utf-8")
    # Skip the CREATE DATABASE / USE statements when running through clickhouse-connect
    for stmt in sql.split(";"):
        s = stmt.strip()
        if not s or s.upper().startswith(("CREATE DATABASE", "USE ")):
            continue
        try:
            ch_client().command(s)
        except Exception as e:  # noqa: BLE001
            log.warning("Statement skipped (%s): %s", e, s[:80])

    signals = json.loads((SEED_DIR / "signals.json").read_text(encoding="utf-8"))
    insert_signals(signals)
    log.info("Inserted %d world_signals", len(signals))


def seed_neo4j() -> None:
    log.info("Seeding Neo4j graph from %s", NEO_CYPHER)
    bootstrap(NEO_CYPHER)
    log.info("Neo4j graph ready")


def main() -> int:
    try:
        seed_clickhouse()
    except Exception as e:  # noqa: BLE001
        log.error("ClickHouse seed failed: %s", e)
        return 1
    try:
        seed_neo4j()
    except Exception as e:  # noqa: BLE001
        log.warning("Neo4j seed failed (continuing): %s", e)
    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
