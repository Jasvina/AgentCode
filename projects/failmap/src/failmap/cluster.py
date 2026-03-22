from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .io import load_manifest


def _sorted_counts(items: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"name": key, "count": value}
        for key, value in sorted(items.items(), key=lambda item: (-item[1], item[0]))
    ]


def build_clusters(pack_dir: str | Path) -> dict[str, Any]:
    manifest = load_manifest(pack_dir)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in manifest.get("cases", []):
        grouped[str(case.get("signature") or "unknown")].append(case)

    clusters: list[dict[str, Any]] = []
    total_cases = 0
    for signature, cases in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        total_cases += len(cases)
        agent_counts: dict[str, int] = defaultdict(int)
        model_counts: dict[str, int] = defaultdict(int)
        tag_counts: dict[str, int] = defaultdict(int)
        successes = 0
        failures = 0

        for case in cases:
            agent_counts[str(case.get("agent_name") or "unknown")] += 1
            model_counts[str(case.get("model") or "unknown")] += 1
            for tag in case.get("tags", []):
                tag_counts[str(tag)] += 1
            if case.get("success"):
                successes += 1
            else:
                failures += 1

        clusters.append(
            {
                "signature": signature,
                "case_count": len(cases),
                "successes": successes,
                "failures": failures,
                "agents": _sorted_counts(agent_counts),
                "models": _sorted_counts(model_counts),
                "tags": _sorted_counts(tag_counts),
                "example_episode_ids": [str(case.get("episode_id")) for case in cases[:3]],
                "example_files": [str(case.get("file")) for case in cases[:3]],
            }
        )

    return {
        "format": "failmap-v1",
        "source_format": manifest.get("format", "unknown"),
        "source_pack": str(Path(pack_dir)),
        "case_count": total_cases,
        "cluster_count": len(clusters),
        "clusters": clusters,
    }
