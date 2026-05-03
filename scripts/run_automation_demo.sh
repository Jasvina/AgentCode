#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_DIR="${1:-${TMPDIR:-/tmp}/agentreliabilitykit-automation-demo-${TIMESTAMP}}"

mkdir -p "$OUTPUT_DIR"

echo "Writing automation demo artifacts to: $OUTPUT_DIR"

run_agentci() {
  cd "$ROOT_DIR/projects/agentci"
  PYTHONPATH=src python3 -m agentci.cli summarize \
    examples/openai_agents_episode.json \
    --json > "$OUTPUT_DIR/agentci-summary.json"

  PYTHONPATH=src python3 -m agentci.cli assert-regression \
    examples/math_episode.json \
    examples/math_episode_latency_candidate.json \
    --ignore-diff-prefix metric:latency_ms \
    --json > "$OUTPUT_DIR/agentci-regression.json"
}

run_tracepack() {
  cd "$ROOT_DIR/projects/tracepack"
  PYTHONPATH=src python3 -m tracepack.cli scan \
    examples/source_episodes \
    --json > "$OUTPUT_DIR/tracepack-scan.json"

  PYTHONPATH=src python3 -m tracepack.cli build \
    examples/source_episodes \
    "$OUTPUT_DIR/tracepack-pack" \
    --only-failures \
    --redact \
    --max-per-signature 2 \
    --json > "$OUTPUT_DIR/tracepack-build.json"

  PYTHONPATH=src python3 -m tracepack.cli inspect \
    "$OUTPUT_DIR/tracepack-pack" \
    --json > "$OUTPUT_DIR/tracepack-inspect.json"
}

run_failmap() {
  cd "$ROOT_DIR/projects/failmap"
  PYTHONPATH=src python3 -m failmap.cli cluster \
    "$OUTPUT_DIR/tracepack-pack" \
    "$OUTPUT_DIR/failmap-clusters.json" \
    --json > "$OUTPUT_DIR/failmap-cluster.json"

  PYTHONPATH=src python3 -m failmap.cli summarize \
    "$OUTPUT_DIR/failmap-clusters.json" \
    --json > "$OUTPUT_DIR/failmap-summary.json"
}

run_packslice() {
  cd "$ROOT_DIR/projects/packslice"
  PYTHONPATH=src python3 -m packslice.cli split \
    "$OUTPUT_DIR/tracepack-pack" \
    "$OUTPUT_DIR/packslice" \
    --group-by signature \
    --train-ratio 70 \
    --eval-ratio 15 \
    --test-ratio 15 \
    --json > "$OUTPUT_DIR/packslice-split.json"

  PYTHONPATH=src python3 -m packslice.cli summarize \
    "$OUTPUT_DIR/packslice" \
    --json > "$OUTPUT_DIR/packslice-summary.json"
}

write_manifest() {
  python3 - "$OUTPUT_DIR" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

out = Path(sys.argv[1])

def load_json(name: str) -> dict:
    return json.loads((out / name).read_text(encoding="utf-8"))

agentci_summary = load_json("agentci-summary.json")
agentci_regression = load_json("agentci-regression.json")
tracepack_scan = load_json("tracepack-scan.json")
tracepack_build = load_json("tracepack-build.json")
tracepack_inspect = load_json("tracepack-inspect.json")
failmap_cluster = load_json("failmap-cluster.json")
packslice_summary = load_json("packslice-summary.json")

manifest = {
    "format": "agentreliabilitykit-demo-v1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "artifact_root": str(out),
    "toolchain": ["AgentCI", "TracePack", "FailMap", "PackSlice"],
    "artifacts": {
        "agentci_summary": "agentci-summary.json",
        "agentci_regression": "agentci-regression.json",
        "tracepack_scan": "tracepack-scan.json",
        "tracepack_build": "tracepack-build.json",
        "tracepack_inspect": "tracepack-inspect.json",
        "tracepack_pack_manifest": "tracepack-pack/manifest.json",
        "failmap_cluster": "failmap-cluster.json",
        "failmap_clusters": "failmap-clusters.json",
        "failmap_summary": "failmap-summary.json",
        "packslice_split": "packslice-split.json",
        "packslice_summary": "packslice-summary.json",
        "packslice_manifest": "packslice/summary.json",
    },
    "summary": {
        "agentci": {
            "episode_id": agentci_summary["episode_id"],
            "agent_name": agentci_summary["agent_name"],
            "tool_calls": agentci_summary["tool_calls"],
            "model_calls": agentci_summary["model_calls"],
            "success": agentci_summary["success"],
            "regression_passed": agentci_regression["passed"],
        },
        "tracepack": {
            "episode_count": tracepack_scan["episode_count"],
            "failure_count": tracepack_scan["failures"],
            "pack_case_count": tracepack_inspect["case_count"],
            "redacted": tracepack_inspect["redacted"],
            "only_failures": tracepack_build["only_failures"],
        },
        "failmap": {
            "cluster_count": failmap_cluster["cluster_count"],
            "case_count": failmap_cluster["case_count"],
            "top_signatures": [cluster["signature"] for cluster in failmap_cluster.get("clusters", [])[:3]],
        },
        "packslice": {
            "total_cases": packslice_summary["total_cases"],
            "split_counts": {
                split["name"]: split["case_count"]
                for split in packslice_summary.get("splits", [])
            },
        },
    },
}

(out / "manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
}

run_agentci
run_tracepack
run_failmap
run_packslice
write_manifest

cat <<EOF
Done.

Key outputs:
- $OUTPUT_DIR/manifest.json
- $OUTPUT_DIR/agentci-summary.json
- $OUTPUT_DIR/agentci-regression.json
- $OUTPUT_DIR/tracepack-pack/manifest.json
- $OUTPUT_DIR/failmap-clusters.json
- $OUTPUT_DIR/packslice/summary.json

See also:
- $ROOT_DIR/docs/automation.md
EOF
