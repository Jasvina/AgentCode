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
- compares two cluster snapshots to show which failure modes are new, resolved, growing, or shrinking
- generates issue-ready Markdown drafts for the clusters that need triage
- adds triage metadata such as `priority`, `labels`, and `suggested_owner`
- supports rules-driven routing so teams can map failure signatures and tags to owners and priorities
- builds batch issue bundles grouped by priority and owner for planning meetings or bulk import workflows
- tracks signature trends across multiple releases to show which failures are persisting, growing, or newly appearing
- keeps the workflow simple enough for CI and team triage

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
failmap cluster examples/sample_pack examples/clusters.json
failmap summarize examples/clusters.json
failmap markdown examples/clusters.json examples/report.md
failmap compare examples/baseline_clusters.json examples/candidate_clusters.json examples/compare.json
failmap compare-summary examples/compare.json
failmap compare-markdown examples/compare.json examples/compare.md
failmap issue-drafts examples/compare.json examples/issues --rules examples/triage_rules.json
failmap issue-bundle examples/issues examples/bundle
failmap issue-bundle-summary examples/bundle/bundle.json
failmap trend examples/trends.json examples/baseline_clusters.json examples/candidate_clusters.json examples/release3_clusters.json
failmap trend-summary examples/trends.json
failmap trend-markdown examples/trends.json examples/trends.md
```

## Example output

```text
$ failmap issue-bundle-summary examples/bundle/bundle.json
Drafts: 2
By priority:
- P0: 2
By owner:
- tooling: 2
```

Example metadata emitted into each issue draft:

```yaml
priority: P0
suggested_owner: tooling
labels:
  - failmap
  - status:new
  - priority:P0
```

Example routing rules:

```json
{
  "defaults": {"labels": ["triage:auto"]},
  "rules": [
    {
      "name": "tooling-escalation",
      "match": {"status_in": ["new", "growing"], "tag_in": ["tool_call"]},
      "set": {"owner": "tooling", "priority": "P0", "labels": ["area:tools"]}
    }
  ]
}
```

Example trend summary:

```text
$ failmap trend-summary examples/trends.json
Snapshots: 3
Tracked signatures: 4
Latest snapshot changes:
- new: 1
- resolved: 1
- growing: 0
- shrinking: 2
- stable: 0
```

## CLI

```bash
failmap cluster path/to/tracepack path/to/clusters.json
failmap summarize path/to/clusters.json
failmap markdown path/to/clusters.json path/to/report.md
failmap compare baseline_clusters.json candidate_clusters.json path/to/compare.json
failmap compare-summary path/to/compare.json
failmap compare-markdown path/to/compare.json path/to/report.md
failmap issue-drafts path/to/compare.json path/to/issues_dir --rules path/to/triage_rules.json --status new --status growing
failmap issue-bundle path/to/issues_dir path/to/bundle_dir
failmap issue-bundle-summary path/to/bundle.json
failmap trend path/to/trends.json baseline.json candidate.json release3.json
failmap trend-summary path/to/trends.json
failmap trend-markdown path/to/trends.json path/to/report.md
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

## Compare fields

Each compare report contains:

- `summary` counts for `new`, `resolved`, `growing`, `shrinking`, `unchanged`
- per-cluster `baseline_case_count`, `candidate_case_count`, and `delta`
- representative baseline and candidate episode ids

## Issue draft output

Each generated issue draft includes:

- a ready-to-paste issue title
- the failure signature and status
- case delta between baseline and candidate
- candidate cluster context such as top agents, models, and tags
- representative baseline and candidate examples
- triage metadata: `priority`, `suggested_owner`, `labels`
- matched routing rules, when a rules file is provided
- suggested next steps for triage and regression coverage

## Issue bundle output

Each generated issue bundle includes:

- `bundle.json` with grouped drafts by priority, owner, and status
- `SUMMARY.md` for planning reviews and standups
- compact counts for prioritization and ownership assignment

## Trend report output

Each generated trend report includes:

- ordered snapshots and their labels
- per-signature counts across releases
- latest-release status such as `new_in_latest`, `growing_in_latest`, or `shrinking_in_latest`
- peak counts and first/last seen metadata for prioritization

## Roadmap

- compare clusters across releases
- cluster by semantic similarity in addition to signature
- emit GitHub issue templates for the largest recurring failures
- richer trend dashboards for eval packs over time

## License

MIT
