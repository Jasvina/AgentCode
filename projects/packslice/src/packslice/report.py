from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def load_summary(path: str | Path) -> dict[str, Any]:
    summary_path = Path(path)
    if summary_path.is_dir():
        summary_path = summary_path / "summary.json"
    return json.loads(summary_path.read_text(encoding="utf-8"))


def summarize_splits(payload: dict[str, Any]) -> str:
    lines = [
        f"Total cases: {payload['total_cases']}",
        f"Group by: {payload['group_by']}",
        "Splits:",
    ]
    for split in payload.get("splits", []):
        lines.append(f"- {split['name']}: {split['case_count']} cases")
    return "\n".join(lines)
