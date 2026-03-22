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
