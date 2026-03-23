from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .builder import build_pack, export_pack_chat_jsonl, export_pack_jsonl
from .scanner import scan_directory


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def _print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON output")


def _inspect_manifest(path: str | Path) -> dict[str, object]:
    manifest = json.loads((Path(path) / "manifest.json").read_text(encoding="utf-8"))
    signatures: dict[str, int] = {}
    labels: dict[str, int] = {}
    for case in manifest.get("cases", []):
        signature = case.get("signature", "unknown")
        signatures[signature] = signatures.get(signature, 0) + 1
        for label in case.get("labels", []):
            labels[label] = labels.get(label, 0) + 1
    return {
        "format": manifest["format"],
        "case_count": manifest["case_count"],
        "only_failures": manifest["only_failures"],
        "redacted": manifest.get("redacted", False),
        "max_per_signature": manifest.get("max_per_signature"),
        "signatures": dict(sorted(signatures.items())),
        "labels": dict(sorted(labels.items())),
        "manifest": manifest,
    }


def _cmd_scan(args: argparse.Namespace) -> int:
    summary = scan_directory(args.path)
    payload = summary.to_dict()
    if args.json:
        _print_json(payload)
        return 0
    print(f"Episodes: {len(summary.episodes)}")
    print(f"Successes: {summary.successes}")
    print(f"Failures: {summary.failures}")
    print(f"Sensitive: {payload['sensitive']}")
    if payload["kind_counts"]:
        kinds = ", ".join(f"{key}={value}" for key, value in payload["kind_counts"].items())
        print(f"Kinds: {kinds}")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    summary = build_pack(
        args.source,
        args.output,
        only_failures=args.only_failures,
        redact=args.redact,
        max_per_signature=args.max_per_signature,
    )
    if args.json:
        _print_json(
            {
                "output": str(args.output),
                "only_failures": args.only_failures,
                "redacted": args.redact,
                "max_per_signature": args.max_per_signature,
                **summary.to_dict(),
            }
        )
        return 0
    print(f"Built pack with {len(summary.episodes)} cases at {args.output}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    payload = _inspect_manifest(args.path)
    if args.json:
        _print_json(payload)
        return 0
    print(f"Format: {payload['format']}")
    print(f"Cases: {payload['case_count']}")
    print(f"Only failures: {payload['only_failures']}")
    print(f"Redacted: {payload['redacted']}")
    print(f"Max per signature: {payload['max_per_signature']}")
    if payload["signatures"]:
        summary = ", ".join(f"{key}={value}" for key, value in payload["signatures"].items())
        print(f"Signatures: {summary}")
    if payload["labels"]:
        top = ", ".join(f"{key}={value}" for key, value in list(payload["labels"].items())[:8])
        print(f"Labels: {top}")
    return 0


def _cmd_export_jsonl(args: argparse.Namespace) -> int:
    count = export_pack_jsonl(args.pack, args.output)
    if args.json:
        _print_json({"output": str(args.output), "count": count, "format": "jsonl"})
        return 0
    print(f"Exported {count} cases to {args.output}")
    return 0


def _cmd_export_chat(args: argparse.Namespace) -> int:
    count = export_pack_chat_jsonl(args.pack, args.output, success_only=args.success_only)
    if args.json:
        _print_json(
            {
                "output": str(args.output),
                "count": count,
                "format": "chat-jsonl",
                "success_only": args.success_only,
            }
        )
        return 0
    print(f"Exported {count} chat rows to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracepack")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="summarize a folder of episode JSON files")
    scan.add_argument("path")
    _add_json_flag(scan)
    scan.set_defaults(func=_cmd_scan)

    build = subparsers.add_parser("build", help="build a reusable trace pack")
    build.add_argument("source")
    build.add_argument("output")
    build.add_argument("--only-failures", action="store_true")
    build.add_argument("--redact", action="store_true", help="redact simple sensitive patterns in final outputs")
    build.add_argument(
        "--max-per-signature",
        type=_positive_int,
        help="keep at most N cases per failure signature when building a pack",
    )
    _add_json_flag(build)
    build.set_defaults(func=_cmd_build)

    inspect_cmd = subparsers.add_parser("inspect", help="inspect an existing trace pack")
    inspect_cmd.add_argument("path")
    _add_json_flag(inspect_cmd)
    inspect_cmd.set_defaults(func=_cmd_inspect)

    export_jsonl = subparsers.add_parser("export-jsonl", help="export a pack manifest to jsonl")
    export_jsonl.add_argument("pack")
    export_jsonl.add_argument("output")
    _add_json_flag(export_jsonl)
    export_jsonl.set_defaults(func=_cmd_export_jsonl)

    export_chat = subparsers.add_parser(
        "export-chat",
        help="export a pack as chat-style jsonl for fine-tuning or eval workflows",
    )
    export_chat.add_argument("pack")
    export_chat.add_argument("output")
    export_chat.add_argument("--success-only", action="store_true", help="only export successful cases")
    _add_json_flag(export_chat)
    export_chat.set_defaults(func=_cmd_export_chat)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
