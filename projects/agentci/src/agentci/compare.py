from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Episode


@dataclass
class StepDiffItem:
    step_index: int
    kind: str
    name: str
    field_path: str
    left: Any
    right: Any
    change_type: str = "changed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "kind": self.kind,
            "name": self.name,
            "field_path": self.field_path,
            "left": self.left,
            "right": self.right,
            "change_type": self.change_type,
        }

    def to_text(self) -> str:
        prefix = f"step {self.step_index} [{self.kind}:{self.name}] {self.field_path}"
        if self.change_type == "added":
            return f"{prefix}: <missing> -> {self.right!r}"
        if self.change_type == "removed":
            return f"{prefix}: {self.left!r} -> <missing>"
        return f"{prefix}: {self.left!r} -> {self.right!r}"


@dataclass
class EpisodeDiff:
    changed: bool
    items: list[str] = field(default_factory=list)
    step_items: list[StepDiffItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "changed": self.changed,
            "items": list(self.items),
            "step_items": [item.to_dict() for item in self.step_items],
        }


def _append_if_changed(items: list[str], label: str, left: Any, right: Any) -> None:
    if left != right:
        items.append(f"{label}: {left!r} -> {right!r}")


def _append_nested_step_diffs(
    step_items: list[StepDiffItem],
    *,
    step_index: int,
    kind: str,
    name: str,
    field_path: str,
    left: Any,
    right: Any,
) -> None:
    if left == right:
        return
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child_path = f"{field_path}.{key}" if field_path else str(key)
            _append_nested_step_diffs(
                step_items,
                step_index=step_index,
                kind=kind,
                name=name,
                field_path=child_path,
                left=left.get(key),
                right=right.get(key),
            )
        return
    step_items.append(
        StepDiffItem(
            step_index=step_index,
            kind=kind,
            name=name,
            field_path=field_path,
            left=left,
            right=right,
        )
    )


def compare_episodes(baseline: Episode, candidate: Episode) -> EpisodeDiff:
    items: list[str] = []
    step_items: list[StepDiffItem] = []

    _append_if_changed(items, "model", baseline.model, candidate.model)
    _append_if_changed(items, "prompt_version", baseline.prompt_version, candidate.prompt_version)
    _append_if_changed(items, "success", baseline.success, candidate.success)
    _append_if_changed(items, "final_output", baseline.final_output, candidate.final_output)
    _append_if_changed(items, "step_count", len(baseline.steps), len(candidate.steps))

    max_steps = max(len(baseline.steps), len(candidate.steps))
    for index in range(max_steps):
        left = baseline.steps[index] if index < len(baseline.steps) else None
        right = candidate.steps[index] if index < len(candidate.steps) else None
        if left is None and right is not None:
            step_items.append(
                StepDiffItem(
                    step_index=index + 1,
                    kind=right.kind,
                    name=right.name,
                    field_path="step",
                    left=None,
                    right=right.payload,
                    change_type="added",
                )
            )
            continue
        if left is not None and right is None:
            step_items.append(
                StepDiffItem(
                    step_index=index + 1,
                    kind=left.kind,
                    name=left.name,
                    field_path="step",
                    left=left.payload,
                    right=None,
                    change_type="removed",
                )
            )
            continue
        assert left is not None and right is not None
        if left.kind != right.kind:
            step_items.append(
                StepDiffItem(
                    step_index=index + 1,
                    kind=left.kind,
                    name=left.name,
                    field_path="kind",
                    left=left.kind,
                    right=right.kind,
                )
            )
            continue
        if left.name != right.name:
            step_items.append(
                StepDiffItem(
                    step_index=index + 1,
                    kind=left.kind,
                    name=left.name,
                    field_path="name",
                    left=left.name,
                    right=right.name,
                )
            )
        _append_nested_step_diffs(
            step_items,
            step_index=index + 1,
            kind=left.kind,
            name=left.name,
            field_path="payload",
            left=left.payload,
            right=right.payload,
        )

    all_metric_keys = sorted(set(baseline.metrics) | set(candidate.metrics))
    for key in all_metric_keys:
        _append_if_changed(
            items,
            f"metric:{key}",
            baseline.metrics.get(key),
            candidate.metrics.get(key),
        )

    items.extend(item.to_text() for item in step_items)
    return EpisodeDiff(changed=bool(items), items=items, step_items=step_items)
