from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Episode


def _flatten(prefix: str, value: Any, output: dict[str, list[Any]]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            _flatten(f"{prefix}.{key}" if prefix else str(key), value[key], output)
        return
    if isinstance(value, list):
        output[prefix] = list(value)
        return
    output[prefix] = [value]


def _episode_fields(episode: Episode) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "model": episode.model,
        "prompt_version": episode.prompt_version,
        "success": episode.success,
        "final_output": episode.final_output,
        "step_count": len(episode.steps),
    }
    for key, value in sorted(episode.metrics.items()):
        fields[f"metric:{key}"] = value
    for index, step in enumerate(episode.steps, start=1):
        fields[f"step {index} kind"] = step.kind
        fields[f"step {index} name"] = step.name
        payload_fields: dict[str, list[Any]] = {}
        _flatten("", step.payload, payload_fields)
        for payload_key, payload_value in sorted(payload_fields.items()):
            fields[f"step {index} payload.{payload_key}"] = payload_value[0]
    return fields


@dataclass
class FlakyField:
    name: str
    values: list[str]
    occurrences: dict[str, int] = field(default_factory=dict)


@dataclass
class FlakyReport:
    episode_count: int
    unstable_fields: list[FlakyField] = field(default_factory=list)

    @property
    def is_stable(self) -> bool:
        return not self.unstable_fields


def analyze_flakiness(episodes: list[Episode]) -> FlakyReport:
    indices = [_episode_fields(episode) for episode in episodes]
    all_keys = sorted({key for item in indices for key in item})
    unstable_fields: list[FlakyField] = []

    for key in all_keys:
        seen: dict[str, int] = {}
        for item in indices:
            rendered = repr(item.get(key))
            seen[rendered] = seen.get(rendered, 0) + 1
        if len(seen) > 1:
            unstable_fields.append(
                FlakyField(
                    name=key,
                    values=sorted(seen),
                    occurrences=dict(sorted(seen.items(), key=lambda pair: pair[0])),
                )
            )

    return FlakyReport(episode_count=len(episodes), unstable_fields=unstable_fields)
