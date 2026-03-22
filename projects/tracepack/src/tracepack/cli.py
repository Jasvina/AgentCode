from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .builder import build_pack
from .scanner import scan_directory


def _cmd_scan(args: argparse.Namespace) -> int:
    summary = scan_directory(args.path)
    kind_counts: dict[str, int] = {}
    for episode in summary.episodes:
        for tag in episode.tags:
            kind_counts[tag] = kind_counts.get(tag, 0) + 1
    print(f"Episodes: {len(summary.episodes)}")
    print(f"Successes: {summary.successes}")
    print(f"Failures: {summary.failures}")
    if kind_counts:
        kinds = ", ".join(f"{key}={value}" for key, value in sorted(kind_counts.items()))
        print(f"Kinds: {kinds}")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    summary = build_pack(args.source, args.output, only_failures=args.only_failures)
    print(f"Built pack with {len(summary.episodes)} cases at {args.output}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    manifest = json.loads((Path(args.path) / "manifest.json").read_text(encoding="utf-8"))
    print(f"Format: {manifest['format']}")
    print(f"Cases: {manifest['case_count']}")
    print(f"Only failures: {manifest['only_failures']}")
    signatures: dict[str, int] = {}
    for case in manifest.get("cases", []):
        signature = case.get("signature", "unknown")
        signatures[signature] = signatures.get(signature, 0) + 1
    if signatures:
        summary = ", ".join(f"{key}={value}" for key, value in sorted(signatures.items()))
        print(f"Signatures: {summary}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracepack")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="summarize a folder of episode JSON files")
    scan.add_argument("path")
    scan.set_defaults(func=_cmd_scan)

    build = subparsers.add_parser("build", help="build a reusable trace pack")
    build.add_argument("source")
    build.add_argument("output")
    build.add_argument("--only-failures", action="store_true")
    build.set_defaults(func=_cmd_build)

    inspect_cmd = subparsers.add_parser("inspect", help="inspect an existing trace pack")
    inspect_cmd.add_argument("path")
    inspect_cmd.set_defaults(func=_cmd_inspect)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
