from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_clusters(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_clusters(payload: dict[str, Any]) -> str:
    lines = [
        f"Clusters: {payload['cluster_count']}",
        f"Cases: {payload['case_count']}",
        "Top clusters:",
    ]
    for cluster in payload.get("clusters", [])[:5]:
        lines.append(f"- {cluster['signature']} ({cluster['case_count']} cases)")
    return "\n".join(lines)


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# FailMap Report",
        "",
        f"- Source format: `{payload['source_format']}`",
        f"- Clusters: {payload['cluster_count']}",
        f"- Cases: {payload['case_count']}",
        "",
    ]
    for cluster in payload.get("clusters", []):
        lines.append(f"## {cluster['signature']}")
        lines.append("")
        lines.append(f"- Cases: {cluster['case_count']}")
        lines.append(f"- Failures: {cluster['failures']}")
        lines.append(f"- Successes: {cluster['successes']}")
        top_agents = ", ".join(item['name'] for item in cluster.get('agents', [])[:3]) or "unknown"
        top_models = ", ".join(item['name'] for item in cluster.get('models', [])[:3]) or "unknown"
        lines.append(f"- Agents: {top_agents}")
        lines.append(f"- Models: {top_models}")
        example_ids = ", ".join(cluster.get("example_episode_ids", [])) or "none"
        lines.append(f"- Example episodes: {example_ids}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def summarize_compare(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"Compared clusters: {payload['cluster_count']}",
        f"Cases: {payload['baseline_case_count']} -> {payload['candidate_case_count']}",
        "Changes:",
        f"- new: {summary['new']}",
        f"- resolved: {summary['resolved']}",
        f"- growing: {summary['growing']}",
        f"- shrinking: {summary['shrinking']}",
        f"- unchanged: {summary['unchanged']}",
    ]
    top_changed = [cluster for cluster in payload.get("clusters", []) if cluster["status"] != "unchanged"][:5]
    if top_changed:
        lines.append("Top cluster deltas:")
        for cluster in top_changed:
            delta = cluster["delta"]
            lines.append(f"- {cluster['signature']} ({delta:+d}) [{cluster['status']}]")
    return "\n".join(lines)


def markdown_compare_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# FailMap Compare Report",
        "",
        f"- Baseline cases: {payload['baseline_case_count']}",
        f"- Candidate cases: {payload['candidate_case_count']}",
        f"- Cluster count: {payload['cluster_count']}",
        "",
        "## Summary",
        "",
        f"- New: {summary['new']}",
        f"- Resolved: {summary['resolved']}",
        f"- Growing: {summary['growing']}",
        f"- Shrinking: {summary['shrinking']}",
        f"- Unchanged: {summary['unchanged']}",
        "",
    ]
    for cluster in payload.get("clusters", []):
        if cluster["status"] == "unchanged":
            continue
        lines.append(f"## {cluster['signature']}")
        lines.append("")
        lines.append(f"- Status: {cluster['status']}")
        lines.append(
            f"- Cases: {cluster['baseline_case_count']} -> {cluster['candidate_case_count']} ({cluster['delta']:+d})"
        )
        baseline_examples = ", ".join(cluster.get("baseline_examples", [])) or "none"
        candidate_examples = ", ".join(cluster.get("candidate_examples", [])) or "none"
        lines.append(f"- Baseline examples: {baseline_examples}")
        lines.append(f"- Candidate examples: {candidate_examples}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
