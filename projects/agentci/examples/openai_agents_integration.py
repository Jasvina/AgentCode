from __future__ import annotations

from pathlib import Path

from agentci.adapters import OpenAIAgentsEventAdapter
from agentci.trace import EpisodeRecorder


def main() -> None:
    recorder = EpisodeRecorder(
        episode_id="openai-agents-demo",
        agent_name="support-agent",
        model="gpt-4.1-mini",
        prompt_version="agents-v1",
        seed=19,
    )
    adapter = OpenAIAgentsEventAdapter(recorder)
    adapter.record_items(
        [
            {
                "type": "message_output_item",
                "role": "assistant",
                "agent": "triage",
                "content": [
                    {"type": "output_text", "text": "I'll check the refund policy."},
                ],
            },
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
                "status": "ok",
            },
            {
                "type": "message_output_item",
                "role": "assistant",
                "agent": "responder",
                "content": [
                    {"type": "output_text", "text": "You can request a refund within 14 days."},
                ],
            },
        ],
        prompt="Can I get a refund after 10 days?",
    )
    episode = recorder.finish(
        final_output="You can request a refund within 14 days.",
        success=True,
        metrics={"latency_ms": 46, "cost_usd": 0.0006},
    )
    output_path = Path(__file__).with_name("openai_agents_episode.json")
    episode.save(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
