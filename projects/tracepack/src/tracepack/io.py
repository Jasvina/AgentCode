from __future__ import annotations

import json
from pathlib import Path

from .model import Episode, EpisodeStep


def load_episode(path: str | Path) -> Episode:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    steps = [EpisodeStep(**step) for step in data.get("steps", [])]
    return Episode(
        episode_id=data["episode_id"],
        agent_name=data["agent_name"],
        model=data["model"],
        prompt_version=data["prompt_version"],
        success=bool(data.get("success", False)),
        final_output=str(data.get("final_output", "")),
        metrics=dict(data.get("metrics", {})),
        steps=steps,
    )


def find_episode_files(root: str | Path) -> list[Path]:
    return sorted(Path(root).rglob("*.json"))
