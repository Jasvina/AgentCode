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
        f"Order by: {payload.get('order_by', 'episode_id')}",
        f"Chronological: {payload.get('chronological', False)}",
        "Splits:",
    ]
    for split in payload.get("splits", []):
        lines.append(f"- {split['name']}: {split['case_count']} cases")
    return "\n".join(lines)


def markdown_splits(payload: dict[str, Any]) -> str:
    lines = [
        "# PackSlice Report",
        "",
        f"- Total cases: {payload['total_cases']}",
        f"- Group by: `{payload['group_by']}`",
        f"- Order by: `{payload.get('order_by', 'episode_id')}`",
        f"- Chronological: `{payload.get('chronological', False)}`",
        "",
    ]
    filters = payload.get("filters", {})
    lines.append("## Filters")
    lines.append("")
    lines.append(f"- Success mode: `{filters.get('success_mode', 'all')}`")
    labels = filters.get("include_labels", [])
    lines.append(f"- Include labels: `{', '.join(labels) if labels else 'none'}`")
    lines.append("")
    for split in payload.get("splits", []):
        lines.append(f"## {split['name']}")
        lines.append("")
        lines.append(f"- Cases: {split['case_count']}")
        signatures = split.get("signatures", [])
        if signatures:
            top = ", ".join(f"{item['signature']} ({item['count']})" for item in signatures[:5])
            lines.append(f"- Signatures: {top}")
        else:
            lines.append("- Signatures: none")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
