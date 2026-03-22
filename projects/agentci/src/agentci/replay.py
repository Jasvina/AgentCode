from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Episode


@dataclass
class ReplayResult:
    matched: bool
    mismatches: list[str] = field(default_factory=list)


def replay_episode(episode: Episode, strict: bool = True) -> ReplayResult:
    mismatches: list[str] = []

    for index, step in enumerate(episode.steps, start=1):
        if step.kind == "tool_call":
            payload = step.payload
            if "output" not in payload:
                mismatches.append(f"step {index} tool '{step.name}' is missing an output")
            if strict and payload.get("status") != "ok":
                mismatches.append(
                    f"step {index} tool '{step.name}' has non-ok status '{payload.get('status')}'"
                )
        elif step.kind == "model_call":
            payload = step.payload
            if not payload.get("prompt"):
                mismatches.append(f"step {index} model call is missing a prompt")
            if "response" not in payload:
                mismatches.append(f"step {index} model call is missing a response")

    if not episode.final_output:
        mismatches.append("episode is missing final_output")

    return ReplayResult(matched=not mismatches, mismatches=mismatches)
