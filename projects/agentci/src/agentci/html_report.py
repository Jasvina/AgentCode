from __future__ import annotations

from html import escape
import json
from pathlib import Path

from .compare import compare_episodes
from .schema import Episode, EpisodeStep


def _pretty_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


def _step_rows(baseline: Episode, candidate: Episode) -> str:
    rows: list[str] = []
    max_steps = max(len(baseline.steps), len(candidate.steps))
    for index in range(max_steps):
        left = baseline.steps[index] if index < len(baseline.steps) else None
        right = candidate.steps[index] if index < len(candidate.steps) else None
        changed = left != right
        rows.append(
            "<tr>"
            f"<td>{index + 1}</td>"
            f"<td>{_render_step(left)}</td>"
            f"<td>{_render_step(right)}</td>"
            f"<td><span class='badge {'changed' if changed else 'same'}'>{'changed' if changed else 'same'}</span></td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_step(step: EpisodeStep | None) -> str:
    if step is None:
        return "<span class='muted'>missing</span>"
    payload = escape(_pretty_json(step.payload))
    return (
        f"<div><strong>{escape(step.kind)}</strong> · <code>{escape(step.name)}</code></div>"
        f"<details><summary>payload</summary><pre>{payload}</pre></details>"
    )


def render_diff_html_report(baseline: Episode, candidate: Episode) -> str:
    diff = compare_episodes(baseline, candidate)
    diff_items = "\n".join(f"<li><code>{escape(item)}</code></li>" for item in diff.items) or "<li>No differences</li>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgentCI Diff Report · {escape(baseline.episode_id)}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0b1020;
      --panel: #131a2a;
      --muted: #8ea0bf;
      --text: #eef4ff;
      --accent: #5cc8ff;
      --warn: #ffb020;
      --border: #263147;
      --same: #1f9d55;
      --changed: #d97706;
      --code: #0f172a;
    }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: linear-gradient(180deg, #0b1020 0%, #111827 100%);
      color: var(--text);
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    .hero {{
      margin-bottom: 24px;
      padding: 24px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(19, 26, 42, 0.92);
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
    }}
    .hero h1, h2, h3 {{ margin-top: 0; }}
    .muted {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin: 20px 0 28px;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      background: rgba(19, 26, 42, 0.92);
    }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .value {{
      font-size: 24px;
      font-weight: 700;
      margin-top: 8px;
    }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    pre {{
      overflow-x: auto;
      padding: 12px;
      border-radius: 12px;
      background: var(--code);
      border: 1px solid var(--border);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 16px;
      border: 1px solid var(--border);
      background: rgba(19, 26, 42, 0.92);
    }}
    th, td {{
      padding: 14px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      text-align: left;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .badge.same {{
      background: rgba(31, 157, 85, 0.18);
      color: #8cf0b3;
    }}
    .badge.changed {{
      background: rgba(217, 119, 6, 0.18);
      color: #ffd08a;
    }}
    details summary {{
      cursor: pointer;
      color: var(--accent);
      margin-top: 8px;
    }}
    ul {{
      padding-left: 20px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="muted">AgentCI HTML diff report</p>
      <h1>{escape(baseline.episode_id)}</h1>
      <p>Compare a baseline agent run against a candidate run before shipping a prompt, model, or tool change.</p>
      <div class="grid">
        <div class="card">
          <div class="label">Changed fields</div>
          <div class="value">{len(diff.items)}</div>
        </div>
        <div class="card">
          <div class="label">Baseline final output</div>
          <div class="value"><code>{escape(baseline.final_output)}</code></div>
        </div>
        <div class="card">
          <div class="label">Candidate final output</div>
          <div class="value"><code>{escape(candidate.final_output)}</code></div>
        </div>
        <div class="card">
          <div class="label">Prompt versions</div>
          <div class="value"><code>{escape(baseline.prompt_version)} → {escape(candidate.prompt_version)}</code></div>
        </div>
      </div>
    </section>

    <section class="hero">
      <h2>Change summary</h2>
      <ul>
        {diff_items}
      </ul>
    </section>

    <section class="hero">
      <h2>Episode metadata</h2>
      <div class="grid">
        <div class="card">
          <div class="label">Agent</div>
          <div class="value">{escape(baseline.agent_name)}</div>
        </div>
        <div class="card">
          <div class="label">Model</div>
          <div class="value">{escape(baseline.model)} → {escape(candidate.model)}</div>
        </div>
        <div class="card">
          <div class="label">Steps</div>
          <div class="value">{len(baseline.steps)} → {len(candidate.steps)}</div>
        </div>
        <div class="card">
          <div class="label">Success</div>
          <div class="value">{baseline.success} → {candidate.success}</div>
        </div>
      </div>
      <div class="grid">
        <div class="card">
          <div class="label">Baseline metrics</div>
          <pre>{escape(_pretty_json(baseline.metrics))}</pre>
        </div>
        <div class="card">
          <div class="label">Candidate metrics</div>
          <pre>{escape(_pretty_json(candidate.metrics))}</pre>
        </div>
      </div>
    </section>

    <section class="hero">
      <h2>Step-by-step comparison</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Baseline</th>
            <th>Candidate</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {_step_rows(baseline, candidate)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def write_diff_html_report(baseline: Episode, candidate: Episode, output_path: str | Path) -> None:
    Path(output_path).write_text(render_diff_html_report(baseline, candidate), encoding="utf-8")
