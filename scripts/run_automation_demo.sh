#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_DIR="${1:-${TMPDIR:-/tmp}/agentcode-automation-demo-${TIMESTAMP}}"

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

run_agentci
run_tracepack
run_failmap
run_packslice

cat <<EOF
Done.

Key outputs:
- $OUTPUT_DIR/agentci-summary.json
- $OUTPUT_DIR/agentci-regression.json
- $OUTPUT_DIR/tracepack-pack/manifest.json
- $OUTPUT_DIR/failmap-clusters.json
- $OUTPUT_DIR/packslice/summary.json

See also:
- $ROOT_DIR/docs/automation.md
EOF
