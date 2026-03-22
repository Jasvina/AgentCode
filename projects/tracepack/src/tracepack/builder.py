from __future__ import annotations

import json
from pathlib import Path

from .scanner import PackSummary, scan_directory


def _slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"-", "_", " ", ":"}:
            cleaned.append("-")
    text = "".join(cleaned).strip("-")
    return text or "case"


def build_pack(source_dir: str | Path, output_dir: str | Path, only_failures: bool = False) -> PackSummary:
    summary = scan_directory(source_dir)
    episodes = [episode for episode in summary.episodes if (not only_failures or not episode.success)]

    out_root = Path(output_dir)
    cases_dir = out_root / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    manifest_cases = []
    for index, episode in enumerate(episodes, start=1):
        filename = f"{index:03d}-{_slug(episode.episode_id)}.json"
        case_payload = {
            "episode_id": episode.episode_id,
            "agent_name": episode.agent_name,
            "model": episode.model,
            "prompt_version": episode.prompt_version,
            "success": episode.success,
            "signature": episode.signature,
            "tags": episode.tags,
            "step_count": episode.step_count,
            "final_output": episode.final_output,
            "source_path": episode.source_path,
        }
        (cases_dir / filename).write_text(
            json.dumps(case_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest_cases.append({"file": f"cases/{filename}", **case_payload})

    manifest = {
        "format": "tracepack-v1",
        "source_dir": str(source_dir),
        "case_count": len(manifest_cases),
        "only_failures": only_failures,
        "cases": manifest_cases,
    }
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PackSummary(episodes=episodes)
