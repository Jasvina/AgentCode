# Contributing to AgentCode

Thanks for checking out `AgentCode`.

This monorepo is intentionally narrow: each project should solve a concrete gap in agent reproducibility, regression testing, failure analysis, or benchmark preparation. Contributions are most useful when they strengthen that end-to-end story instead of adding unrelated demos.

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

For monorepo automation checks, the root demo script is often the fastest way to verify the whole artifact chain:

```bash
chmod +x scripts/run_automation_demo.sh
./scripts/run_automation_demo.sh /tmp/agentcode-demo
```

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

## Testing expectations

Use the smallest useful validation that matches the scope of the change.

Package-level tests:

```bash
cd projects/agentci && python -m unittest discover -s tests -v
cd projects/tracepack && python -m unittest discover -s tests -v
cd projects/failmap && python -m unittest discover -s tests -v
cd projects/packslice && python -m unittest discover -s tests -v
```

End-to-end validation:

```bash
./scripts/run_automation_demo.sh /tmp/agentcode-demo
```

If you change CLI output that is documented in the README, examples, or CI workflow, update those references in the same pull request.

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

## Questions and proposals

If you want to propose a new project for the monorepo, start by describing:

- the missing workflow in today's agent tooling
- why the problem is not already well served by existing OSS
- the minimal artifact contract and CLI that would make it useful
- how it would connect to the rest of `AgentCode`
