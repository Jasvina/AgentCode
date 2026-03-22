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


def _priority(cluster: dict[str, Any]) -> str:
    status = str(cluster.get("status") or "unknown")
    baseline_count = int(cluster.get("baseline_case_count", 0))
    candidate_count = int(cluster.get("candidate_case_count", 0))
    delta = int(cluster.get("delta", 0))
    if status in {"new", "growing"} and (candidate_count >= 5 or delta >= 3):
        return "P0"
    if status in {"new", "growing"} and (candidate_count >= 2 or delta >= 1):
        return "P1"
    if status in {"resolved", "shrinking"}:
        return "P2"
    if baseline_count == candidate_count:
        return "P3"
    return "P2"


def _suggested_owner(cluster: dict[str, Any]) -> str:
    signature = str(cluster.get("signature") or "")
    if "tool_call" in signature:
        return "tooling"
    if "model_call" in signature:
        return "agent-runtime"
    if "assertion" in signature or "note" in signature:
        return "evals"
    return "agent-platform"


def _labels(cluster: dict[str, Any], priority: str) -> list[str]:
    status = str(cluster.get("status") or "unknown")
    signature = str(cluster.get("signature") or "unknown")
    signature_label = f"signature:{_slug(signature)[:48]}"
    return ["failmap", f"status:{status}", f"priority:{priority}", signature_label]


def _frontmatter(cluster: dict[str, Any], priority: str, owner: str, labels: list[str]) -> str:
    label_lines = "\n".join(f"  - {label}" for label in labels)
    return (
        "---\n"
        f"title: \"{_title(cluster)}\"\n"
        f"priority: {priority}\n"
        f"suggested_owner: {owner}\n"
        "labels:\n"
        f"{label_lines}\n"
        "---\n\n"
    )


def _body(cluster: dict[str, Any]) -> str:
    baseline_examples = ", ".join(cluster.get("baseline_examples", [])) or "none"
    candidate_examples = ", ".join(cluster.get("candidate_examples", [])) or "none"
    priority = _priority(cluster)
    owner = _suggested_owner(cluster)
    labels = _labels(cluster, priority)
    return (
        _frontmatter(cluster, priority, owner, labels)
        +
        f"# {_title(cluster)}\n\n"
        "## Triage metadata\n\n"
        f"- Priority: `{priority}`\n"
        f"- Suggested owner: `{owner}`\n"
        f"- Labels: `{', '.join(labels)}`\n\n"
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
        priority = _priority(cluster)
        owner = _suggested_owner(cluster)
        labels = _labels(cluster, priority)
        filename = f"{index:03d}-{_slug(status)}-{_slug(str(cluster.get('signature') or 'cluster'))}.md"
        issue_path = out_root / filename
        issue_path.write_text(_body(cluster), encoding="utf-8")
        drafts.append(
            {
                "file": filename,
                "title": _title(cluster),
                "status": status,
                "signature": cluster.get("signature"),
                "priority": priority,
                "suggested_owner": owner,
                "labels": labels,
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
