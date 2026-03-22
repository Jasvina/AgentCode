from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentci.adapters import LangGraphEventAdapter, OpenAIAgentsEventAdapter
from agentci.compare import compare_episodes
from agentci.html_report import render_diff_html_report
from agentci.replay import replay_episode
from agentci.schema import Episode
from agentci.trace import EpisodeRecorder


class AgentCITests(unittest.TestCase):
    def _build_episode(self):
        recorder = EpisodeRecorder(
            episode_id="test-episode",
            agent_name="tester",
            model="model-a",
            prompt_version="v1",
            seed=1,
        )
        recorder.model_call("prompt", "response")
        recorder.tool_call("tool", {"x": 1}, {"ok": True})
        return recorder.finish("done", True, {"latency_ms": 1})

    def test_roundtrip_and_replay(self):
        episode = self._build_episode()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "episode.json"
            episode.save(path)
            loaded = type(episode).load(path)
        result = replay_episode(loaded)
        self.assertTrue(result.matched)
        self.assertEqual(loaded.final_output, "done")

    def test_compare_detects_changes(self):
        baseline = self._build_episode()
        candidate = self._build_episode()
        candidate.prompt_version = "v2"
        candidate.final_output = "different"
        diff = compare_episodes(baseline, candidate)
        self.assertTrue(diff.changed)
        self.assertGreaterEqual(len(diff.items), 2)

    def test_html_report_renders_changed_fields(self):
        baseline = self._build_episode()
        candidate = self._build_episode()
        candidate.prompt_version = "v2"
        candidate.final_output = "different"
        html = render_diff_html_report(baseline, candidate)
        self.assertIn("AgentCI HTML diff report", html)
        self.assertIn("prompt_version", html)
        self.assertIn("different", html)

    def test_load_rejects_invalid_episode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.json"
            path.write_text('{"episode_id": "", "agent_name": "", "model": "", "prompt_version": "", "steps": []}')
            with self.assertRaises(ValueError):
                Episode.load(path)

    def test_langgraph_adapter_records_model_and_tool_events(self):
        recorder = EpisodeRecorder("lg", "graph", "demo", "v1")
        adapter = LangGraphEventAdapter(recorder)
        adapter.record_events(
            [
                {
                    "event": "on_chat_model_end",
                    "node": "planner",
                    "data": {"input": "Question", "output": "Use tool"},
                },
                {
                    "event": "on_tool_end",
                    "node": "search_node",
                    "tool_name": "search_docs",
                    "data": {"input": {"query": "agentci"}, "output": {"hits": 3}},
                },
            ]
        )
        episode = recorder.finish("done", True)
        self.assertEqual(episode.steps[0].name, "planner")
        self.assertEqual(episode.steps[1].name, "search_docs")
        self.assertEqual(episode.steps[1].payload["metadata"]["framework"], "langgraph")

    def test_openai_adapter_matches_tool_results_to_calls(self):
        recorder = EpisodeRecorder("oa", "agents", "demo", "v1")
        adapter = OpenAIAgentsEventAdapter(recorder)
        adapter.record_items(
            [
                {
                    "type": "tool_call_item",
                    "call_id": "call-1",
                    "name": "lookup_policy",
                    "arguments": {"topic": "refunds"},
                },
                {
                    "type": "tool_result_item",
                    "call_id": "call-1",
                    "name": "lookup_policy",
                    "output": {"window_days": 14},
                },
                {
                    "type": "message_output_item",
                    "agent": "responder",
                    "content": [{"type": "output_text", "text": "Refunds are allowed."}],
                },
            ],
            prompt="Can I get a refund?",
        )
        episode = recorder.finish("Refunds are allowed.", True)
        self.assertEqual(episode.steps[0].name, "lookup_policy")
        self.assertEqual(episode.steps[0].payload["arguments"], {"topic": "refunds"})
        self.assertEqual(episode.steps[1].name, "responder")


if __name__ == "__main__":
    unittest.main()
