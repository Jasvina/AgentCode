---
title: "[FailMap] growing: failure:tool_call:web_search"
priority: P1
suggested_owner: tooling
labels:
  - failmap
  - status:growing
  - priority:P1
  - signature:failure-tool-call-web-search
---

# [FailMap] growing: failure:tool_call:web_search

## Triage metadata

- Priority: `P1`
- Suggested owner: `tooling`
- Labels: `failmap, status:growing, priority:P1, signature:failure-tool-call-web-search`

## Why this matters

- Status: `growing`
- Signature: `failure:tool_call:web_search`
- Case delta: `2 -> 3 (+1)`

## Representative examples

- Baseline: billing-timeout-a, billing-timeout-b
- Candidate: billing-timeout-a, billing-timeout-b, billing-timeout-c

## Suggested next steps

- Reproduce one representative failure locally
- Check recent prompt, model, or tool changes touching this path
- Add a targeted regression case to AgentCI / TracePack
- Decide whether this needs an immediate fix or backlog prioritization
