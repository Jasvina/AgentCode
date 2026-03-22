from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_manifest(pack_dir: str | Path) -> dict[str, Any]:
    return json.loads((Path(pack_dir) / "manifest.json").read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
