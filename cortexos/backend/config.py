"""Central config - load .env once, expose typed settings."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # ClickHouse
    ch_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    ch_port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    ch_user: str = os.getenv("CLICKHOUSE_USER", "cortexos")
    ch_password: str = os.getenv("CLICKHOUSE_PASSWORD", "cortexos")
    ch_db: str = os.getenv("CLICKHOUSE_DB", "cortexos")
    ch_secure: bool = os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true"

    # Neo4j
    neo_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo_password: str = os.getenv("NEO4J_PASSWORD", "cortexos123")

    # Gemini (primary LLM)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Ollama (fallback if you want to swap back to local)
    use_ollama: int = int(os.getenv("USE_OLLAMA", "0"))
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    # Datadog (optional)
    dd_api_key: str = os.getenv("DD_API_KEY", "")
    dd_site: str = os.getenv("DD_SITE", "us5.datadoghq.com")
    dd_service: str = os.getenv("DD_SERVICE", "cortexos")
    dd_env: str = os.getenv("DD_ENV", "hackathon")


settings = Settings()
