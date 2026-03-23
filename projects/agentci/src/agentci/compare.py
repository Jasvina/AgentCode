from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Episode


@dataclass
class EpisodeDiff:
    changed: bool
    items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "changed": self.changed,
            "items": list(self.items),
        }


def _append_if_changed(items: list[str], label: str, left: Any, right: Any) -> None:
    if left != right:
        items.append(f"{label}: {left!r} -> {right!r}")


def compare_episodes(baseline: Episode, candidate: Episode) -> EpisodeDiff:
    items: list[str] = []

    _append_if_changed(items, "model", baseline.model, candidate.model)
    _append_if_changed(items, "prompt_version", baseline.prompt_version, candidate.prompt_version)
    _append_if_changed(items, "success", baseline.success, candidate.success)
    _append_if_changed(items, "final_output", baseline.final_output, candidate.final_output)
    _append_if_changed(items, "step_count", len(baseline.steps), len(candidate.steps))

    max_steps = min(len(baseline.steps), len(candidate.steps))
    for index in range(max_steps):
        left = baseline.steps[index]
        right = candidate.steps[index]
        if left.kind != right.kind:
            items.append(f"step {index + 1} kind: {left.kind!r} -> {right.kind!r}")
            continue
        if left.name != right.name:
            items.append(f"step {index + 1} name: {left.name!r} -> {right.name!r}")
        if left.payload != right.payload:
            all_payload_keys = sorted(set(left.payload) | set(right.payload))
            for key in all_payload_keys:
                if left.payload.get(key) != right.payload.get(key):
                    items.append(
                        f"step {index + 1} payload.{key}: "
                        f"{left.payload.get(key)!r} -> {right.payload.get(key)!r}"
                    )

    all_metric_keys = sorted(set(baseline.metrics) | set(candidate.metrics))
    for key in all_metric_keys:
        _append_if_changed(
            items,
            f"metric:{key}",
            baseline.metrics.get(key),
            candidate.metrics.get(key),
        )

    return EpisodeDiff(changed=bool(items), items=items)
