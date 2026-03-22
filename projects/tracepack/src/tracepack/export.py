from __future__ import annotations

import json
from pathlib import Path


def _load_manifest(pack_dir: str | Path) -> dict:
    return json.loads((Path(pack_dir) / "manifest.json").read_text(encoding="utf-8"))


def export_manifest_to_jsonl(pack_dir: str | Path, output_path: str | Path) -> int:
    manifest = _load_manifest(pack_dir)
    cases = manifest.get("cases", [])
    target = Path(output_path)
    lines = [json.dumps(case, sort_keys=True) for case in cases]
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(cases)


def _first_prompt(case: dict) -> str:
    for step in case.get("steps", []):
        if step.get("kind") == "model_call":
            prompt = step.get("payload", {}).get("prompt")
            if prompt:
                return str(prompt)
    return str(case.get("episode_id") or "tracepack-case")


def export_pack_to_chat_jsonl(
    pack_dir: str | Path,
    output_path: str | Path,
    *,
    success_only: bool = False,
) -> int:
    manifest = _load_manifest(pack_dir)
    cases = list(manifest.get("cases", []))
    if success_only:
        cases = [case for case in cases if case.get("success")]

    rows = []
    for case in cases:
        row = {
            "messages": [
                {"role": "user", "content": _first_prompt(case)},
                {"role": "assistant", "content": str(case.get("final_output", ""))},
            ],
            "metadata": {
                "episode_id": case.get("episode_id"),
                "agent_name": case.get("agent_name"),
                "model": case.get("model"),
                "prompt_version": case.get("prompt_version"),
                "success": case.get("success"),
                "signature": case.get("signature"),
                "labels": case.get("labels", []),
                "tags": case.get("tags", []),
                "source_path": case.get("source_path"),
            },
        }
        rows.append(json.dumps(row, sort_keys=True))

    target = Path(output_path)
    target.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    return len(rows)
