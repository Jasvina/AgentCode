from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
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
    seed: int | None = None
    success: bool = False
    final_output: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    steps: list[EpisodeStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.episode_id:
            errors.append("episode_id is required")
        if not self.agent_name:
            errors.append("agent_name is required")
        if not self.model:
            errors.append("model is required")
        if not self.prompt_version:
            errors.append("prompt_version is required")
        if not isinstance(self.steps, list):
            errors.append("steps must be a list")

        for index, step in enumerate(self.steps, start=1):
            if not step.kind:
                errors.append(f"step {index} kind is required")
            if not step.name:
                errors.append(f"step {index} name is required")
            if not isinstance(step.payload, dict):
                errors.append(f"step {index} payload must be an object")

        return errors

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Episode":
        steps = [EpisodeStep(**step) for step in data.get("steps", [])]
        copied = dict(data)
        copied["steps"] = steps
        return cls(**copied)

    @classmethod
    def load(cls, path: str | Path) -> "Episode":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        episode = cls.from_dict(data)
        errors = episode.validate()
        if errors:
            raise ValueError("; ".join(errors))
        return episode
