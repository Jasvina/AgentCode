from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from failmap.cluster import build_clusters
from failmap.compare import compare_cluster_files
from failmap.io import write_json
from failmap.report import (
    markdown_compare_report,
    markdown_report,
    summarize_clusters,
    summarize_compare,
)


class FailMapTests(unittest.TestCase):
    def _write_pack(self, root: Path) -> None:
        cases_dir = root / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "format": "tracepack-v1",
            "case_count": 3,
            "cases": [
                {
                    "file": "cases/001-a.json",
                    "episode_id": "billing-timeout-a",
                    "agent_name": "billing-agent",
                    "model": "gpt-4.1-mini",
                    "signature": "failure:tool_call:web_search",
                    "tags": ["model_call", "tool_call"],
                    "success": False,
                },
                {
                    "file": "cases/002-b.json",
                    "episode_id": "billing-timeout-b",
                    "agent_name": "billing-agent",
                    "model": "gpt-4.1-mini",
                    "signature": "failure:tool_call:web_search",
                    "tags": ["tool_call"],
                    "success": False,
                },
                {
                    "file": "cases/003-c.json",
                    "episode_id": "assertion-failed",
                    "agent_name": "search-agent",
                    "model": "gpt-4.1",
                    "signature": "failure:note:assertion",
                    "tags": ["note", "tool_call"],
                    "success": False,
                },
            ],
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_build_clusters_groups_by_signature(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_pack(root)
            payload = build_clusters(root)
            self.assertEqual(payload["cluster_count"], 2)
            self.assertEqual(payload["clusters"][0]["signature"], "failure:tool_call:web_search")
            self.assertEqual(payload["clusters"][0]["case_count"], 2)

    def test_reports_render_expected_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_pack(root)
            payload = build_clusters(root)
            summary = summarize_clusters(payload)
            report = markdown_report(payload)
            self.assertIn("Clusters: 2", summary)
            self.assertIn("# FailMap Report", report)
            self.assertIn("## failure:tool_call:web_search", report)

    def test_compare_reports_detect_growing_and_new_clusters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline_root = root / "baseline"
            candidate_root = root / "candidate"
            self._write_pack(baseline_root)
            self._write_pack(candidate_root)

            baseline_payload = build_clusters(baseline_root)
            candidate_payload = build_clusters(candidate_root)
            candidate_payload["clusters"][0]["case_count"] = 3
            candidate_payload["clusters"].append(
                {
                    "signature": "failure:tool_call:db_lookup",
                    "case_count": 1,
                    "successes": 0,
                    "failures": 1,
                    "agents": [{"name": "db-agent", "count": 1}],
                    "models": [{"name": "gpt-4.1-mini", "count": 1}],
                    "tags": [{"name": "tool_call", "count": 1}],
                    "example_episode_ids": ["db-failure-a"],
                    "example_files": ["cases/004-d.json"],
                }
            )

            baseline_path = root / "baseline.json"
            candidate_path = root / "candidate.json"
            write_json(baseline_path, baseline_payload)
            write_json(candidate_path, candidate_payload)

            compare_payload = compare_cluster_files(baseline_path, candidate_path)
            summary = summarize_compare(compare_payload)
            markdown = markdown_compare_report(compare_payload)
            self.assertEqual(compare_payload["summary"]["new"], 1)
            self.assertEqual(compare_payload["summary"]["growing"], 1)
            self.assertIn("growing", summary)
            self.assertIn("# FailMap Compare Report", markdown)
            self.assertIn("failure:tool_call:db_lookup", markdown)


if __name__ == "__main__":
    unittest.main()
