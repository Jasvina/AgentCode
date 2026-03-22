# FailMap Compare Report

- Baseline cases: 4
- Candidate cases: 5
- Cluster count: 3

## Summary

- New: 1
- Resolved: 0
- Growing: 1
- Shrinking: 0
- Unchanged: 1

## failure:tool_call:db_lookup

- Status: new
- Cases: 0 -> 1 (+1)
- Baseline examples: none
- Candidate examples: db-timeout-a

## failure:tool_call:web_search

- Status: growing
- Cases: 2 -> 3 (+1)
- Baseline examples: billing-timeout-a, billing-timeout-b
- Candidate examples: billing-timeout-a, billing-timeout-b, billing-timeout-c
