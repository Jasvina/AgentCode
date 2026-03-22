from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tracepack.builder import build_pack, export_pack_jsonl
from tracepack.scanner import scan_directory


class TracePackTests(unittest.TestCase):
    def _make_episode(self, path: Path, episode_id: str, success: bool) -> None:
        payload = {
            "episode_id": episode_id,
            "agent_name": "demo-agent",
            "model": "demo-model",
            "prompt_version": "v1",
            "success": success,
            "final_output": "ok" if success else "Contact alice@example.com about INV-7 using sk_secret",
            "steps": [
                {"kind": "model_call", "name": "planner", "payload": {"prompt": "p", "response": "r"}},
                {"kind": "tool_call", "name": "tool", "payload": {"arguments": {"x": 1}, "output": {"ok": success}, "status": "ok" if success else "error"}},
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_scan_directory_counts_successes_and_failures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._make_episode(root / 'a.json', 'episode-a', True)
            self._make_episode(root / 'b.json', 'episode-b', False)
            summary = scan_directory(root)
            self.assertEqual(len(summary.episodes), 2)
            self.assertEqual(summary.successes, 1)
            self.assertEqual(summary.failures, 1)
            self.assertTrue(any(item.contains_sensitive for item in summary.episodes))

    def test_build_pack_only_failures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / 'episodes'
            root.mkdir()
            self._make_episode(root / 'a.json', 'episode-a', True)
            self._make_episode(root / 'b.json', 'episode-b', False)
            out = Path(tmpdir) / 'pack'
            summary = build_pack(root, out, only_failures=True, redact=True)
            self.assertEqual(len(summary.episodes), 1)
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['case_count'], 1)
            self.assertTrue(manifest['only_failures'])
            self.assertEqual(manifest['cases'][0]['episode_id'], 'episode-b')
            self.assertTrue(manifest['redacted'])
            self.assertTrue(manifest['cases'][0]['redaction_applied'])
            self.assertIn('[REDACTED_EMAIL]', manifest['cases'][0]['final_output'])
            self.assertIn('labels', manifest['cases'][0])

    def test_export_jsonl_outputs_one_line_per_case(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / 'episodes'
            root.mkdir()
            self._make_episode(root / 'a.json', 'episode-a', True)
            self._make_episode(root / 'b.json', 'episode-b', False)
            out = Path(tmpdir) / 'pack'
            build_pack(root, out, redact=True)
            jsonl_path = Path(tmpdir) / 'pack.jsonl'
            count = export_pack_jsonl(out, jsonl_path)
            self.assertEqual(count, 2)
            lines = jsonl_path.read_text(encoding='utf-8').strip().splitlines()
            self.assertEqual(len(lines), 2)


if __name__ == '__main__':
    unittest.main()
