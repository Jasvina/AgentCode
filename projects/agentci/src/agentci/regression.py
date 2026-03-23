from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .compare import compare_episodes
from .replay import replay_episode
from .schema import Episode


@dataclass
class RegressionResult:
    passed: bool
    baseline_path: str | None = None
    candidate_path: str | None = None
    diff_items: list[str] = field(default_factory=list)
    replay_mismatches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "baseline_path": self.baseline_path,
            "candidate_path": self.candidate_path,
            "diff_items": list(self.diff_items),
            "replay_mismatches": list(self.replay_mismatches),
        }

    def failure_message(self) -> str:
        lines = ["AgentCI regression check failed"]
        if self.baseline_path or self.candidate_path:
            lines.append(f"- baseline: {self.baseline_path or '<episode>'}")
            lines.append(f"- candidate: {self.candidate_path or '<episode>'}")
        if self.diff_items:
            lines.append("- diff:")
            lines.extend(f"  - {item}" for item in self.diff_items)
        if self.replay_mismatches:
            lines.append("- replay mismatches:")
            lines.extend(f"  - {item}" for item in self.replay_mismatches)
        return "\n".join(lines)


class RegressionAssertionError(AssertionError):
    pass


def _keep_item(item: str, ignore_prefixes: tuple[str, ...]) -> bool:
    return not any(item.startswith(prefix) for prefix in ignore_prefixes)


def run_regression_check(
    baseline: Episode,
    candidate: Episode,
    *,
    ignore_diff_prefixes: tuple[str, ...] = (),
    check_candidate_replay: bool = True,
    baseline_path: str | None = None,
    candidate_path: str | None = None,
) -> RegressionResult:
    diff = compare_episodes(baseline, candidate)
    kept_items = [item for item in diff.items if _keep_item(item, ignore_diff_prefixes)]
    replay_mismatches: list[str] = []
    if check_candidate_replay:
        replay = replay_episode(candidate, strict=True)
        replay_mismatches = replay.mismatches
    passed = not kept_items and not replay_mismatches
    return RegressionResult(
        passed=passed,
        baseline_path=baseline_path,
        candidate_path=candidate_path,
        diff_items=kept_items,
        replay_mismatches=replay_mismatches,
    )


def assert_episode_regression(
    baseline: Episode,
    candidate: Episode,
    *,
    ignore_diff_prefixes: tuple[str, ...] = (),
    check_candidate_replay: bool = True,
    baseline_path: str | None = None,
    candidate_path: str | None = None,
) -> RegressionResult:
    result = run_regression_check(
        baseline,
        candidate,
        ignore_diff_prefixes=ignore_diff_prefixes,
        check_candidate_replay=check_candidate_replay,
        baseline_path=baseline_path,
        candidate_path=candidate_path,
    )
    if not result.passed:
        raise RegressionAssertionError(result.failure_message())
    return result


def assert_episode_regression_from_paths(
    baseline_path: str | Path,
    candidate_path: str | Path,
    *,
    ignore_diff_prefixes: tuple[str, ...] = (),
    check_candidate_replay: bool = True,
) -> RegressionResult:
    left = Episode.load(baseline_path)
    right = Episode.load(candidate_path)
    return assert_episode_regression(
        left,
        right,
        ignore_diff_prefixes=ignore_diff_prefixes,
        check_candidate_replay=check_candidate_replay,
        baseline_path=str(baseline_path),
        candidate_path=str(candidate_path),
    )
