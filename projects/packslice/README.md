# PackSlice

Balanced dataset slicing for TracePack benchmark packs.

PackSlice takes an existing TracePack pack and turns it into train/eval/test subsets while preserving the distribution of key groups such as failure signature, agent, or model.

## Why this project exists

Once teams collect real traces and build eval packs, they quickly hit another gap:

- how do we create stable train/eval/test slices from the same pack
- how do we avoid one failure signature dominating a split
- how do we keep splits portable enough for CI and dataset workflows

PackSlice focuses on that layer.

## What PackSlice does

- reads a TracePack `manifest.json`
- groups cases by `signature`, `agent_name`, or `model`
- creates balanced `train`, `eval`, and `test` subsets
- copies referenced case files into each split directory
- writes per-split `manifest.json` files plus a top-level `summary.json`
- prints compact split summaries for CI logs
- biases toward split coverage so small signature groups still reach eval and test

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
packslice split examples/sample_pack examples/split_demo --group-by signature --train-ratio 70 --eval-ratio 15 --test-ratio 15
packslice summarize examples/split_demo
packslice markdown examples/split_demo examples/split_demo/REPORT.md
```

## Example output

```text
$ packslice summarize examples/split_demo
Total cases: 6
Group by: signature
Splits:
- train: 2 cases
- eval: 2 cases
- test: 2 cases
```

## CLI

```bash
packslice split path/to/tracepack path/to/output_dir --group-by signature
packslice summarize path/to/output_dir
packslice markdown path/to/output_dir path/to/report.md
```

## Output layout

```text
split_demo/
  summary.json
  train/
    manifest.json
    cases/
  eval/
    manifest.json
    cases/
  test/
    manifest.json
    cases/
```

## Roadmap

- deterministic shuffling with user-provided seeds
- label-aware and success-aware filters
- temporal splits for release-over-release evaluation
- stratified slicing for chat export datasets

## License

MIT
