from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .cluster import build_clusters
from .compare import compare_cluster_files
from .io import write_json
from .report import (
    load_clusters,
    markdown_compare_report,
    markdown_report,
    summarize_clusters,
    summarize_compare,
)


def _cmd_cluster(args: argparse.Namespace) -> int:
    payload = build_clusters(args.pack)
    write_json(args.output, payload)
    print(f"Wrote clusters to {args.output}")
    return 0


def _cmd_summarize(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    print(summarize_clusters(payload))
    return 0


def _cmd_markdown(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    Path(args.output).write_text(markdown_report(payload), encoding="utf-8")
    print(f"Wrote report to {args.output}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    payload = compare_cluster_files(args.baseline, args.candidate)
    write_json(args.output, payload)
    print(f"Wrote compare report to {args.output}")
    return 0


def _cmd_compare_summary(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    print(summarize_compare(payload))
    return 0


def _cmd_compare_markdown(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    Path(args.output).write_text(markdown_compare_report(payload), encoding="utf-8")
    print(f"Wrote compare markdown to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="failmap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cluster = subparsers.add_parser("cluster", help="cluster failures from a TracePack pack")
    cluster.add_argument("pack")
    cluster.add_argument("output")
    cluster.set_defaults(func=_cmd_cluster)

    summarize = subparsers.add_parser("summarize", help="summarize a clusters json file")
    summarize.add_argument("path")
    summarize.set_defaults(func=_cmd_summarize)

    markdown = subparsers.add_parser("markdown", help="render a markdown report from clusters json")
    markdown.add_argument("path")
    markdown.add_argument("output")
    markdown.set_defaults(func=_cmd_markdown)

    compare = subparsers.add_parser("compare", help="compare two cluster json files")
    compare.add_argument("baseline")
    compare.add_argument("candidate")
    compare.add_argument("output")
    compare.set_defaults(func=_cmd_compare)

    compare_summary = subparsers.add_parser("compare-summary", help="summarize a compare json file")
    compare_summary.add_argument("path")
    compare_summary.set_defaults(func=_cmd_compare_summary)

    compare_markdown = subparsers.add_parser("compare-markdown", help="render markdown from a compare json file")
    compare_markdown.add_argument("path")
    compare_markdown.add_argument("output")
    compare_markdown.set_defaults(func=_cmd_compare_markdown)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
