# Contributing to AgentEvalKit

Thanks for checking out `AgentEvalKit`.

This monorepo is intentionally narrow: each project should solve a concrete gap in agent reproducibility, regression testing, failure analysis, or benchmark preparation. Contributions are most useful when they strengthen that end-to-end story instead of adding unrelated demos.

## Ways to contribute

Useful contributions are not limited to new features. Good pull requests often:

- fix bugs or edge cases in one of the existing CLIs
- improve docs, examples, or quick-start flows for real users
- strengthen tests, CI checks, and reproducibility
- improve how artifacts move between `AgentCI`, `TracePack`, `FailMap`, and `PackSlice`
- add small integrations that make the tools easier to adopt in real agent stacks

## What belongs here

Good additions usually fit at least one of these patterns:

- improve one of the four existing tools: `AgentCI`, `TracePack`, `FailMap`, or `PackSlice`
- make the tools work better together through shared docs, CI, examples, or artifact handoffs
- add integrations that help teams adopt the tools in real agent stacks
- improve reproducibility, testing, packaging, or release readiness

Less useful changes usually look like:

- generic chat demos with no reusable artifact output
- unrelated agent frameworks or memory layers
- one-off examples that are not tested or documented

When in doubt, optimize for sharper scope. A small contribution that makes one existing workflow more reliable is usually a better fit than a broad new abstraction layer.

## Before you start

Before writing code, it helps to align on the kind of change you are making:

- for bug fixes, include a failing test or a concrete reproduction if possible
- for CLI changes, think about both human-readable output and JSON output
- for docs changes, keep the root repo story and the package-level story consistent
- for new features, prefer the smallest artifact contract that is still reusable

If the change is large or introduces a new workflow, open an issue or start a discussion first so the scope stays aligned with the monorepo direction.

## Local setup

The projects are independent Python packages inside one repository.

For package-level work, use an editable install from the project you are changing:

```bash
cd projects/agentci
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Repeat the same pattern for `projects/tracepack`, `projects/failmap`, or `projects/packslice`.

If you want a no-install path for quick experiments, most package commands can also be run with `PYTHONPATH=src python3 -m ...` from the relevant package directory.

For monorepo automation checks, the root demo script is often the fastest way to verify the whole artifact chain:

```bash
chmod +x scripts/run_automation_demo.sh
./scripts/run_automation_demo.sh /tmp/agentevalkit-demo
```

That demo now writes a root `manifest.json` alongside the per-tool artifacts, which is the best single file to inspect when you want to confirm the end-to-end handoff shape.

## Repo layout

```text
projects/agentci    replay-first regression testing
projects/tracepack  trace-to-benchmark packaging
projects/failmap    failure clustering and release comparison
projects/packslice  balanced dataset splitting
docs/               monorepo-level walkthroughs and visuals
scripts/            root automation helpers
.github/workflows/  CI coverage for the monorepo and each package
```

## Development workflow

When making a change:

1. update the relevant package code, docs, and examples together
2. run the package tests for the area you touched
3. run the package CLI example flow if the change affects user-facing behavior
4. run `./scripts/run_automation_demo.sh` if the change affects cross-tool handoffs or root docs
5. keep JSON outputs stable when they are already part of CI or docs

For cross-tool changes, think in terms of handoffs:

- what artifact shape is produced?
- which downstream tool consumes it?
- what docs or examples show that contract?
- what CI assertion should catch regressions later?

## Testing expectations

Use the smallest useful validation that matches the scope of the change.

If you only change prose or visuals, code tests may not be necessary. But if that docs change describes a runnable command, make sure the command still works.

Package-level tests:

```bash
cd projects/agentci && python -m unittest discover -s tests -v
cd projects/tracepack && python -m unittest discover -s tests -v
cd projects/failmap && python -m unittest discover -s tests -v
cd projects/packslice && python -m unittest discover -s tests -v
```

End-to-end validation:

```bash
./scripts/run_automation_demo.sh /tmp/agentevalkit-demo
```

If you change CLI output that is documented in the README, examples, or CI workflow, update those references in the same pull request.

If you change a JSON schema or machine-readable field:

- update tests
- update example outputs or docs that mention the field
- update any root-level automation checks that assert on that field

## Design principles

- prefer portable JSON artifacts over hard-to-parse terminal output
- keep examples runnable in a few minutes on a normal developer machine
- make failures easy to inspect and compare across runs
- document the handoff between tools, not just each tool in isolation
- favor small, composable features over broad framework abstractions

## Pull request checklist

Before opening a PR, check that you:

- describe the user problem solved by the change
- include tests or a concrete validation command
- update docs when commands, files, or output shapes change
- avoid breaking the monorepo automation story unless the PR intentionally revises it
- keep the PR scoped enough that reviewers can understand the artifact story quickly

## Pull request notes

Helpful PR descriptions usually include:

- the workflow before the change
- the workflow after the change
- the commands you ran to validate it
- any JSON or artifact shape changes reviewers should pay attention to

Screenshots, sample command output, or generated artifact snippets are especially helpful when changing reports, docs, or visual assets.

## Questions and proposals

If you want to propose a new project for the monorepo, start by describing:

- the missing workflow in today's agent tooling
- why the problem is not already well served by existing OSS
- the minimal artifact contract and CLI that would make it useful
- how it would connect to the rest of `AgentEvalKit`

The best proposals usually start small: one tight workflow, one useful artifact, one clear CLI, and one obvious connection to the rest of the toolchain.
