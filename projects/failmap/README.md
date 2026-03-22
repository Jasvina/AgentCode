# FailMap

Cluster recurring agent failures from TracePack packs.

FailMap sits one layer above trace collection: once you already have a portable pack of cases, it helps you answer what is failing repeatedly, which agents and models are involved, and what should be fixed first.

## Why this project exists

Most teams can collect traces. Some teams can turn them into eval packs. Very few teams have a lightweight OSS tool that clusters failure cases into actionable buckets.

FailMap focuses on that missing step.

## What FailMap does

- reads a TracePack `manifest.json`
- groups cases by failure signature
- aggregates tags, agents, models, and representative examples
- exports cluster reports as JSON or Markdown
- keeps the workflow simple enough for CI and team triage

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
failmap cluster examples/sample_pack examples/clusters.json
failmap summarize examples/clusters.json
failmap markdown examples/clusters.json examples/report.md
```

## Example output

```text
$ failmap summarize examples/clusters.json
Clusters: 2
Cases: 4
Top clusters:
- failure:tool_call:web_search (2 cases)
- failure:note:assertion (2 cases)
```

## CLI

```bash
failmap cluster path/to/tracepack path/to/clusters.json
failmap summarize path/to/clusters.json
failmap markdown path/to/clusters.json path/to/report.md
```

## Cluster fields

Each cluster contains:

- `signature`
- `case_count`
- `agents`
- `models`
- `tags`
- `example_episode_ids`
- `example_files`
- `successes`
- `failures`

## Roadmap

- compare clusters across releases
- cluster by semantic similarity in addition to signature
- emit GitHub issue templates for the largest recurring failures
- trend dashboards for eval packs over time

## License

MIT
