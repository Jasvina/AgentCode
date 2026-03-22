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
- supports `--only-failures` for failure-focused packs

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python examples/make_sample_episodes.py
tracepack scan examples/source_episodes
tracepack build examples/source_episodes examples/demo_pack --only-failures
tracepack inspect examples/demo_pack
```

## Example output

```text
$ tracepack scan examples/source_episodes
Episodes: 3
Successes: 2
Failures: 1
Kinds: model_call=5, tool_call=3, note=2

$ tracepack build examples/source_episodes examples/demo_pack --only-failures
Built pack with 1 cases at examples/demo_pack
```

## CLI

```bash
tracepack scan path/to/episodes
tracepack build path/to/episodes path/to/pack --only-failures
tracepack inspect path/to/pack
```

## Pack layout

```text
pack/
  manifest.json
  cases/
    001-billing-timeout.json
    002-search-loop.json
```

## Roadmap

- redaction policies for sensitive payloads
- label files for human triage
- export formats for eval harnesses and fine-tuning datasets
- clustering similar failures across large trace corpora

## License

MIT
