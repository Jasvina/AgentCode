# [FailMap] new: failure:tool_call:db_lookup

## Why this matters

- Status: `new`
- Signature: `failure:tool_call:db_lookup`
- Case delta: `0 -> 1 (+1)`

## Representative examples

- Baseline: none
- Candidate: db-timeout-a

## Suggested next steps

- Reproduce one representative failure locally
- Check recent prompt, model, or tool changes touching this path
- Add a targeted regression case to AgentCI / TracePack
- Decide whether this needs an immediate fix or backlog prioritization
