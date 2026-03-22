from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_json


def _slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif char in {"-", "_", " ", ":"}:
            chars.append("-")
    return "".join(chars).strip("-") or "issue"


def _title(cluster: dict[str, Any]) -> str:
    status = str(cluster.get("status") or "cluster")
    signature = str(cluster.get("signature") or "unknown")
    return f"[FailMap] {status}: {signature}"


def _body(cluster: dict[str, Any]) -> str:
    baseline_examples = ", ".join(cluster.get("baseline_examples", [])) or "none"
    candidate_examples = ", ".join(cluster.get("candidate_examples", [])) or "none"
    return (
        f"# {_title(cluster)}\n\n"
        "## Why this matters\n\n"
        f"- Status: `{cluster['status']}`\n"
        f"- Signature: `{cluster['signature']}`\n"
        f"- Case delta: `{cluster['baseline_case_count']} -> {cluster['candidate_case_count']} ({cluster['delta']:+d})`\n\n"
        "## Representative examples\n\n"
        f"- Baseline: {baseline_examples}\n"
        f"- Candidate: {candidate_examples}\n\n"
        "## Suggested next steps\n\n"
        "- Reproduce one representative failure locally\n"
        "- Check recent prompt, model, or tool changes touching this path\n"
        "- Add a targeted regression case to AgentCI / TracePack\n"
        "- Decide whether this needs an immediate fix or backlog prioritization\n"
    )


def generate_issue_drafts(
    compare_path: str | Path,
    output_dir: str | Path,
    include_statuses: set[str] | None = None,
) -> dict[str, Any]:
    payload = load_json(compare_path)
    statuses = include_statuses or {"new", "growing", "resolved", "shrinking"}
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    drafts: list[dict[str, Any]] = []
    for index, cluster in enumerate(payload.get("clusters", []), start=1):
        status = str(cluster.get("status") or "unknown")
        if status not in statuses:
            continue
        filename = f"{index:03d}-{_slug(status)}-{_slug(str(cluster.get('signature') or 'cluster'))}.md"
        issue_path = out_root / filename
        issue_path.write_text(_body(cluster), encoding="utf-8")
        drafts.append(
            {
                "file": filename,
                "title": _title(cluster),
                "status": status,
                "signature": cluster.get("signature"),
            }
        )

    manifest = {
        "format": "failmap-issues-v1",
        "source_compare": str(compare_path),
        "draft_count": len(drafts),
        "drafts": drafts,
    }
    (out_root / "manifest.json").write_text(
        __import__("json").dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
