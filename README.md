# AgentEvalKit

[![CI](https://github.com/Jasvina/AgentEvalKit/actions/workflows/ci.yml/badge.svg)](https://github.com/Jasvina/AgentEvalKit/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Jasvina/AgentEvalKit)](LICENSE)
[![Monorepo](https://img.shields.io/badge/layout-agent%20tooling%20monorepo-0a7bbb)](https://github.com/Jasvina/AgentEvalKit)

A public monorepo for practical open-source projects in the LLM Agent stack.

I am deliberately not collecting random demos here. Each project is chosen from a specific gap in the current GitHub landscape: crowded categories already have plenty of frameworks, browser agents, coding agents, and memory layers, so this repo focuses on under-built infrastructure around reproducibility, regression testing, and turning real traces into reusable eval assets.

## Why this repo exists

After surveying today's high-star Agent repositories, four opportunities stood out:

- teams can build agents, but still struggle to replay failures and guard against regressions
- teams can trace agents, but still lack clean tooling to turn real trajectories into reusable eval packs and benchmark cases
- teams can collect failures, but still lack a simple OSS layer for clustering recurring failure modes and prioritizing fixes across releases
- teams can build eval packs, but still lack balanced split tooling for train/eval/test and release slicing

`AgentEvalKit` is a place to build those missing layers as focused OSS projects.

## Architecture at a glance

<p align="center">
  <img src="docs/assets/agentevalkit-overview.svg" alt="AgentEvalKit architecture overview" width="100%" />
</p>

This is the intended product story for the monorepo:

- `AgentCI` turns real runs into replayable regression artifacts
- `TracePack` packages those runs into reusable benchmark cases
- `FailMap` turns repeated failures into triage-ready clusters
- `PackSlice` creates stable train/eval/test slices from the same pack
- the root CI workflow validates that the whole chain works end to end

## Quick demo output

<p align="center">
  <img src="docs/assets/agentevalkit-demo-terminal.svg" alt="AgentEvalKit terminal-style demo output" width="100%" />
</p>

If you want a one-command walkthrough of the whole repo:

```bash
./scripts/run_automation_demo.sh /tmp/agentevalkit-demo
```

That gives visitors an immediate answer to the most important README question: “what does this repo actually produce when I run it?”

## Projects

### 1. AgentCI

Path: `projects/agentci`

Replay-first regression testing for tool-using LLM agents, with portable episode traces, HTML diff reports, and pytest-friendly regression assertions.

### 2. TracePack

Path: `projects/tracepack`

Build reusable benchmark packs from real agent traces, with recursive redaction, case labels, jsonl/chat export, and signature-aware sampling for eval pipelines.

### 3. FailMap

Path: `projects/failmap`

Cluster recurring agent failures from TracePack packs, compare releases, generate issue-ready triage drafts with rules-driven routing, bundle them for planning, and track failure trends across snapshots.

### 4. PackSlice

Path: `projects/packslice`

Create balanced train/eval/test splits from TracePack packs with distribution-aware, label-aware, and chronological slicing modes.

## Toolchain story

```text
AgentCI   -> record and diff trajectories
TracePack -> turn trajectories into reusable benchmark packs
FailMap   -> cluster failures, compare releases, generate triage issues, bundle work
PackSlice -> split packs into balanced train/eval/test datasets
```

## Machine-readable CLI story

All four projects now support JSON-friendly CLI flows, so they can be chained in CI without scraping human text output:

```bash
agentci summarize projects/agentci/examples/math_episode.json --json
tracepack scan projects/tracepack/examples/source_episodes --json
failmap summarize projects/failmap/examples/clusters.json --json
packslice summarize projects/packslice/examples/split_demo --json
```

That makes it easier to build release checks, artifact pipelines, and automated dashboards on top of the same OSS commands shown in the READMEs.

For a fuller walkthrough, see `docs/automation.md`, the companion script `scripts/run_automation_demo.sh`, and the monorepo contributor guide in `CONTRIBUTING.md`.

## What the monorepo demo produces

The root workflow now runs an end-to-end automation demo and uploads artifacts that mirror a real team handoff:

```text
manifest.json
agentci-summary.json
agentci-regression.json
tracepack-pack/
  manifest.json
  cases/
failmap-clusters.json
packslice/
  summary.json
  train/
  eval/
  test/
```

The top-level `manifest.json` acts as a machine-readable index for the full demo run, so CI jobs, dashboards, or artifact consumers can discover the output set and key summary metrics from one stable entrypoint.

That makes the repo feel less like four isolated READMEs and more like one coherent toolchain.

Here is a visual snapshot of that terminal-style demo flow:

<p align="center">
  <img src="docs/assets/agentevalkit-demo-terminal.svg" alt="AgentEvalKit quick demo output" width="100%" />
</p>

## Monorepo structure

```text
projects/
  agentci/    replay-first regression testing
  tracepack/  trace-to-benchmark packaging
  failmap/    failure clustering and release comparison
  packslice/  balanced dataset splitting for trace packs
.github/
  workflows/  monorepo CI
```

If you want to contribute at the monorepo level, start with `CONTRIBUTING.md`.

## Quick start

### AgentCI

```bash
cd projects/agentci
python -m venv .venv
source .venv/bin/activate
pip install -e .
python examples/math_agent.py
agentci diff examples/math_episode.json examples/math_episode_candidate.json
agentci diff-html examples/math_episode.json examples/math_episode_candidate.json examples/math_diff.html
agentci assert-regression examples/math_episode.json examples/math_episode_latency_candidate.json --ignore-diff-prefix metric:latency_ms
agentci detect-flaky examples/math_episode.json examples/math_episode_latency_candidate.json examples/math_episode_candidate.json
# optional: install pytest extra for regression-suite integration
# pip install -e .[pytest]
# pytest -q --agentci-ignore-diff metric:latency_ms
```

### TracePack

```bash
cd projects/tracepack
python -m venv .venv
source .venv/bin/activate
pip install -e .
python examples/make_sample_episodes.py
tracepack scan examples/source_episodes
tracepack build examples/source_episodes examples/demo_pack --only-failures --redact --max-per-signature 1
tracepack inspect examples/demo_pack
tracepack export-jsonl examples/demo_pack examples/demo_pack.jsonl
tracepack export-chat examples/demo_pack examples/demo_chat.jsonl
tracepack scan examples/source_episodes --json
```

### FailMap

```bash
cd projects/failmap
python -m venv .venv
source .venv/bin/activate
pip install -e .
failmap compare examples/baseline_clusters.json examples/candidate_clusters.json examples/compare.json
failmap issue-drafts examples/compare.json examples/issues --rules examples/triage_rules.json
failmap issue-bundle examples/issues examples/bundle
failmap trend examples/trends.json examples/baseline_clusters.json examples/candidate_clusters.json examples/release3_clusters.json
failmap compare-summary examples/compare.json --json
```

### PackSlice

```bash
cd projects/packslice
python -m venv .venv
source .venv/bin/activate
pip install -e .
packslice split examples/sample_pack examples/split_demo --group-by signature
packslice summarize examples/split_demo
packslice markdown examples/split_demo examples/split_demo/REPORT.md
packslice summarize examples/split_demo --json
```

## Why these projects have star potential

High-star Agent infra repos usually win when they are:

1. painkiller products, not toy abstractions
2. compatible with existing stacks
3. easy to demo in under five minutes
4. useful to both researchers and production teams

The projects in this repo are designed around that rule.

## Roadmap

- add more AgentCI integrations and richer HTML diff reports
- strengthen TracePack redaction policies, labeling workflows, and dataset export formats
- add richer FailMap issue templates, trend views, and release-to-release cluster drilldowns
- expand PackSlice with temporal and label-aware slicing
- add more focused projects around agent eval infra, failure mining, and trajectory analytics

## License

MIT
