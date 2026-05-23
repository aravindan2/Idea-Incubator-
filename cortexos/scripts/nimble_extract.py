"""CLI helper to call Nimble extraction through the backend client."""
from __future__ import annotations

import argparse
import json
import sys

from backend.nimble_client import extract


def _load_payload(args: argparse.Namespace) -> dict:
    if args.payload_file:
        with open(args.payload_file, "r", encoding="utf-8") as handle:
            return json.load(handle)
    if args.payload:
        return json.loads(args.payload)
    if args.url:
        return {"url": args.url}
    raise ValueError("Provide --payload, --payload-file, or --url")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Nimble extraction call.")
    parser.add_argument("--url", help="Convenience URL payload field")
    parser.add_argument("--payload", help="Raw JSON string payload")
    parser.add_argument("--payload-file", help="Path to JSON payload file")
    args = parser.parse_args()

    try:
        payload = _load_payload(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Payload error: {exc}", file=sys.stderr)
        return 2

    result = extract(payload)
    output = {
        "ok": result.ok,
        "status_code": result.status_code,
        "latency_ms": result.latency_ms,
        "data": result.data,
        "error": result.error,
    }
    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

