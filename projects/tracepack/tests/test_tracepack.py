from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tracepack.builder import build_pack, export_pack_chat_jsonl, export_pack_jsonl
from tracepack.scanner import scan_directory


class TracePackTests(unittest.TestCase):
    def _make_episode(self, path: Path, episode_id: str, success: bool, final_step_name: str = "tool") -> None:
        payload = {
            "episode_id": episode_id,
            "agent_name": "demo-agent",
            "model": "demo-model",
            "prompt_version": "v1",
            "success": success,
            "final_output": "ok" if success else "Contact alice@example.com about INV-7 using sk_secret",
            "metrics": {
                "trace_owner": "alice@example.com" if not success else "owner@example.com",
            },
            "steps": [
                {"kind": "model_call", "name": "planner", "payload": {"prompt": "p", "response": "r"}},
                {
                    "kind": "tool_call",
                    "name": final_step_name,
                    "payload": {
                        "arguments": {"x": 1, "invoice_id": "INV-7"},
                        "output": {"ok": success, "contact": "alice@example.com"},
                        "status": "ok" if success else "error",
                        "metadata": {"token": "sk_secret"},
                    },
                },
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
            self.assertEqual(
                manifest['cases'][0]['steps'][1]['payload']['output']['contact'],
                '[REDACTED_EMAIL]',
            )
            self.assertEqual(
                manifest['cases'][0]['steps'][1]['payload']['metadata']['token'],
                '[REDACTED_TOKEN]',
            )
            self.assertEqual(
                manifest['cases'][0]['metrics']['trace_owner'],
                '[REDACTED_EMAIL]',
            )

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

    def test_build_pack_can_cap_cases_per_signature(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / 'episodes'
            root.mkdir()
            self._make_episode(root / 'a.json', 'episode-a', False, final_step_name='search')
            self._make_episode(root / 'b.json', 'episode-b', False, final_step_name='search')
            self._make_episode(root / 'c.json', 'episode-c', False, final_step_name='db')
            out = Path(tmpdir) / 'pack'
            summary = build_pack(root, out, only_failures=True, max_per_signature=1)
            self.assertEqual(len(summary.episodes), 2)
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['case_count'], 2)
            self.assertEqual(manifest['max_per_signature'], 1)
            signatures = [case['signature'] for case in manifest['cases']]
            self.assertEqual(signatures.count('failure:tool_call:search'), 1)
            self.assertEqual(signatures.count('failure:tool_call:db'), 1)

    def test_export_chat_jsonl_outputs_messages_and_can_filter_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / 'episodes'
            root.mkdir()
            self._make_episode(root / 'a.json', 'episode-a', True)
            self._make_episode(root / 'b.json', 'episode-b', False)
            out = Path(tmpdir) / 'pack'
            build_pack(root, out, redact=True)
            chat_path = Path(tmpdir) / 'chat.jsonl'
            count = export_pack_chat_jsonl(out, chat_path, success_only=True)
            self.assertEqual(count, 1)
            rows = [json.loads(line) for line in chat_path.read_text(encoding='utf-8').splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['messages'][0]['role'], 'user')
            self.assertEqual(rows[0]['messages'][0]['content'], 'p')
            self.assertEqual(rows[0]['messages'][1]['role'], 'assistant')
            self.assertEqual(rows[0]['metadata']['episode_id'], 'episode-a')


if __name__ == '__main__':
    unittest.main()
