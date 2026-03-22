from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from failmap.cluster import build_clusters
from failmap.compare import compare_cluster_files
from failmap.issues import build_issue_bundle, generate_issue_drafts
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

    def test_issue_drafts_are_generated_for_changed_clusters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            compare_payload = {
                "format": "failmap-compare-v1",
                "baseline_case_count": 4,
                "candidate_case_count": 5,
                "cluster_count": 3,
                "summary": {
                    "new": 1,
                    "resolved": 0,
                    "growing": 1,
                    "shrinking": 0,
                    "unchanged": 1,
                },
                "clusters": [
                    {
                        "signature": "failure:tool_call:db_lookup",
                        "status": "new",
                        "baseline_case_count": 0,
                        "candidate_case_count": 1,
                        "delta": 1,
                        "baseline_examples": [],
                        "candidate_examples": ["db-timeout-a"],
                    },
                    {
                        "signature": "failure:tool_call:web_search",
                        "status": "growing",
                        "baseline_case_count": 2,
                        "candidate_case_count": 3,
                        "delta": 1,
                        "baseline_examples": ["billing-timeout-a"],
                        "candidate_examples": ["billing-timeout-a", "billing-timeout-b"],
                    },
                    {
                        "signature": "failure:note:assertion",
                        "status": "unchanged",
                        "baseline_case_count": 2,
                        "candidate_case_count": 2,
                        "delta": 0,
                        "baseline_examples": ["assertion-a"],
                        "candidate_examples": ["assertion-a"],
                    },
                ],
            }
            compare_path = root / "compare.json"
            write_json(compare_path, compare_payload)
            output_dir = root / "issues"
            manifest = generate_issue_drafts(compare_path, output_dir)
            self.assertEqual(manifest["draft_count"], 2)
            issue_files = sorted(path.name for path in output_dir.glob("*.md"))
            self.assertEqual(len(issue_files), 2)
            self.assertTrue(any("new" in name for name in issue_files))
            self.assertTrue(any("growing" in name for name in issue_files))
            self.assertEqual(manifest["drafts"][0]["priority"], "P1")
            self.assertIn("failmap", manifest["drafts"][0]["labels"])
            first_issue = (output_dir / issue_files[0]).read_text(encoding="utf-8")
            self.assertIn("priority:", first_issue)
            self.assertIn("suggested_owner:", first_issue)

    def test_issue_bundle_groups_by_priority_and_owner(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            issues_dir = root / "issues"
            issues_dir.mkdir(parents=True, exist_ok=True)
            manifest = {
                "format": "failmap-issues-v1",
                "source_compare": "compare.json",
                "draft_count": 2,
                "drafts": [
                    {
                        "file": "001-new-tool.md",
                        "title": "[FailMap] new: failure:tool_call:db_lookup",
                        "status": "new",
                        "signature": "failure:tool_call:db_lookup",
                        "priority": "P1",
                        "suggested_owner": "tooling",
                        "labels": ["failmap", "status:new", "priority:P1"],
                    },
                    {
                        "file": "002-growing-assertion.md",
                        "title": "[FailMap] growing: failure:note:assertion",
                        "status": "growing",
                        "signature": "failure:note:assertion",
                        "priority": "P1",
                        "suggested_owner": "evals",
                        "labels": ["failmap", "status:growing", "priority:P1"],
                    },
                ],
            }
            write_json(issues_dir / "manifest.json", manifest)
            bundle_dir = root / "bundle"
            bundle = build_issue_bundle(issues_dir, bundle_dir)
            self.assertEqual(bundle["draft_count"], 2)
            self.assertEqual(bundle["priority_counts"]["P1"], 2)
            self.assertEqual(bundle["owner_counts"]["tooling"], 1)
            summary = (bundle_dir / "SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("# FailMap Issue Bundle", summary)
            self.assertIn("tooling", summary)


if __name__ == "__main__":
    unittest.main()
