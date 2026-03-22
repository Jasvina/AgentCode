# AgentCode

[![CI](https://github.com/Jasvina/AgentCode/actions/workflows/ci.yml/badge.svg)](https://github.com/Jasvina/AgentCode/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Jasvina/AgentCode)](LICENSE)
[![Monorepo](https://img.shields.io/badge/layout-agent%20tooling%20monorepo-0a7bbb)](https://github.com/Jasvina/AgentCode)

A public monorepo for practical open-source projects in the LLM Agent stack.

I am deliberately not collecting random demos here. Each project is chosen from a specific gap in the current GitHub landscape: crowded categories already have plenty of frameworks, browser agents, coding agents, and memory layers, so this repo focuses on under-built infrastructure around reproducibility, regression testing, and turning real traces into reusable eval assets.

## Why this repo exists

After surveying today's high-star Agent repositories, three opportunities stood out:

- teams can build agents, but still struggle to replay failures and guard against regressions
- teams can trace agents, but still lack clean tooling to turn real trajectories into reusable eval packs and benchmark cases
- teams can collect failures, but still lack a simple OSS layer for clustering recurring failure modes and prioritizing fixes across releases

`AgentCode` is a place to build those missing layers as focused OSS projects.

## Projects

### 1. AgentCI

Path: `projects/agentci`

Replay-first regression testing for tool-using LLM agents, with portable episode traces, HTML diff reports, and pytest-friendly regression assertions.

### 2. TracePack

Path: `projects/tracepack`

Build reusable benchmark packs from real agent traces, with lightweight redaction, case labels, jsonl export, and signature-aware sampling for eval pipelines.

### 3. FailMap

Path: `projects/failmap`

Cluster recurring agent failures from TracePack packs, compare releases, generate issue-ready triage drafts with rules-driven routing, bundle them for planning, and track failure trends across snapshots.

## Toolchain story

```text
AgentCI   -> record and diff trajectories
TracePack -> turn trajectories into reusable benchmark packs
FailMap   -> cluster failures, compare releases, generate triage issues, bundle work
```

## Monorepo structure

```text
projects/
  agentci/    replay-first regression testing
  tracepack/  trace-to-benchmark packaging
  failmap/    failure clustering and release comparison
.github/
  workflows/  monorepo CI
```

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
- add more focused projects around agent eval infra, failure mining, and trajectory analytics

## License

MIT
