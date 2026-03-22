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
- teams can collect failures, but still lack a simple OSS layer for clustering recurring failure modes and prioritizing fixes

`AgentCode` is a place to build those missing layers as focused OSS projects.

## Projects

### 1. AgentCI

Path: `projects/agentci`

Replay-first regression testing for tool-using LLM agents.

What it does:

- records agent episodes as portable JSON
- replays runs from frozen outputs
- diffs baseline vs candidate trajectories
- validates episodes in CI
- includes experimental adapters for LangGraph-style events and OpenAI Agents-style items

### 2. TracePack

Path: `projects/tracepack`

Build reusable benchmark packs from real agent traces.

What it does:

- scans folders of AgentCI-compatible episodes
- extracts case summaries, tags, and failure signatures
- builds a shareable benchmark pack with a manifest and normalized case files
- helps teams turn production traces into internal eval datasets

### 3. FailMap

Path: `projects/failmap`

Cluster recurring agent failures from TracePack packs.

What it does:

- reads a TracePack `manifest.json`
- groups cases by failure signature and tags
- computes cluster sizes, agents, models, and representative examples
- exports JSON or Markdown reports for triage and roadmap planning

## Toolchain story

```text
AgentCI   -> record and diff trajectories
TracePack -> turn trajectories into reusable benchmark packs
FailMap   -> cluster failures and prioritize what to fix next
```

## Monorepo structure

```text
projects/
  agentci/    replay-first regression testing
  tracepack/  trace-to-benchmark packaging
  failmap/    failure clustering and reporting
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
```

### TracePack

```bash
cd projects/tracepack
python -m venv .venv
source .venv/bin/activate
pip install -e .
python examples/make_sample_episodes.py
tracepack scan examples/source_episodes
tracepack build examples/source_episodes examples/demo_pack --only-failures
tracepack inspect examples/demo_pack
```

### FailMap

```bash
cd projects/failmap
python -m venv .venv
source .venv/bin/activate
pip install -e .
failmap cluster examples/sample_pack examples/clusters.json
failmap summarize examples/clusters.json
failmap markdown examples/clusters.json examples/report.md
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
- add TracePack redaction rules, labeling workflows, and dataset export formats
- add FailMap trend analysis, issue templates, and cluster comparison across releases
- add more focused projects around agent eval infra, failure mining, and trajectory analytics

## License

MIT
