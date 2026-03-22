from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_json
from .routing import apply_routing_rules


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


def _frontmatter(
    cluster: dict[str, Any],
    priority: str,
    owner: str,
    labels: list[str],
    matched_rules: list[str] | None = None,
) -> str:
    label_lines = "\n".join(f"  - {label}" for label in labels)
    rule_lines = ""
    if matched_rules:
        rule_lines = "routing_rules:\n" + "\n".join(f"  - {rule}" for rule in matched_rules) + "\n"
    return (
        "---\n"
        f"title: \"{_title(cluster)}\"\n"
        f"priority: {priority}\n"
        f"suggested_owner: {owner}\n"
        f"{rule_lines}"
        "labels:\n"
        f"{label_lines}\n"
        "---\n\n"
    )


def _body(cluster: dict[str, Any], priority: str, owner: str, labels: list[str], matched_rules: list[str]) -> str:
    baseline_examples = ", ".join(cluster.get("baseline_examples", [])) or "none"
    candidate_examples = ", ".join(cluster.get("candidate_examples", [])) or "none"
    candidate_tags = ", ".join(cluster.get("candidate_tags", [])) or "none"
    candidate_agents = ", ".join(cluster.get("candidate_agents", [])) or "none"
    candidate_models = ", ".join(cluster.get("candidate_models", [])) or "none"
    matched = ", ".join(matched_rules) or "none"
    return (
        _frontmatter(cluster, priority, owner, labels, matched_rules)
        +
        f"# {_title(cluster)}\n\n"
        "## Triage metadata\n\n"
        f"- Priority: `{priority}`\n"
        f"- Suggested owner: `{owner}`\n"
        f"- Labels: `{', '.join(labels)}`\n\n"
        f"- Routing rules: `{matched}`\n\n"
        "## Why this matters\n\n"
        f"- Status: `{cluster['status']}`\n"
        f"- Signature: `{cluster['signature']}`\n"
        f"- Case delta: `{cluster['baseline_case_count']} -> {cluster['candidate_case_count']} ({cluster['delta']:+d})`\n\n"
        "## Candidate cluster context\n\n"
        f"- Agents: {candidate_agents}\n"
        f"- Models: {candidate_models}\n"
        f"- Tags: {candidate_tags}\n\n"
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
    rules_path: str | Path | None = None,
) -> dict[str, Any]:
    payload = load_json(compare_path)
    rules_payload = load_json(rules_path) if rules_path else None
    statuses = include_statuses or {"new", "growing", "resolved", "shrinking"}
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    drafts: list[dict[str, Any]] = []
    for index, cluster in enumerate(payload.get("clusters", []), start=1):
        status = str(cluster.get("status") or "unknown")
        if status not in statuses:
            continue
        fallback_priority = _priority(cluster)
        fallback_owner = _suggested_owner(cluster)
        fallback_labels = _labels(cluster, fallback_priority)
        routed = apply_routing_rules(
            cluster,
            rules_payload,
            fallback_owner=fallback_owner,
            fallback_priority=fallback_priority,
            fallback_labels=fallback_labels,
        )
        priority = str(routed["priority"])
        owner = str(routed["owner"])
        labels = [label for label in routed["labels"] if not str(label).startswith("priority:")]
        labels.append(f"priority:{priority}")
        labels = sorted(set(str(label) for label in labels))
        matched_rules = list(routed["matched_rules"])
        filename = f"{index:03d}-{_slug(status)}-{_slug(str(cluster.get('signature') or 'cluster'))}.md"
        issue_path = out_root / filename
        issue_path.write_text(_body(cluster, priority, owner, labels, matched_rules), encoding="utf-8")
        drafts.append(
            {
                "file": filename,
                "title": _title(cluster),
                "status": status,
                "signature": cluster.get("signature"),
                "priority": priority,
                "suggested_owner": owner,
                "labels": labels,
                "matched_rules": matched_rules,
            }
        )

    manifest = {
        "format": "failmap-issues-v1",
        "source_compare": str(compare_path),
        "source_rules": str(rules_path) if rules_path else None,
        "draft_count": len(drafts),
        "drafts": drafts,
    }
    (out_root / "manifest.json").write_text(
        __import__("json").dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_issue_manifest(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    manifest_path = source / "manifest.json" if source.is_dir() else source
    return load_json(manifest_path)


def _group_drafts(drafts: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for draft in drafts:
        value = str(draft.get(key) or "unknown")
        grouped.setdefault(value, []).append(draft)
    for value in grouped:
        grouped[value] = sorted(grouped[value], key=lambda item: (item["title"], item["file"]))
    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def _bundle_markdown(bundle: dict[str, Any]) -> str:
    lines = [
        "# FailMap Issue Bundle",
        "",
        f"- Drafts: {bundle['draft_count']}",
        f"- Priorities: {', '.join(bundle['priority_counts'].keys()) or 'none'}",
        f"- Owners: {', '.join(bundle['owner_counts'].keys()) or 'none'}",
        "",
        "## By priority",
        "",
    ]
    for priority, count in bundle["priority_counts"].items():
        lines.append(f"- {priority}: {count}")
    lines.extend(["", "## By owner", ""])
    for owner, count in bundle["owner_counts"].items():
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Drafts", ""])
    for draft in bundle["drafts"]:
        lines.append(
            f"- [{draft['title']}]({draft['file']}) — priority `{draft['priority']}`, owner `{draft['suggested_owner']}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_issue_bundle(issues_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    manifest = load_issue_manifest(issues_path)
    drafts = list(manifest.get("drafts", []))
    by_priority = _group_drafts(drafts, "priority")
    by_owner = _group_drafts(drafts, "suggested_owner")
    by_status = _group_drafts(drafts, "status")

    bundle = {
        "format": "failmap-issue-bundle-v1",
        "source_manifest": str(Path(issues_path)),
        "draft_count": len(drafts),
        "drafts": drafts,
        "priority_counts": {key: len(value) for key, value in by_priority.items()},
        "owner_counts": {key: len(value) for key, value in by_owner.items()},
        "status_counts": {key: len(value) for key, value in by_status.items()},
        "by_priority": by_priority,
        "by_owner": by_owner,
        "by_status": by_status,
    }

    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "bundle.json").write_text(
        __import__("json").dumps(bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_root / "SUMMARY.md").write_text(_bundle_markdown(bundle), encoding="utf-8")
    return bundle
