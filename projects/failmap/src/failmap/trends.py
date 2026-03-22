from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_json


def _index_clusters(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(cluster.get("signature") or "unknown"): cluster
        for cluster in payload.get("clusters", [])
    }


def _latest_status(previous_count: int, latest_count: int) -> str:
    if previous_count == 0 and latest_count > 0:
        return "new_in_latest"
    if previous_count > 0 and latest_count == 0:
        return "resolved_in_latest"
    if latest_count > previous_count:
        return "growing_in_latest"
    if latest_count < previous_count:
        return "shrinking_in_latest"
    if latest_count > 0:
        return "stable_in_latest"
    return "absent_in_latest"


def build_trend_report(cluster_paths: list[str | Path]) -> dict[str, Any]:
    if not cluster_paths:
        raise ValueError("expected at least one cluster snapshot")

    snapshots: list[dict[str, Any]] = []
    indices: list[dict[str, dict[str, Any]]] = []
    for raw_path in cluster_paths:
        path = Path(raw_path)
        payload = load_json(path)
        snapshots.append(
            {
                "label": path.stem,
                "path": str(path),
                "case_count": int(payload.get("case_count", 0)),
                "cluster_count": int(payload.get("cluster_count", 0)),
            }
        )
        indices.append(_index_clusters(payload))

    signatures = sorted({signature for index in indices for signature in index})
    tracked: list[dict[str, Any]] = []
    status_counts = {
        "new_in_latest": 0,
        "resolved_in_latest": 0,
        "growing_in_latest": 0,
        "shrinking_in_latest": 0,
        "stable_in_latest": 0,
        "absent_in_latest": 0,
    }

    for signature in signatures:
        counts: list[int] = []
        points: list[dict[str, Any]] = []
        for snapshot, index in zip(snapshots, indices):
            count = int(index.get(signature, {}).get("case_count", 0))
            counts.append(count)
            points.append({"label": snapshot["label"], "case_count": count})

        first_seen = next((point["label"] for point in points if point["case_count"] > 0), None)
        last_seen = next((point["label"] for point in reversed(points) if point["case_count"] > 0), None)
        latest_count = counts[-1]
        previous_count = counts[-2] if len(counts) > 1 else 0
        latest_status = _latest_status(previous_count, latest_count)
        status_counts[latest_status] += 1

        tracked.append(
            {
                "signature": signature,
                "points": points,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "peak_case_count": max(counts),
                "latest_case_count": latest_count,
                "previous_case_count": previous_count,
                "delta_latest": latest_count - previous_count,
                "latest_status": latest_status,
            }
        )

    tracked.sort(
        key=lambda item: (
            -item["latest_case_count"],
            -item["peak_case_count"],
            item["signature"],
        )
    )

    return {
        "format": "failmap-trends-v1",
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "signature_count": len(tracked),
        "summary": status_counts,
        "signatures": tracked,
    }
