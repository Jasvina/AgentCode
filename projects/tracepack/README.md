# TracePack

Build reusable benchmark packs from real agent traces.

TracePack turns folders of AgentCI-compatible episodes into compact eval packs that teams can share internally, version in Git, and feed into later benchmarking pipelines.

## Why this project exists

Most agent teams already collect traces. Very few teams have a clean path from traces to benchmark assets.

Typical missing steps are:

- finding the most representative failures
- summarizing each trajectory into a reusable case
- attaching tags and signatures for later triage
- exporting the result as a portable pack

TracePack focuses on that layer.

## What TracePack does

- scans a directory of episode JSON files
- builds summaries for each trace
- computes a simple failure signature from the last failing step
- exports a benchmark pack with a `manifest.json` and `cases/`
- attaches case labels for downstream triage and analytics
- detects simple sensitive patterns and can recursively redact final outputs, metrics, and nested step payloads during pack build
- exports packs to jsonl for dataset and eval workflows
- exports chat-style jsonl for fine-tuning and evaluator pipelines
- can cap repeated signatures to keep packs diverse with `--max-per-signature`
- supports `--only-failures` for failure-focused packs

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python examples/make_sample_episodes.py
tracepack scan examples/source_episodes
tracepack build examples/source_episodes examples/demo_pack --only-failures --redact
tracepack inspect examples/demo_pack
tracepack export-jsonl examples/demo_pack examples/demo_pack.jsonl
tracepack scan examples/source_episodes --json
```

## Example output

```text
$ tracepack scan examples/source_episodes
Episodes: 3
Successes: 2
Failures: 1
Sensitive: 1
Kinds: model_call=3, note=1, tool_call=3

$ tracepack build examples/source_episodes examples/demo_pack --only-failures --redact
Built pack with 1 cases at examples/demo_pack

$ tracepack scan examples/source_episodes --json
{
  "episode_count": 3,
  "failures": 1,
  "kind_counts": {
    "model_call": 3,
    "note": 1,
    "tool_call": 3
  },
  "sensitive": 1,
  "successes": 2
}
```

## CLI

```bash
tracepack scan path/to/episodes
tracepack build path/to/episodes path/to/pack --only-failures --redact
tracepack build path/to/episodes path/to/pack --only-failures --max-per-signature 3
tracepack inspect path/to/pack
tracepack export-jsonl path/to/pack path/to/output.jsonl
tracepack export-chat path/to/pack path/to/chat.jsonl --success-only
tracepack inspect path/to/pack --json
```

Read-only CLI commands also support `--json` for scripting and CI handoffs.

## Pack layout

```text
pack/
  manifest.json
  cases/
    001-billing-timeout.json
    002-search-loop.json
  # optional export
  demo_pack.jsonl
```

## Roadmap

- stronger redaction policies for nested payloads
- richer label files for human triage
- export formats for eval harnesses and fine-tuning datasets
- better pack balancing and sampling policies
- clustering similar failures across large trace corpora

## License

MIT
