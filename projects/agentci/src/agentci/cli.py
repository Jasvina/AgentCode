from __future__ import annotations

import argparse
import json
import sys

from .compare import compare_episodes
from .flaky import analyze_flakiness
from .html_report import write_diff_html_report
from .regression import run_regression_check
from .replay import replay_episode
from .schema import Episode


def _print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def _episode_summary(episode: Episode) -> dict[str, object]:
    tool_calls = sum(1 for step in episode.steps if step.kind == "tool_call")
    model_calls = sum(1 for step in episode.steps if step.kind == "model_call")
    return {
        "episode_id": episode.episode_id,
        "agent_name": episode.agent_name,
        "model": episode.model,
        "prompt_version": episode.prompt_version,
        "seed": episode.seed,
        "steps": len(episode.steps),
        "success": episode.success,
        "tool_calls": tool_calls,
        "model_calls": model_calls,
        "metrics": dict(episode.metrics),
    }


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON output",
    )


def _cmd_summarize(args: argparse.Namespace) -> int:
    episode = Episode.load(args.path)
    summary = _episode_summary(episode)
    if args.json:
        _print_json(summary)
        return 0
    print(f"Episode: {episode.episode_id}")
    print(f"Agent: {episode.agent_name}")
    print(f"Model: {episode.model}")
    print(f"Prompt version: {episode.prompt_version}")
    print(f"Steps: {summary['steps']}")
    print(f"Success: {episode.success}")
    print(f"Tool calls: {summary['tool_calls']}")
    print(f"Model calls: {summary['model_calls']}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    episode = Episode.load(args.path)
    if args.json:
        _print_json({"ok": True, "episode_id": episode.episode_id})
        return 0
    print(f"OK: {episode.episode_id}")
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    episode = Episode.load(args.path)
    result = replay_episode(episode, strict=True)
    if args.json:
        _print_json(result.to_dict())
        return 1 if args.fail_on_mismatch and not result.matched else 0
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
    if args.json:
        _print_json(diff.to_dict())
        return 0
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
    baseline = Episode.load(args.baseline)
    candidate = Episode.load(args.candidate)
    result = run_regression_check(
        baseline,
        candidate,
        ignore_diff_prefixes=tuple(args.ignore_diff_prefix),
        check_candidate_replay=not args.skip_replay,
        baseline_path=str(args.baseline),
        candidate_path=str(args.candidate),
    )
    if args.json:
        _print_json(result.to_dict())
        return 0 if result.passed else 1
    if not result.passed:
        print(result.failure_message())
        return 1
    print("AgentCI regression assertion passed")
    return 0


def _cmd_detect_flaky(args: argparse.Namespace) -> int:
    episodes = [Episode.load(path) for path in args.paths]
    report = analyze_flakiness(episodes)
    if args.json:
        _print_json(report.to_dict())
        return 0
    print(f"Episodes analyzed: {report.episode_count}")
    print(f"Unstable fields: {len(report.unstable_fields)}")
    if report.is_stable:
        print("No unstable fields detected")
        return 0
    for field in report.unstable_fields:
        occurrences = ", ".join(f"{value} x{count}" for value, count in field.occurrences.items())
        print(f"- {field.name}: {occurrences}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentci")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser("summarize", help="show a compact episode summary")
    summarize.add_argument("path")
    _add_json_flag(summarize)
    summarize.set_defaults(func=_cmd_summarize)

    validate = subparsers.add_parser("validate", help="validate that an episode can be loaded")
    validate.add_argument("path")
    _add_json_flag(validate)
    validate.set_defaults(func=_cmd_validate)

    replay = subparsers.add_parser("replay", help="replay an episode from frozen outputs")
    replay.add_argument("path")
    replay.add_argument("--fail-on-mismatch", action="store_true")
    _add_json_flag(replay)
    replay.set_defaults(func=_cmd_replay)

    diff = subparsers.add_parser("diff", help="compare two episodes")
    diff.add_argument("baseline")
    diff.add_argument("candidate")
    _add_json_flag(diff)
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
    _add_json_flag(assert_regression)
    assert_regression.set_defaults(func=_cmd_assert_regression)

    detect_flaky = subparsers.add_parser(
        "detect-flaky",
        help="analyze multiple episodes and report unstable fields across runs",
    )
    detect_flaky.add_argument("paths", nargs="+")
    _add_json_flag(detect_flaky)
    detect_flaky.set_defaults(func=_cmd_detect_flaky)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
