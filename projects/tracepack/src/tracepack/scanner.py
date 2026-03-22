from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .io import find_episode_files, load_episode
from .model import Episode
from .redact import contains_sensitive_value


@dataclass
class CaseSummary:
    source_path: str
    episode_id: str
    agent_name: str
    model: str
    prompt_version: str
    success: bool
    final_output: str
    step_count: int
    signature: str
    tags: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    steps: list[dict] = field(default_factory=list)
    contains_sensitive: bool = False


@dataclass
class PackSummary:
    episodes: list[CaseSummary]

    @property
    def successes(self) -> int:
        return sum(1 for episode in self.episodes if episode.success)

    @property
    def failures(self) -> int:
        return sum(1 for episode in self.episodes if not episode.success)

    @property
    def kind_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for episode in self.episodes:
            for tag in episode.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts


def _failure_signature(episode: Episode) -> str:
    if episode.success:
        return "success"
    if not episode.steps:
        return "failure:empty"
    last_step = episode.steps[-1]
    return f"failure:{last_step.kind}:{last_step.name}"


def _tags(episode: Episode) -> list[str]:
    tags: list[str] = []
    for step in episode.steps:
        tags.append(step.kind)
    return sorted(set(tags))


def _labels(episode: Episode, signature: str, tags: list[str], contains_sensitive: bool) -> list[str]:
    labels = [f"status:{'success' if episode.success else 'failure'}", f"signature:{signature.replace(':', '-')}"]
    labels.extend(f"step:{tag}" for tag in tags)
    if contains_sensitive:
        labels.append("pii:possible")
    return sorted(set(labels))


def _contains_sensitive(episode: Episode) -> bool:
    fields = [
        episode.final_output,
        episode.episode_id,
        episode.agent_name,
        episode.model,
        episode.prompt_version,
        episode.metrics,
    ]
    for step in episode.steps:
        fields.extend([step.kind, step.name, step.payload])
    return any(contains_sensitive_value(value) for value in fields)


def scan_directory(root: str | Path) -> PackSummary:
    episodes: list[CaseSummary] = []
    for path in find_episode_files(root):
        episode = load_episode(path)
        signature = _failure_signature(episode)
        tags = _tags(episode)
        contains_sensitive = _contains_sensitive(episode)
        episodes.append(
            CaseSummary(
                source_path=str(path),
                episode_id=episode.episode_id,
                agent_name=episode.agent_name,
                model=episode.model,
                prompt_version=episode.prompt_version,
                success=episode.success,
                final_output=episode.final_output,
                step_count=len(episode.steps),
                signature=signature,
                tags=tags,
                labels=_labels(episode, signature, tags, contains_sensitive),
                metrics=dict(episode.metrics),
                steps=[
                    {
                        "kind": step.kind,
                        "name": step.name,
                        "payload": step.payload,
                    }
                    for step in episode.steps
                ],
                contains_sensitive=contains_sensitive,
            )
        )
    return PackSummary(episodes=episodes)
