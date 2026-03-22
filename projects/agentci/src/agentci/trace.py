from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import Episode, EpisodeStep


class EpisodeRecorder:
    def __init__(
        self,
        episode_id: str,
        agent_name: str,
        model: str,
        prompt_version: str,
        seed: int | None = None,
    ) -> None:
        self.episode = Episode(
            episode_id=episode_id,
            agent_name=agent_name,
            model=model,
            prompt_version=prompt_version,
            seed=seed,
        )

    def model_call(
        self,
        prompt: str,
        response: str,
        metadata: dict[str, Any] | None = None,
        name: str = "model",
    ) -> None:
        self.episode.steps.append(
            EpisodeStep(
                kind="model_call",
                name=name,
                payload={
                    "prompt": prompt,
                    "response": response,
                    "metadata": metadata or {},
                },
            )
        )

    def tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        output: Any,
        status: str = "ok",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.episode.steps.append(
            EpisodeStep(
                kind="tool_call",
                name=tool_name,
                payload={
                    "arguments": arguments,
                    "output": output,
                    "status": status,
                    "metadata": metadata or {},
                },
            )
        )

    def note(self, name: str, payload: dict[str, Any]) -> None:
        self.episode.steps.append(EpisodeStep(kind="note", name=name, payload=payload))

    def finish(self, final_output: str, success: bool, metrics: dict[str, Any] | None = None) -> Episode:
        self.episode.final_output = final_output
        self.episode.success = success
        self.episode.metrics = metrics or {}
        return self.episode

    def save(self, path: str | Path) -> None:
        self.episode.save(path)
