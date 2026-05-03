# Automation Guide

This guide shows how to automate the full `AgentReliabilityKit` toolchain in a way that works for local scripts, CI jobs, and later dashboards:

```text
AgentCI   -> record or validate episodes
TracePack -> package compatible episodes into a reusable pack
FailMap   -> cluster recurring failures and compare snapshots
PackSlice -> split a pack into train/eval/test datasets
```

The key design choice across the repo is that every tool now has machine-readable CLI output, so you can hand off artifacts without scraping human log text.

## What gets passed between tools

The main artifact chain looks like this:

1. `AgentCI` works with portable episode JSON files.
2. `TracePack` reads a directory of those compatible episode JSON files and writes a pack with `manifest.json` plus `cases/`.
3. `FailMap` reads a TracePack pack and writes clustered failure snapshots.
4. `PackSlice` reads a TracePack pack and writes split manifests for `train`, `eval`, and `test`.

In practice:

- `AgentCI` is your regression gate and episode recorder.
- `TracePack` is your packaging layer.
- `FailMap` is your triage and release-comparison layer.
- `PackSlice` is your dataset prep layer.

## Local prerequisites

From a clean checkout, each project can be driven either with editable installs or directly with `PYTHONPATH=src`.

For automation, `PYTHONPATH=src python -m ...` is often the simplest because it avoids managing multiple virtualenv activations inside one script.

Examples in this doc assume:

- repo root: `AgentReliabilityKit/`
- Python 3.10+
- commands run from the relevant project directory, or with explicit `cd`

## Quick end-to-end demo

The repo includes a companion script:

```bash
./scripts/run_automation_demo.sh
```

It writes a timestamped output directory under `/tmp` by default and produces:

- one root `manifest.json` that indexes the whole run
- AgentCI JSON summaries
- a TracePack pack
- a FailMap cluster snapshot
- a PackSlice split output

To write into a fixed directory instead:

```bash
./scripts/run_automation_demo.sh /tmp/agentreliabilitykit-demo
```

### Root demo manifest contract

The root `manifest.json` produced by `./scripts/run_automation_demo.sh` is intended to be the stable entrypoint for downstream automation. Its current contract is:

- `format`: the top-level manifest format identifier, currently `agentreliabilitykit-demo-v1`
- `generated_at`: UTC timestamp for the demo run
- `artifact_root`: absolute path to the generated demo directory
- `toolchain`: ordered list of the tool names included in the run
- `artifacts`: map of logical artifact names to relative file paths within the demo output directory
- `summary`: compact per-tool summary values for `agentci`, `tracepack`, `failmap`, and `packslice`

The `artifacts` map currently indexes these logical outputs:

- `agentci_summary` -> `agentci-summary.json`
- `agentci_regression` -> `agentci-regression.json`
- `tracepack_scan` -> `tracepack-scan.json`
- `tracepack_build` -> `tracepack-build.json`
- `tracepack_inspect` -> `tracepack-inspect.json`
- `tracepack_pack_manifest` -> `tracepack-pack/manifest.json`
- `failmap_cluster` -> `failmap-cluster.json`
- `failmap_clusters` -> `failmap-clusters.json`
- `failmap_summary` -> `failmap-summary.json`
- `packslice_split` -> `packslice-split.json`
- `packslice_summary` -> `packslice-summary.json`
- `packslice_manifest` -> `packslice/summary.json`

For CI and dashboard consumers, treat `format`, `artifacts`, and the per-tool `summary` blocks as the stable fields to depend on first.

## Step-by-step pipeline

### 1. AgentCI: validate or gate compatible episodes

Use AgentCI when you want regression checks or compact machine-readable summaries for CI.

```bash
cd projects/agentci

PYTHONPATH=src python3 -m agentci.cli summarize \
  examples/openai_agents_episode.json \
  --json

PYTHONPATH=src python3 -m agentci.cli assert-regression \
  examples/math_episode.json \
  examples/math_episode_latency_candidate.json \
  --ignore-diff-prefix metric:latency_ms \
  --json
```

Typical outputs:

- `summarize --json` gives `episode_id`, `tool_calls`, `model_calls`, `metrics`, and `success`
- `assert-regression --json` gives `passed`, `diff_items`, and `replay_mismatches`

Recommended use:

- fail the build if `passed` is `false`
- upload the JSON result as a CI artifact for later debugging

### 2. TracePack: turn episodes into a reusable pack

TracePack consumes a directory of AgentCI-compatible episode JSON files.

For a stable demo input, this repo includes example episodes under `projects/tracepack/examples/source_episodes`.

```bash
cd projects/tracepack

PYTHONPATH=src python3 -m tracepack.cli scan \
  examples/source_episodes \
  --json

PYTHONPATH=src python3 -m tracepack.cli build \
  examples/source_episodes \
  /tmp/agentreliabilitykit-demo/tracepack-pack \
  --only-failures \
  --redact \
  --max-per-signature 2 \
  --json

PYTHONPATH=src python3 -m tracepack.cli inspect \
  /tmp/agentreliabilitykit-demo/tracepack-pack \
  --json

PYTHONPATH=src python3 -m tracepack.cli validate \
  /tmp/agentreliabilitykit-demo/tracepack-pack \
  --json
```

Recommended use:

- run `scan --json` first for preflight counts
- run `build --json` to create the portable artifact
- run `inspect --json` to confirm the built pack shape before downstream jobs consume it
- run `validate --json` to fail fast on malformed pack structure before FailMap or PackSlice reads it

Important fields:

- `episode_count`, `successes`, `failures`, `sensitive`
- `case_count`, `redacted`, `max_per_signature`
- per-case `signature`, `labels`, and `source_path`

### 3. FailMap: cluster recurring failures from the pack

FailMap reads the TracePack output and turns it into a triage-oriented snapshot.

```bash
cd projects/failmap

PYTHONPATH=src python3 -m failmap.cli cluster \
  /tmp/agentreliabilitykit-demo/tracepack-pack \
  /tmp/agentreliabilitykit-demo/failmap-clusters.json \
  --json

PYTHONPATH=src python3 -m failmap.cli summarize \
  /tmp/agentreliabilitykit-demo/failmap-clusters.json \
  --json
```

If you want release-over-release comparisons later:

```bash
PYTHONPATH=src python3 -m failmap.cli compare \
  previous-clusters.json \
  current-clusters.json \
  compare.json \
  --json

PYTHONPATH=src python3 -m failmap.cli compare-summary \
  compare.json \
  --json
```

Recommended use:

- publish `cluster` output as a versioned artifact per build or release
- compare cluster snapshots between releases to identify `new`, `growing`, or `resolved` failure modes
- generate issue drafts only for selected statuses

Important fields:

- `cluster_count`, `case_count`
- cluster `signature`, `case_count`, `agents`, `models`, `tags`
- compare `summary.new`, `summary.growing`, `summary.resolved`

### 4. PackSlice: create train/eval/test splits from the same pack

PackSlice works directly on the TracePack artifact, so you can prepare datasets from the exact same pack you cluster in FailMap.

```bash
cd projects/packslice

PYTHONPATH=src python3 -m packslice.cli split \
  /tmp/agentreliabilitykit-demo/tracepack-pack \
  /tmp/agentreliabilitykit-demo/packslice \
  --group-by signature \
  --train-ratio 70 \
  --eval-ratio 15 \
  --test-ratio 15 \
  --json

PYTHONPATH=src python3 -m packslice.cli summarize \
  /tmp/agentreliabilitykit-demo/packslice \
  --json
```

Recommended use:

- use `signature` grouping for failure-mode balancing
- switch to `--chronological --order-by source_path` for release-style evaluation
- save `summary.json` so downstream eval jobs can record exactly which slices were used

Important fields:

- `total_cases`
- `group_by`, `order_by`, `chronological`
- `splits[].case_count`
- `splits[].signatures`

## Suggested CI handoff pattern

One practical pattern is:

1. run `AgentCI` regression checks on prompt/model/tool changes
2. if the gate passes, build or refresh a `TracePack` pack
3. cluster that pack with `FailMap`
4. split the same pack with `PackSlice`
5. upload all JSON outputs as artifacts

That gives you:

- regression confidence for the change being merged
- a reusable pack for future benchmarks
- a triage snapshot for recurring failures
- reproducible train/eval/test splits from the same source artifact

## Example shell assertions

You do not need `jq`; plain Python works everywhere GitHub Actions already has Python.

```bash
agentci summarize examples/openai_agents_episode.json --json > summary.json
python -c "import json; data=json.load(open('summary.json')); assert data['tool_calls'] >= 1"

tracepack inspect /tmp/agentreliabilitykit-demo/tracepack-pack --json > inspect.json
python -c "import json; data=json.load(open('inspect.json')); assert data['case_count'] >= 1"

failmap compare-summary compare.json --json > compare-summary.json
python -c "import json; data=json.load(open('compare-summary.json')); assert 'summary' in data"

packslice summarize /tmp/agentreliabilitykit-demo/packslice --json > split-summary.json
python -c "import json; data=json.load(open('split-summary.json')); assert len(data['splits']) == 3"
```

## Recommended artifact layout

For a real CI job, a layout like this works well:

```text
artifacts/
  manifest.json
  agentci/
    summary.json
    regression.json
  tracepack/
    scan.json
    build.json
    inspect.json
    pack/
      manifest.json
      cases/
  failmap/
    clusters.json
    summary.json
    compare.json
  packslice/
    split.json
    summary.json
    train/
    eval/
    test/
```

This keeps every stage debuggable on its own while still making the artifact chain obvious.

## When to branch the flow

Use the straight-through flow when:

- you want a fresh pack from new episodes
- you want fresh failure clustering
- you want new split outputs from the same pack

Branch into compare or issue-drafting flows when:

- you already have a baseline and candidate FailMap snapshot
- you want release-over-release triage instead of a fresh single-snapshot summary
- you want Markdown issue drafts for planning or GitHub import

## Repo references

- root overview: `README.md`
- CI checks: `.github/workflows/ci.yml`
- companion automation script: `scripts/run_automation_demo.sh`
- AgentCI docs: `projects/agentci/README.md`
- TracePack docs: `projects/tracepack/README.md`
- FailMap docs: `projects/failmap/README.md`
- PackSlice docs: `projects/packslice/README.md`
