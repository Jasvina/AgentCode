from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EpisodeStep:
    kind: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Episode:
    episode_id: str
    agent_name: str
    model: str
    prompt_version: str
    success: bool = False
    final_output: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    steps: list[EpisodeStep] = field(default_factory=list)
