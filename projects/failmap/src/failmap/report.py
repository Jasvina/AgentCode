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


def summarize_trends(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"Snapshots: {payload['snapshot_count']}",
        f"Tracked signatures: {payload['signature_count']}",
        "Latest snapshot changes:",
        f"- new: {summary['new_in_latest']}",
        f"- resolved: {summary['resolved_in_latest']}",
        f"- growing: {summary['growing_in_latest']}",
        f"- shrinking: {summary['shrinking_in_latest']}",
        f"- stable: {summary['stable_in_latest']}",
    ]
    visible = [item for item in payload.get("signatures", []) if item["latest_case_count"] > 0][:5]
    if visible:
        lines.append("Top latest signatures:")
        for item in visible:
            delta = item["delta_latest"]
            lines.append(
                f"- {item['signature']} ({item['latest_case_count']} cases, {delta:+d} vs previous) [{item['latest_status']}]"
            )
    return "\n".join(lines)


def markdown_trend_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    snapshot_labels = ", ".join(snapshot["label"] for snapshot in payload.get("snapshots", [])) or "none"
    lines = [
        "# FailMap Trend Report",
        "",
        f"- Snapshots: {payload['snapshot_count']}",
        f"- Snapshot labels: {snapshot_labels}",
        f"- Tracked signatures: {payload['signature_count']}",
        "",
        "## Latest snapshot summary",
        "",
        f"- New in latest: {summary['new_in_latest']}",
        f"- Resolved in latest: {summary['resolved_in_latest']}",
        f"- Growing in latest: {summary['growing_in_latest']}",
        f"- Shrinking in latest: {summary['shrinking_in_latest']}",
        f"- Stable in latest: {summary['stable_in_latest']}",
        "",
        "## Signatures",
        "",
    ]
    for item in payload.get("signatures", []):
        counts = " -> ".join(str(point["case_count"]) for point in item.get("points", []))
        lines.append(f"### {item['signature']}")
        lines.append("")
        lines.append(f"- Trend: `{counts}`")
        lines.append(f"- Latest status: `{item['latest_status']}`")
        lines.append(f"- Latest count: {item['latest_case_count']}")
        lines.append(f"- Previous count: {item['previous_case_count']}")
        lines.append(f"- Delta vs previous: {item['delta_latest']:+d}")
        lines.append(f"- Peak count: {item['peak_case_count']}")
        lines.append(f"- First seen: {item['first_seen'] or 'never'}")
        lines.append(f"- Last seen: {item['last_seen'] or 'never'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
