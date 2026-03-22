from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_json


def _index_clusters(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(cluster.get("signature") or "unknown"): cluster
        for cluster in payload.get("clusters", [])
    }


def _status(baseline_count: int, candidate_count: int) -> str:
    if baseline_count == 0 and candidate_count > 0:
        return "new"
    if baseline_count > 0 and candidate_count == 0:
        return "resolved"
    if candidate_count > baseline_count:
        return "growing"
    if candidate_count < baseline_count:
        return "shrinking"
    return "unchanged"


def compare_cluster_files(baseline_path: str | Path, candidate_path: str | Path) -> dict[str, Any]:
    baseline = load_json(baseline_path)
    candidate = load_json(candidate_path)
    baseline_index = _index_clusters(baseline)
    candidate_index = _index_clusters(candidate)

    signatures = sorted(set(baseline_index) | set(candidate_index))
    clusters: list[dict[str, Any]] = []
    counts = {
        "new": 0,
        "resolved": 0,
        "growing": 0,
        "shrinking": 0,
        "unchanged": 0,
    }

    for signature in signatures:
        left = baseline_index.get(signature, {})
        right = candidate_index.get(signature, {})
        baseline_count = int(left.get("case_count", 0))
        candidate_count = int(right.get("case_count", 0))
        status = _status(baseline_count, candidate_count)
        counts[status] += 1
        clusters.append(
            {
                "signature": signature,
                "status": status,
                "baseline_case_count": baseline_count,
                "candidate_case_count": candidate_count,
                "delta": candidate_count - baseline_count,
                "baseline_examples": left.get("example_episode_ids", []),
                "candidate_examples": right.get("example_episode_ids", []),
                "candidate_agents": [item.get("name") for item in right.get("agents", [])],
                "candidate_models": [item.get("name") for item in right.get("models", [])],
                "candidate_tags": [item.get("name") for item in right.get("tags", [])],
            }
        )

    clusters.sort(key=lambda item: (-abs(item["delta"]), item["signature"]))
    return {
        "format": "failmap-compare-v1",
        "baseline": str(Path(baseline_path)),
        "candidate": str(Path(candidate_path)),
        "baseline_case_count": int(baseline.get("case_count", 0)),
        "candidate_case_count": int(candidate.get("case_count", 0)),
        "cluster_count": len(clusters),
        "summary": counts,
        "clusters": clusters,
    }
