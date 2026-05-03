from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def load_summary(path: str | Path) -> dict[str, Any]:
    summary_path = Path(path)
    if summary_path.is_dir():
        summary_path = summary_path / "summary.json"
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _split_balance_note(payload: dict[str, Any]) -> str | None:
    balance = payload.get("balance", {})
    if not balance:
        return None
    if balance.get("status") == "even":
        return "Split balance looks even across train, eval, and test."
    if balance.get("status") == "empty":
        empty = ", ".join(balance.get("empty_splits", [])) or "unknown"
        return f"Some splits are empty: {empty}."
    return "Split balance is uneven; inspect the counts below for skew or leakage risk."


def summarize_splits(payload: dict[str, Any]) -> str:
    balance_note = _split_balance_note(payload)
    lines = [
        f"Total cases: {payload['total_cases']}",
        f"Group by: {payload['group_by']}",
        f"Order by: {payload.get('order_by', 'episode_id')}",
        f"Chronological: {payload.get('chronological', False)}",
        "Splits:",
    ]
    for split in payload.get("splits", []):
        lines.append(f"- {split['name']}: {split['case_count']} cases")
    if balance_note:
        lines.append(f"Balance note: {balance_note}")
    balance = payload.get("balance", {})
    if balance.get("case_counts"):
        lines.append("Split balance:")
        for name, count in balance["case_counts"].items():
            lines.append(f"- {name}: {count}")
    return "\n".join(lines)


def markdown_splits(payload: dict[str, Any]) -> str:
    balance_note = _split_balance_note(payload)
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
    if balance_note:
        lines.append(f"- Balance note: {balance_note}")
    lines.append("")
    for split in payload.get("splits", []):
        lines.append(f"## {split['name']}")
        lines.append("")
        lines.append(f"- Cases: {split['case_count']}")
        groups = split.get("groups", [])
        if groups:
            top = ", ".join(f"{item['name']} ({item['count']})" for item in groups[:5])
            lines.append(f"- Groups: {top}")
        else:
            lines.append("- Groups: none")
        signatures = split.get("signatures", [])
        if signatures:
            top = ", ".join(f"{item['signature']} ({item['count']})" for item in signatures[:5])
            lines.append(f"- Signatures: {top}")
        else:
            lines.append("- Signatures: none")
        lines.append("")
    if balance_note:
        lines.append("## Balance")
        lines.append("")
        lines.append(f"- Note: {balance_note}")
    return "\n".join(lines).rstrip() + "\n"
