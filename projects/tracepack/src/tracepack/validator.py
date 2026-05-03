from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REQUIRED_CASE_FIELDS = (
    "episode_id",
    "agent_name",
    "model",
    "prompt_version",
    "success",
    "signature",
    "tags",
    "labels",
    "step_count",
    "metrics",
    "steps",
    "final_output",
    "source_path",
    "file",
)


def validate_pack(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    manifest_path = root / "manifest.json"
    errors: list[str] = []
    manifest: dict[str, Any] = {}

    if not manifest_path.exists():
        return {
            "valid": False,
            "errors": [f"missing manifest: {manifest_path}"],
            "format": "unknown",
            "case_count": 0,
            "missing_case_files": [],
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "valid": False,
            "errors": [f"invalid manifest json: {exc}"],
            "format": "unknown",
            "case_count": 0,
            "missing_case_files": [],
        }

    if manifest.get("format") != "tracepack-v1":
        errors.append(f"unsupported format: {manifest.get('format')!r}")

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        cases = []

    case_count = manifest.get("case_count")
    if not isinstance(case_count, int):
        errors.append("case_count must be an integer")
    elif case_count != len(cases):
        errors.append(f"case_count mismatch: manifest says {case_count}, cases has {len(cases)}")

    missing_case_files: list[str] = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"case {index} is not an object")
            continue
        for field in _REQUIRED_CASE_FIELDS:
            if field not in case:
                errors.append(f"case {index} missing field: {field}")
        case_file = case.get("file")
        if not isinstance(case_file, str) or not case_file:
            errors.append(f"case {index} has invalid file field")
            continue
        target = root / case_file
        if not target.exists():
            missing_case_files.append(case_file)
        else:
            try:
                json.loads(target.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"case file {case_file} is not valid json: {exc}")
        labels = case.get("labels")
        tags = case.get("tags")
        steps = case.get("steps")
        metrics = case.get("metrics")
        if not isinstance(labels, list):
            errors.append(f"case {index} labels must be a list")
        if not isinstance(tags, list):
            errors.append(f"case {index} tags must be a list")
        if not isinstance(steps, list):
            errors.append(f"case {index} steps must be a list")
        if not isinstance(metrics, dict):
            errors.append(f"case {index} metrics must be an object")
        step_count = case.get("step_count")
        if isinstance(step_count, int) and isinstance(steps, list) and step_count != len(steps):
            errors.append(f"case {index} step_count mismatch: {step_count} != {len(steps)}")

    for case_file in missing_case_files:
        errors.append(f"missing case file: {case_file}")

    return {
        "valid": not errors,
        "errors": errors,
        "format": manifest.get("format", "unknown"),
        "case_count": len(cases),
        "missing_case_files": missing_case_files,
    }
