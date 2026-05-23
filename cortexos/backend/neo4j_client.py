"""Neo4j wrapper. Only what we need: bootstrap, read graph for viz."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from neo4j import GraphDatabase, Driver

from .config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def driver() -> Driver:
    log.info("Connecting to Neo4j %s", settings.neo_uri)
    return GraphDatabase.driver(settings.neo_uri, auth=(settings.neo_user, settings.neo_password))


@contextmanager
def session():
    drv = driver()
    s = drv.session()
    try:
        yield s
    finally:
        s.close()


def bootstrap(cypher_path: str | Path) -> None:
    """Run the init_neo4j.cypher file. Idempotent."""
    text = Path(cypher_path).read_text(encoding="utf-8")
    # Split on `;` but skip empties/comments
    statements = [s.strip() for s in text.split(";") if s.strip() and not s.strip().startswith("//")]
    with session() as s:
        for stmt in statements:
            s.run(stmt)


def fetch_graph() -> dict:
    """Return nodes + edges in a shape pyvis can render."""
    with session() as s:
        nodes = s.run(
            "MATCH (n) RETURN id(n) AS id, labels(n)[0] AS label, properties(n) AS props"
        ).data()
        edges = s.run(
            "MATCH (a)-[r]->(b) "
            "RETURN id(a) AS src, id(b) AS dst, type(r) AS type, properties(r) AS props"
        ).data()
    return {"nodes": nodes, "edges": edges}
