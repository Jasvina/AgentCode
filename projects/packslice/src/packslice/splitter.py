from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import shutil
from typing import Any

from .io import load_manifest, write_json

SPLIT_NAMES = ("train", "eval", "test")


def _largest_remainder_counts(total: int, ratios: tuple[int, int, int]) -> dict[str, int]:
    counts = {name: 0 for name in SPLIT_NAMES}
    active = [name for name, ratio in zip(SPLIT_NAMES, ratios) if ratio > 0]
    if not active:
        return counts

    if total >= len(active):
        for name in active:
            counts[name] = 1
        total -= len(active)
    else:
        for name in active[:total]:
            counts[name] = 1
        return counts

    ratio_sum = sum(ratios)
    raw = {name: total * ratio / ratio_sum for name, ratio in zip(SPLIT_NAMES, ratios)}
    additions = {name: int(value) for name, value in raw.items()}
    for name in SPLIT_NAMES:
        counts[name] += additions[name]
    assigned = sum(additions.values())
    remainders = sorted(
        ((raw[name] - additions[name], name) for name in SPLIT_NAMES),
        key=lambda item: (-item[0], item[1]),
    )
    for _, name in remainders[: total - assigned]:
        counts[name] += 1
    return counts


def _sort_value(case: dict[str, Any], order_by: str) -> tuple[str, str]:
    primary = str(case.get(order_by) or "")
    return primary, str(case.get("episode_id") or case.get("file") or "")


def _filter_cases(
    cases: list[dict[str, Any]],
    *,
    include_labels: tuple[str, ...] = (),
    success_mode: str = "all",
) -> list[dict[str, Any]]:
    filtered = []
    for case in cases:
        if success_mode == "success-only" and not case.get("success"):
            continue
        if success_mode == "failure-only" and case.get("success"):
            continue
        labels = {str(label) for label in case.get("labels", [])}
        if include_labels and not set(include_labels).issubset(labels):
            continue
        filtered.append(case)
    return filtered


def _group_cases(cases: list[dict[str, Any]], group_by: str, order_by: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        key = str(case.get(group_by) or "unknown")
        grouped[key].append(case)
    for key in grouped:
        grouped[key] = sorted(grouped[key], key=lambda item: _sort_value(item, order_by))
    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def _distribute_cases(
    cases: list[dict[str, Any]],
    counts: dict[str, int],
    *,
    chronological: bool,
) -> dict[str, list[dict[str, Any]]]:
    assigned = {name: [] for name in SPLIT_NAMES}
    if chronological:
        cursor = 0
        for split_name in SPLIT_NAMES:
            take = counts[split_name]
            assigned[split_name].extend(cases[cursor : cursor + take])
            cursor += take
        return assigned

    remaining = dict(counts)
    order = [name for name in SPLIT_NAMES if remaining[name] > 0]
    index = 0
    for case in cases:
        while order and remaining[order[index % len(order)]] == 0:
            order = [name for name in order if remaining[name] > 0]
            index = 0
            if not order:
                break
        if not order:
            break
        split_name = order[index % len(order)]
        assigned[split_name].append(case)
        remaining[split_name] -= 1
        index += 1
    return assigned


def _copy_case_file(source_pack: Path, case: dict[str, Any], target_root: Path) -> None:
    case_file = case.get("file")
    if not case_file:
        return
    source = source_pack / str(case_file)
    if not source.exists():
        return
    target = target_root / str(case_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def split_pack(
    source_pack: str | Path,
    output_dir: str | Path,
    *,
    ratios: tuple[int, int, int] = (70, 15, 15),
    group_by: str = "signature",
    include_labels: tuple[str, ...] = (),
    success_mode: str = "all",
    chronological: bool = False,
    order_by: str = "episode_id",
) -> dict[str, Any]:
    source_root = Path(source_pack)
    manifest = load_manifest(source_root)
    filtered_cases = _filter_cases(
        list(manifest.get("cases", [])),
        include_labels=include_labels,
        success_mode=success_mode,
    )
    grouped = _group_cases(filtered_cases, group_by, order_by)
    split_cases: dict[str, list[dict[str, Any]]] = {name: [] for name in SPLIT_NAMES}

    for _, cases in grouped.items():
        counts = _largest_remainder_counts(len(cases), ratios)
        distributed = _distribute_cases(cases, counts, chronological=chronological)
        for split_name in SPLIT_NAMES:
            split_cases[split_name].extend(distributed[split_name])

    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    summary_splits = []
    for split_name in SPLIT_NAMES:
        split_root = out_root / split_name
        split_root.mkdir(parents=True, exist_ok=True)
        cases = split_cases[split_name]
        for case in cases:
            _copy_case_file(source_root, case, split_root)
        split_manifest = {
            "format": "packslice-v1",
            "source_format": manifest.get("format", "unknown"),
            "source_pack": str(source_pack),
            "split": split_name,
            "group_by": group_by,
            "order_by": order_by,
            "chronological": chronological,
            "filters": {
                "include_labels": list(include_labels),
                "success_mode": success_mode,
            },
            "ratios": {"train": ratios[0], "eval": ratios[1], "test": ratios[2]},
            "case_count": len(cases),
            "cases": cases,
        }
        write_json(split_root / "manifest.json", split_manifest)
        summary_splits.append(
            {
                "name": split_name,
                "case_count": len(cases),
                "signatures": _summarize_signatures(cases),
            }
        )

    summary = {
        "format": "packslice-summary-v1",
        "source_pack": str(source_pack),
        "group_by": group_by,
        "order_by": order_by,
        "chronological": chronological,
        "filters": {
            "include_labels": list(include_labels),
            "success_mode": success_mode,
        },
        "ratios": {"train": ratios[0], "eval": ratios[1], "test": ratios[2]},
        "total_cases": len(filtered_cases),
        "splits": summary_splits,
    }
    write_json(out_root / "summary.json", summary)
    return summary


def _summarize_signatures(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        counts[str(case.get("signature") or "unknown")] += 1
    return [
        {"signature": signature, "count": count}
        for signature, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
