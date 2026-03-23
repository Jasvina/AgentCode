from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from packslice.cli import main as cli_main
from packslice.report import markdown_splits, summarize_splits
from packslice.splitter import split_pack


class PackSliceTests(unittest.TestCase):
    def _write_pack(self, root: Path) -> None:
        cases_dir = root / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        cases = []
        items = [
            ("billing-a", "failure:tool_call:web_search", False),
            ("billing-b", "failure:tool_call:web_search", False),
            ("billing-c", "failure:tool_call:web_search", True),
            ("assert-a", "failure:note:assertion", False),
            ("assert-b", "failure:note:assertion", False),
            ("assert-c", "failure:note:assertion", True),
        ]
        for index, (episode_id, signature, success) in enumerate(items, start=1):
            filename = f"cases/{index:03d}-{episode_id}.json"
            payload = {
                "episode_id": episode_id,
                "agent_name": "demo-agent",
                "model": "demo-model",
                "prompt_version": "v1",
                "success": success,
                "signature": signature,
                "final_output": episode_id,
                "file": filename,
                "labels": [f"signature:{signature.replace(':', '-')}", "status:success" if success else "status:failure"],
                "tags": ["tool_call"],
                "source_path": f"episodes/{index:03d}.json",
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
            "order_by": "episode_id",
            "chronological": False,
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
            "order_by": "episode_id",
            "chronological": True,
            "filters": {"success_mode": "failure-only", "include_labels": ["status:failure"]},
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
        self.assertIn("Chronological", report)

    def test_split_pack_can_filter_labels_and_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "sample_pack"
            root.mkdir()
            self._write_pack(root)
            out = Path(tmpdir) / "splits"
            summary = split_pack(
                root,
                out,
                include_labels=("status:failure",),
                success_mode="failure-only",
                ratios=(1, 1, 1),
            )
            self.assertEqual(summary["total_cases"], 4)
            train_manifest = json.loads((out / "train" / "manifest.json").read_text(encoding="utf-8"))
            all_cases = train_manifest["cases"]
            self.assertTrue(all(case["success"] is False for case in all_cases))

    def test_chronological_split_keeps_ordered_groups(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "sample_pack"
            root.mkdir()
            self._write_pack(root)
            out = Path(tmpdir) / "splits"
            split_pack(root, out, ratios=(1, 1, 1), chronological=True, order_by="source_path")
            train_manifest = json.loads((out / "train" / "manifest.json").read_text(encoding="utf-8"))
            eval_manifest = json.loads((out / "eval" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [case["episode_id"] for case in train_manifest["cases"]],
                ["assert-a", "billing-a"],
            )
            self.assertEqual(
                [case["episode_id"] for case in eval_manifest["cases"]],
                ["assert-b", "billing-b"],
            )

    def test_split_cli_can_emit_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "sample_pack"
            root.mkdir()
            self._write_pack(root)
            out = Path(tmpdir) / "splits"
            output = StringIO()
            with redirect_stdout(output):
                code = cli_main(["split", str(root), str(out), "--group-by", "signature", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["total_cases"], 6)
        self.assertEqual(payload["splits"][0]["name"], "train")

    def test_summarize_cli_can_emit_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "sample_pack"
            root.mkdir()
            self._write_pack(root)
            out = Path(tmpdir) / "splits"
            split_pack(root, out, ratios=(2, 1, 1))
            output = StringIO()
            with redirect_stdout(output):
                code = cli_main(["summarize", str(out), "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["group_by"], "signature")
        self.assertEqual(payload["total_cases"], 6)


if __name__ == "__main__":
    unittest.main()
