# Changelog

All notable changes to `AgentReliabilityKit` will be documented in this file.

The project currently tracks a single public line of development on `main`, with GitHub releases used to mark meaningful public milestones in the repo's evolution.

## [0.1.0] - 2026-05-03

Initial public toolkit release for the repo in its current form.

### Added

- clarified monorepo positioning as `AgentReliabilityKit`
- root automation demo with machine-readable `manifest.json`
- GitHub-facing repository docs and community health files
- issue templates, PR template, roadmap, labels, Discussions, funding metadata, and code ownership metadata
- starter issues aligned with the public roadmap

### Included tools

- `AgentCI` for replay-first regression testing
- `TracePack` for trace packaging and redaction-aware eval artifacts
- `FailMap` for failure clustering, comparison, and triage flows
- `PackSlice` for balanced split generation from the same pack

### Notes

This release marks the repo as a coherent public OSS toolchain for agent eval and reliability workflows, not a general-purpose agent framework.
