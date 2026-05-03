# Roadmap

`AgentReliabilityKit` is a toolkit for the agent reliability loop:

1. capture real runs
2. replay and diff them
3. package them into reusable eval artifacts
4. cluster recurring failures
5. slice the same evidence into train/eval/test datasets

This roadmap keeps the repo focused on strengthening that loop.

## Near term

### AgentCI

- add more adapters for real agent runtimes
- improve regression diffs for step-level and metric-level debugging
- expand flaky-run detection and replay mismatch reporting

### TracePack

- improve redaction coverage and redaction test cases
- add richer labeling workflows and metadata normalization
- strengthen export formats for eval and fine-tuning pipelines

### FailMap

- improve release-over-release comparisons
- add stronger issue draft templates and routing rules
- expand trend and drilldown reporting for recurring signatures

### PackSlice

- expand label-aware and temporal splitting strategies
- improve reproducibility guarantees for repeated slicing runs
- add stronger diagnostics for split balance and leakage risks

## Cross-tool priorities

- keep JSON artifact contracts stable and explicit
- make root automation outputs easier to consume in CI and dashboards
- improve monorepo demos so visitors can understand the full toolchain in minutes
- add more tests that lock the handoff between tools

## Not the current focus

To keep the repo sharp, it is intentionally not prioritizing:

- generic chat demos
- broad orchestration frameworks
- memory layers unrelated to eval artifacts
- open-ended agent abstractions with no reproducible output contract

## Contribution lens

The highest-value additions usually do at least one of these:

- make one existing tool more useful in a real eval workflow
- improve the handoff between `AgentCI`, `TracePack`, `FailMap`, and `PackSlice`
- make artifact outputs easier to validate, compare, or automate against
