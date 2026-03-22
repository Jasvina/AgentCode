from __future__ import annotations

import json
from pathlib import Path


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).with_name("source_episodes")
    root.mkdir(parents=True, exist_ok=True)

    episodes = [
        {
            "agent_name": "billing-agent",
            "episode_id": "billing-timeout",
            "final_output": "I could not verify invoice INV-7 for alice@example.com with sk_secret.",
            "metrics": {"latency_ms": 120, "owner": "alice@example.com"},
            "model": "gpt-4.1-mini",
            "prompt_version": "billing-v3",
            "steps": [
                {"kind": "model_call", "name": "planner", "payload": {"prompt": "Check invoice", "response": "Call invoice_lookup"}},
                {
                    "kind": "tool_call",
                    "name": "invoice_lookup",
                    "payload": {
                        "arguments": {"invoice_id": "INV-7"},
                        "output": {"error": "timeout", "contact": "alice@example.com"},
                        "status": "error",
                        "metadata": {"token": "sk_secret"},
                    },
                },
                {"kind": "note", "name": "assertion", "payload": {"expected": "status known", "actual": "timeout"}},
            ],
            "success": False,
        },
        {
            "agent_name": "search-agent",
            "episode_id": "search-success",
            "final_output": "Found 3 relevant documents.",
            "metrics": {"latency_ms": 32},
            "model": "gpt-4.1-mini",
            "prompt_version": "search-v1",
            "steps": [
                {"kind": "model_call", "name": "planner", "payload": {"prompt": "Search docs", "response": "Call search_docs"}},
                {"kind": "tool_call", "name": "search_docs", "payload": {"arguments": {"query": "agent regression"}, "output": {"hits": 3}, "status": "ok"}},
            ],
            "success": True,
        },
        {
            "agent_name": "triage-agent",
            "episode_id": "refund-success",
            "final_output": "Refunds are available within 14 days.",
            "metrics": {"latency_ms": 40},
            "model": "gpt-4.1-mini",
            "prompt_version": "refund-v2",
            "steps": [
                {"kind": "model_call", "name": "triage", "payload": {"prompt": "Check refund policy", "response": "Call lookup_policy"}},
                {"kind": "tool_call", "name": "lookup_policy", "payload": {"arguments": {"topic": "refunds"}, "output": {"window_days": 14}, "status": "ok"}},
                {"kind": "model_call", "name": "responder", "payload": {"prompt": "Answer user", "response": "Refunds are available within 14 days."}},
            ],
            "success": True,
        },
    ]

    for episode in episodes:
        _write(root / f"{episode['episode_id']}.json", episode)

    print(f"Wrote sample episodes to {root}")


if __name__ == "__main__":
    main()
