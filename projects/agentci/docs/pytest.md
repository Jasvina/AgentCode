# AgentCI pytest workflow

AgentCI can plug into an existing pytest suite so that agent trajectory regressions fail like ordinary tests.

## Install

```bash
pip install -e .[pytest]
```

The package exposes a pytest plugin entry point:

- fixture: `episode_regression`
- option: `--agentci-ignore-diff PREFIX`

## Minimal example

```python
from pathlib import Path


def test_agent_regression(episode_regression):
    root = Path("examples")
    episode_regression.assert_match_files(
        root / "math_episode.json",
        root / "math_episode_latency_candidate.json",
        ignore_diff_prefixes=("metric:latency_ms",),
    )
```

## What the fixture does

`episode_regression.assert_match_files(...)`:

- loads two episode JSON files
- runs AgentCI diff logic
- optionally replays the candidate episode
- raises a readable assertion if anything changed unexpectedly

`episode_regression.check(...)` returns a structured result instead of raising.

## Global ignores from the CLI

If you want to ignore certain diff prefixes across a whole pytest run:

```bash
pytest -q \
  --agentci-ignore-diff metric:latency_ms \
  --agentci-ignore-diff metric:cost_usd
```

Then your tests can omit `ignore_diff_prefixes`.

## Failure output

A failing assertion includes:

- baseline path
- candidate path
- diff items
- replay mismatches, if any

This is intended to be readable in CI logs without needing a custom dashboard.
