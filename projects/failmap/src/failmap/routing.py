from __future__ import annotations

from typing import Any


def _as_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def _contains_any(haystack: str, needles: list[str]) -> bool:
    return any(needle in haystack for needle in needles)


def _overlaps(left: list[str], right: list[str]) -> bool:
    return bool(set(left) & set(right))


def _match_rule(cluster: dict[str, Any], match: dict[str, Any]) -> bool:
    signature = str(cluster.get("signature") or "")
    status = str(cluster.get("status") or "")
    candidate_case_count = int(cluster.get("candidate_case_count", 0))
    delta = int(cluster.get("delta", 0))
    candidate_tags = _as_string_list(cluster.get("candidate_tags"))
    candidate_agents = _as_string_list(cluster.get("candidate_agents"))
    candidate_models = _as_string_list(cluster.get("candidate_models"))

    if "status_in" in match and status not in _as_string_list(match.get("status_in")):
        return False
    if "signature_contains" in match and not _contains_any(signature, _as_string_list(match.get("signature_contains"))):
        return False
    if "tag_in" in match and not _overlaps(candidate_tags, _as_string_list(match.get("tag_in"))):
        return False
    if "agent_in" in match and not _overlaps(candidate_agents, _as_string_list(match.get("agent_in"))):
        return False
    if "model_in" in match and not _overlaps(candidate_models, _as_string_list(match.get("model_in"))):
        return False
    if "min_candidate_case_count" in match and candidate_case_count < int(match["min_candidate_case_count"]):
        return False
    if "min_delta" in match and delta < int(match["min_delta"]):
        return False
    return True


def apply_routing_rules(
    cluster: dict[str, Any],
    rules_payload: dict[str, Any] | None,
    *,
    fallback_owner: str,
    fallback_priority: str,
    fallback_labels: list[str],
) -> dict[str, Any]:
    result = {
        "owner": fallback_owner,
        "priority": fallback_priority,
        "labels": list(fallback_labels),
        "matched_rules": [],
    }
    if not rules_payload:
        return result

    defaults = rules_payload.get("defaults", {})
    if isinstance(defaults, dict):
        if defaults.get("owner"):
            result["owner"] = str(defaults["owner"])
        if defaults.get("priority"):
            result["priority"] = str(defaults["priority"])
        result["labels"].extend(_as_string_list(defaults.get("labels")))

    for rule in rules_payload.get("rules", []):
        if not isinstance(rule, dict):
            continue
        match = rule.get("match", {})
        if not isinstance(match, dict) or not _match_rule(cluster, match):
            continue
        update = rule.get("set", {})
        if not isinstance(update, dict):
            continue
        if update.get("owner"):
            result["owner"] = str(update["owner"])
        if update.get("priority"):
            result["priority"] = str(update["priority"])
        result["labels"].extend(_as_string_list(update.get("labels")))
        name = str(rule.get("name") or f"rule-{len(result['matched_rules']) + 1}")
        result["matched_rules"].append(name)

    result["labels"] = sorted(set(str(label) for label in result["labels"]))
    return result
