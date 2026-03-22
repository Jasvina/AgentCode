from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from packslice.report import markdown_splits, summarize_splits
from packslice.splitter import split_pack


class PackSliceTests(unittest.TestCase):
    def _write_pack(self, root: Path) -> None:
        cases_dir = root / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        cases = []
        items = [
            ("billing-a", "failure:tool_call:web_search"),
            ("billing-b", "failure:tool_call:web_search"),
            ("billing-c", "failure:tool_call:web_search"),
            ("assert-a", "failure:note:assertion"),
            ("assert-b", "failure:note:assertion"),
            ("assert-c", "failure:note:assertion"),
        ]
        for index, (episode_id, signature) in enumerate(items, start=1):
            filename = f"cases/{index:03d}-{episode_id}.json"
            payload = {
                "episode_id": episode_id,
                "agent_name": "demo-agent",
                "model": "demo-model",
                "prompt_version": "v1",
                "success": False,
                "signature": signature,
                "final_output": episode_id,
                "file": filename,
                "labels": [f"signature:{signature.replace(':', '-')}"],
                "tags": ["tool_call"],
            }
            (root / filename).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            cases.append(payload)

        manifest = {
            "format": "tracepack-v1",
            "case_count": len(cases),
            "cases": cases,
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_split_pack_writes_balanced_split_manifests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "sample_pack"
            root.mkdir()
            self._write_pack(root)
            out = Path(tmpdir) / "splits"
            summary = split_pack(root, out, ratios=(2, 1, 1))
            self.assertEqual(summary["total_cases"], 6)
            train_manifest = json.loads((out / "train" / "manifest.json").read_text(encoding="utf-8"))
            eval_manifest = json.loads((out / "eval" / "manifest.json").read_text(encoding="utf-8"))
            test_manifest = json.loads((out / "test" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(train_manifest["case_count"], 2)
            self.assertEqual(eval_manifest["case_count"], 2)
            self.assertEqual(test_manifest["case_count"], 2)
            train_signatures = [case["signature"] for case in train_manifest["cases"]]
            self.assertEqual(train_signatures.count("failure:tool_call:web_search"), 1)
            self.assertEqual(train_signatures.count("failure:note:assertion"), 1)

    def test_summarize_splits_renders_counts(self):
        payload = {
            "total_cases": 10,
            "group_by": "signature",
            "splits": [
                {"name": "train", "case_count": 7},
                {"name": "eval", "case_count": 2},
                {"name": "test", "case_count": 1},
            ],
        }
        summary = summarize_splits(payload)
        self.assertIn("Total cases: 10", summary)
        self.assertIn("- train: 7 cases", summary)

    def test_markdown_splits_renders_sections(self):
        payload = {
            "total_cases": 6,
            "group_by": "signature",
            "splits": [
                {
                    "name": "train",
                    "case_count": 2,
                    "signatures": [{"signature": "failure:note:assertion", "count": 1}],
                }
            ],
        }
        report = markdown_splits(payload)
        self.assertIn("# PackSlice Report", report)
        self.assertIn("## train", report)
        self.assertIn("failure:note:assertion", report)


if __name__ == "__main__":
    unittest.main()
