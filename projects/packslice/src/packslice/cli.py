from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .report import load_summary, markdown_splits, summarize_splits
from .splitter import split_pack


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def _print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON output")


def _cmd_split(args: argparse.Namespace) -> int:
    if args.success_only and args.failure_only:
        raise SystemExit("--success-only and --failure-only cannot be used together")
    summary = split_pack(
        args.pack,
        args.output,
        ratios=(args.train_ratio, args.eval_ratio, args.test_ratio),
        group_by=args.group_by,
        include_labels=tuple(args.include_label),
        success_mode="success-only" if args.success_only else "failure-only" if args.failure_only else "all",
        chronological=args.chronological,
        order_by=args.order_by,
    )
    if args.json:
        _print_json(summary)
        return 0
    print(f"Wrote split pack to {args.output}")
    print(summarize_splits(summary))
    return 0


def _split_balance_counts(payload: dict[str, object]) -> dict[str, int]:
    balance = payload.get("balance", {})
    if not isinstance(balance, dict):
        return {}
    case_counts = balance.get("case_counts", {})
    if not isinstance(case_counts, dict):
        return {}
    return {str(name): int(count) for name, count in case_counts.items()}


def _cmd_summarize(args: argparse.Namespace) -> int:
    payload = load_summary(args.path)
    if args.json:
        _print_json(payload)
        return 0
    print(summarize_splits(payload))
    balance = _split_balance_counts(payload)
    if balance:
        print("Split balance:")
        for split_name, count in balance.items():
            print(f"- {split_name}: {count}")
    return 0


def _cmd_markdown(args: argparse.Namespace) -> int:
    payload = load_summary(args.path)
    Path(args.output).write_text(markdown_splits(payload), encoding="utf-8")
    print(f"Wrote markdown report to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="packslice")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split = subparsers.add_parser("split", help="split a TracePack pack into balanced train/eval/test subsets")
    split.add_argument("pack")
    split.add_argument("output")
    split.add_argument("--group-by", default="signature", choices=["signature", "agent_name", "model"])
    split.add_argument("--order-by", default="episode_id", choices=["episode_id", "file", "source_path"])
    split.add_argument("--chronological", action="store_true", help="preserve ordered contiguous slices per group")
    split.add_argument("--include-label", action="append", default=[], help="only keep cases that include this label")
    split.add_argument("--success-only", action="store_true", help="only split successful cases")
    split.add_argument("--failure-only", action="store_true", help="only split failing cases")
    split.add_argument("--train-ratio", type=_positive_int, default=70)
    split.add_argument("--eval-ratio", type=_positive_int, default=15)
    split.add_argument("--test-ratio", type=_positive_int, default=15)
    _add_json_flag(split)
    split.set_defaults(func=_cmd_split)

    summarize = subparsers.add_parser("summarize", help="summarize an existing split output")
    summarize.add_argument("path")
    _add_json_flag(summarize)
    summarize.set_defaults(func=_cmd_summarize)

    markdown = subparsers.add_parser("markdown", help="render a markdown report for an existing split output")
    markdown.add_argument("path")
    markdown.add_argument("output")
    markdown.set_defaults(func=_cmd_markdown)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
