# FailMap Trend Report

- Snapshots: 3
- Snapshot labels: baseline_clusters, candidate_clusters, release3_clusters
- Tracked signatures: 4

## Latest snapshot summary

- New in latest: 1
- Resolved in latest: 1
- Growing in latest: 0
- Shrinking in latest: 2
- Stable in latest: 0

## Signatures

### failure:model_call:planner

- Trend: `0 -> 0 -> 2`
- Latest status: `new_in_latest`
- Latest count: 2
- Previous count: 0
- Delta vs previous: +2
- Peak count: 2
- First seen: release3_clusters
- Last seen: release3_clusters

### failure:tool_call:web_search

- Trend: `2 -> 3 -> 1`
- Latest status: `shrinking_in_latest`
- Latest count: 1
- Previous count: 3
- Delta vs previous: -2
- Peak count: 3
- First seen: baseline_clusters
- Last seen: release3_clusters

### failure:note:assertion

- Trend: `2 -> 2 -> 1`
- Latest status: `shrinking_in_latest`
- Latest count: 1
- Previous count: 2
- Delta vs previous: -1
- Peak count: 2
- First seen: baseline_clusters
- Last seen: release3_clusters

### failure:tool_call:db_lookup

- Trend: `0 -> 1 -> 0`
- Latest status: `resolved_in_latest`
- Latest count: 0
- Previous count: 1
- Delta vs previous: -1
- Peak count: 1
- First seen: candidate_clusters
- Last seen: candidate_clusters
