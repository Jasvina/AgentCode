from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .regression import (
    RegressionResult,
    assert_episode_regression,
    assert_episode_regression_from_paths,
    run_regression_check,
)
from .schema import Episode


@dataclass
class EpisodeRegressionFixture:
    default_ignore_diff_prefixes: tuple[str, ...] = ()

    def check(
        self,
        baseline: Episode,
        candidate: Episode,
        *,
        ignore_diff_prefixes: tuple[str, ...] = (),
        check_candidate_replay: bool = True,
        baseline_path: str | None = None,
        candidate_path: str | None = None,
    ) -> RegressionResult:
        prefixes = ignore_diff_prefixes or self.default_ignore_diff_prefixes
        return run_regression_check(
            baseline,
            candidate,
            ignore_diff_prefixes=prefixes,
            check_candidate_replay=check_candidate_replay,
            baseline_path=baseline_path,
            candidate_path=candidate_path,
        )

    def assert_match(
        self,
        baseline: Episode,
        candidate: Episode,
        *,
        ignore_diff_prefixes: tuple[str, ...] = (),
        check_candidate_replay: bool = True,
        baseline_path: str | None = None,
        candidate_path: str | None = None,
    ) -> RegressionResult:
        prefixes = ignore_diff_prefixes or self.default_ignore_diff_prefixes
        return assert_episode_regression(
            baseline,
            candidate,
            ignore_diff_prefixes=prefixes,
            check_candidate_replay=check_candidate_replay,
            baseline_path=baseline_path,
            candidate_path=candidate_path,
        )

    def assert_match_files(
        self,
        baseline_path: str | Path,
        candidate_path: str | Path,
        *,
        ignore_diff_prefixes: tuple[str, ...] = (),
        check_candidate_replay: bool = True,
    ) -> RegressionResult:
        prefixes = ignore_diff_prefixes or self.default_ignore_diff_prefixes
        return assert_episode_regression_from_paths(
            baseline_path,
            candidate_path,
            ignore_diff_prefixes=prefixes,
            check_candidate_replay=check_candidate_replay,
        )


def pytest_configure(config) -> None:  # pragma: no cover - exercised by pytest
    config.addinivalue_line("markers", "agentci: mark tests using AgentCI regression helpers")


def pytest_report_header(config) -> str:  # pragma: no cover - exercised by pytest
    return "agentci: replay-first regression helpers enabled"


def pytest_addoption(parser) -> None:  # pragma: no cover - exercised by pytest
    group = parser.getgroup("agentci")
    group.addoption(
        "--agentci-ignore-diff",
        action="append",
        default=[],
        help="diff item prefixes to ignore in AgentCI regression assertions",
    )


def _fixture(request) -> EpisodeRegressionFixture:
    raw = request.config.getoption("--agentci-ignore-diff") or []
    return EpisodeRegressionFixture(default_ignore_diff_prefixes=tuple(raw))


try:  # pragma: no cover - import only when pytest is available
    import pytest

    @pytest.fixture
    def episode_regression(request) -> EpisodeRegressionFixture:
        return _fixture(request)

except ModuleNotFoundError:  # pragma: no cover
    pass
