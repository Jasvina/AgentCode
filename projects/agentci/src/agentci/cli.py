from __future__ import annotations

import argparse
import sys

from .compare import compare_episodes
from .html_report import write_diff_html_report
from .regression import RegressionAssertionError, assert_episode_regression_from_paths
from .replay import replay_episode
from .schema import Episode


def _cmd_summarize(args: argparse.Namespace) -> int:
    episode = Episode.load(args.path)
    tool_calls = sum(1 for step in episode.steps if step.kind == "tool_call")
    model_calls = sum(1 for step in episode.steps if step.kind == "model_call")
    print(f"Episode: {episode.episode_id}")
    print(f"Agent: {episode.agent_name}")
    print(f"Model: {episode.model}")
    print(f"Prompt version: {episode.prompt_version}")
    print(f"Steps: {len(episode.steps)}")
    print(f"Success: {episode.success}")
    print(f"Tool calls: {tool_calls}")
    print(f"Model calls: {model_calls}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    episode = Episode.load(args.path)
    print(f"OK: {episode.episode_id}")
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    episode = Episode.load(args.path)
    result = replay_episode(episode, strict=True)
    if result.matched:
        print("Replay succeeded")
        return 0
    print("Replay failed")
    for mismatch in result.mismatches:
        print(f"- {mismatch}")
    return 1 if args.fail_on_mismatch else 0


def _cmd_diff(args: argparse.Namespace) -> int:
    baseline = Episode.load(args.baseline)
    candidate = Episode.load(args.candidate)
    diff = compare_episodes(baseline, candidate)
    if not diff.changed:
        print("No differences")
        return 0
    print("Differences")
    for item in diff.items:
        print(f"- {item}")
    return 0


def _cmd_diff_html(args: argparse.Namespace) -> int:
    baseline = Episode.load(args.baseline)
    candidate = Episode.load(args.candidate)
    write_diff_html_report(baseline, candidate, args.output)
    print(f"Wrote HTML diff report to {args.output}")
    return 0


def _cmd_assert_regression(args: argparse.Namespace) -> int:
    try:
        assert_episode_regression_from_paths(
            args.baseline,
            args.candidate,
            ignore_diff_prefixes=tuple(args.ignore_diff_prefix),
            check_candidate_replay=not args.skip_replay,
        )
    except RegressionAssertionError as exc:
        print(str(exc))
        return 1
    print("AgentCI regression assertion passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentci")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser("summarize", help="show a compact episode summary")
    summarize.add_argument("path")
    summarize.set_defaults(func=_cmd_summarize)

    validate = subparsers.add_parser("validate", help="validate that an episode can be loaded")
    validate.add_argument("path")
    validate.set_defaults(func=_cmd_validate)

    replay = subparsers.add_parser("replay", help="replay an episode from frozen outputs")
    replay.add_argument("path")
    replay.add_argument("--fail-on-mismatch", action="store_true")
    replay.set_defaults(func=_cmd_replay)

    diff = subparsers.add_parser("diff", help="compare two episodes")
    diff.add_argument("baseline")
    diff.add_argument("candidate")
    diff.set_defaults(func=_cmd_diff)

    diff_html = subparsers.add_parser("diff-html", help="render an HTML diff report for two episodes")
    diff_html.add_argument("baseline")
    diff_html.add_argument("candidate")
    diff_html.add_argument("output")
    diff_html.set_defaults(func=_cmd_diff_html)

    assert_regression = subparsers.add_parser(
        "assert-regression",
        help="fail if a candidate episode regresses against a baseline episode",
    )
    assert_regression.add_argument("baseline")
    assert_regression.add_argument("candidate")
    assert_regression.add_argument(
        "--ignore-diff-prefix",
        action="append",
        default=[],
        help="ignore diff items whose text starts with this prefix; can be passed multiple times",
    )
    assert_regression.add_argument(
        "--skip-replay",
        action="store_true",
        help="skip replay validation for the candidate episode",
    )
    assert_regression.set_defaults(func=_cmd_assert_regression)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
