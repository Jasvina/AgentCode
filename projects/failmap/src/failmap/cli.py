from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .cluster import build_clusters
from .compare import compare_cluster_files
from .io import write_json
from .issues import build_issue_bundle, generate_issue_drafts, load_issue_manifest
from .report import (
    load_clusters,
    markdown_compare_report,
    markdown_report,
    markdown_trend_report,
    summarize_clusters,
    summarize_compare,
    summarize_trends,
)
from .trends import build_trend_report


def _print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON output")


def _cmd_cluster(args: argparse.Namespace) -> int:
    payload = build_clusters(args.pack)
    write_json(args.output, payload)
    if args.json:
        response = dict(payload)
        response["output"] = str(args.output)
        _print_json(response)
        return 0
    print(f"Wrote clusters to {args.output}")
    return 0


def _cmd_summarize(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    if args.json:
        _print_json(payload)
        return 0
    print(summarize_clusters(payload))
    return 0


def _cmd_markdown(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    Path(args.output).write_text(markdown_report(payload), encoding="utf-8")
    if args.json:
        _print_json(
            {
                "output": str(args.output),
                "cluster_count": int(payload.get("cluster_count", 0)),
                "case_count": int(payload.get("case_count", 0)),
                "format": "markdown",
            }
        )
        return 0
    print(f"Wrote report to {args.output}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    payload = compare_cluster_files(args.baseline, args.candidate)
    write_json(args.output, payload)
    if args.json:
        response = dict(payload)
        response["output"] = str(args.output)
        _print_json(response)
        return 0
    print(f"Wrote compare report to {args.output}")
    return 0


def _cmd_compare_summary(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    if args.json:
        _print_json(payload)
        return 0
    print(summarize_compare(payload))
    return 0


def _cmd_compare_markdown(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    Path(args.output).write_text(markdown_compare_report(payload), encoding="utf-8")
    if args.json:
        _print_json(
            {
                "output": str(args.output),
                "cluster_count": int(payload.get("cluster_count", 0)),
                "summary": dict(payload.get("summary", {})),
                "format": "markdown",
            }
        )
        return 0
    print(f"Wrote compare markdown to {args.output}")
    return 0


def _cmd_issue_drafts(args: argparse.Namespace) -> int:
    statuses = set(args.status) if args.status else None
    manifest = generate_issue_drafts(args.path, args.output_dir, include_statuses=statuses, rules_path=args.rules)
    if args.json:
        response = dict(manifest)
        response["output_dir"] = str(args.output_dir)
        _print_json(response)
        return 0
    print(f"Wrote {manifest['draft_count']} issue drafts to {args.output_dir}")
    return 0


def _cmd_issue_bundle(args: argparse.Namespace) -> int:
    bundle = build_issue_bundle(args.issues_path, args.output_dir)
    if args.json:
        response = dict(bundle)
        response["output_dir"] = str(args.output_dir)
        _print_json(response)
        return 0
    print(f"Wrote issue bundle with {bundle['draft_count']} drafts to {args.output_dir}")
    return 0


def _cmd_issue_bundle_summary(args: argparse.Namespace) -> int:
    bundle = load_issue_manifest(args.path)
    if args.json:
        _print_json(bundle)
        return 0
    draft_count = int(bundle.get("draft_count", 0))
    print(f"Drafts: {draft_count}")
    print("By priority:")
    for key, value in sorted(bundle.get("priority_counts", {}).items()):
        print(f"- {key}: {value}")
    print("By owner:")
    for key, value in sorted(bundle.get("owner_counts", {}).items()):
        print(f"- {key}: {value}")
    return 0


def _cmd_trend(args: argparse.Namespace) -> int:
    payload = build_trend_report(args.paths)
    write_json(args.output, payload)
    if args.json:
        response = dict(payload)
        response["output"] = str(args.output)
        _print_json(response)
        return 0
    print(f"Wrote trend report to {args.output}")
    return 0


def _cmd_trend_summary(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    if args.json:
        _print_json(payload)
        return 0
    print(summarize_trends(payload))
    return 0


def _cmd_trend_markdown(args: argparse.Namespace) -> int:
    payload = load_clusters(args.path)
    Path(args.output).write_text(markdown_trend_report(payload), encoding="utf-8")
    if args.json:
        _print_json(
            {
                "output": str(args.output),
                "snapshot_count": int(payload.get("snapshot_count", 0)),
                "signature_count": int(payload.get("signature_count", 0)),
                "format": "markdown",
            }
        )
        return 0
    print(f"Wrote trend markdown to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="failmap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cluster = subparsers.add_parser("cluster", help="cluster failures from a TracePack pack")
    cluster.add_argument("pack")
    cluster.add_argument("output")
    _add_json_flag(cluster)
    cluster.set_defaults(func=_cmd_cluster)

    summarize = subparsers.add_parser("summarize", help="summarize a clusters json file")
    summarize.add_argument("path")
    _add_json_flag(summarize)
    summarize.set_defaults(func=_cmd_summarize)

    markdown = subparsers.add_parser("markdown", help="render a markdown report from clusters json")
    markdown.add_argument("path")
    markdown.add_argument("output")
    _add_json_flag(markdown)
    markdown.set_defaults(func=_cmd_markdown)

    compare = subparsers.add_parser("compare", help="compare two cluster json files")
    compare.add_argument("baseline")
    compare.add_argument("candidate")
    compare.add_argument("output")
    _add_json_flag(compare)
    compare.set_defaults(func=_cmd_compare)

    compare_summary = subparsers.add_parser("compare-summary", help="summarize a compare json file")
    compare_summary.add_argument("path")
    _add_json_flag(compare_summary)
    compare_summary.set_defaults(func=_cmd_compare_summary)

    compare_markdown = subparsers.add_parser("compare-markdown", help="render markdown from a compare json file")
    compare_markdown.add_argument("path")
    compare_markdown.add_argument("output")
    _add_json_flag(compare_markdown)
    compare_markdown.set_defaults(func=_cmd_compare_markdown)

    issue_drafts = subparsers.add_parser("issue-drafts", help="generate issue-ready markdown drafts from a compare json file")
    issue_drafts.add_argument("path")
    issue_drafts.add_argument("output_dir")
    issue_drafts.add_argument("--rules", help="optional triage routing rules json file")
    issue_drafts.add_argument(
        "--status",
        action="append",
        choices=["new", "resolved", "growing", "shrinking", "unchanged"],
        help="limit generated drafts to selected statuses; can be passed multiple times",
    )
    _add_json_flag(issue_drafts)
    issue_drafts.set_defaults(func=_cmd_issue_drafts)

    issue_bundle = subparsers.add_parser("issue-bundle", help="group issue drafts into a batch triage bundle")
    issue_bundle.add_argument("issues_path")
    issue_bundle.add_argument("output_dir")
    _add_json_flag(issue_bundle)
    issue_bundle.set_defaults(func=_cmd_issue_bundle)

    issue_bundle_summary = subparsers.add_parser("issue-bundle-summary", help="summarize an issue bundle json file")
    issue_bundle_summary.add_argument("path")
    _add_json_flag(issue_bundle_summary)
    issue_bundle_summary.set_defaults(func=_cmd_issue_bundle_summary)

    trend = subparsers.add_parser("trend", help="build a trend report from multiple cluster snapshots")
    trend.add_argument("output")
    trend.add_argument("paths", nargs="+")
    _add_json_flag(trend)
    trend.set_defaults(func=_cmd_trend)

    trend_summary = subparsers.add_parser("trend-summary", help="summarize a trend json file")
    trend_summary.add_argument("path")
    _add_json_flag(trend_summary)
    trend_summary.set_defaults(func=_cmd_trend_summary)

    trend_markdown = subparsers.add_parser("trend-markdown", help="render markdown from a trend json file")
    trend_markdown.add_argument("path")
    trend_markdown.add_argument("output")
    _add_json_flag(trend_markdown)
    trend_markdown.set_defaults(func=_cmd_trend_markdown)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
