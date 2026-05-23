#!/usr/bin/env bash
# One-button local boot. Assumes Docker + Python 3.11+ + Ollama installed.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/5] docker compose up -d"
docker compose up -d

echo "[2/5] waiting for ClickHouse to be ready"
for i in {1..30}; do
  if curl -sf http://localhost:8123/ping >/dev/null 2>&1; then
    echo "  ✓ ClickHouse ready"; break
  fi
  sleep 1
done

echo "[3/5] ensure Ollama model"
ollama pull llama3.2:1b || true

echo "[4/5] python deps"
python -m pip install -q -r requirements.txt

echo "[5/5] seed data + schemas"
python -m backend.ingest.seed

echo ""
echo "Now run, in two separate terminals:"
echo "  uvicorn backend.main:app --reload --port 8000"
echo "  streamlit run frontend/app.py"
