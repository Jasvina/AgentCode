from __future__ import annotations

import json
from pathlib import Path


def export_manifest_to_jsonl(pack_dir: str | Path, output_path: str | Path) -> int:
    manifest = json.loads((Path(pack_dir) / "manifest.json").read_text(encoding="utf-8"))
    cases = manifest.get("cases", [])
    target = Path(output_path)
    lines = [json.dumps(case, sort_keys=True) for case in cases]
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(cases)
