from __future__ import annotations

from pathlib import Path

from agentci.adapters import LangGraphEventAdapter
from agentci.trace import EpisodeRecorder


def main() -> None:
    recorder = EpisodeRecorder(
        episode_id="langgraph-demo",
        agent_name="research-graph",
        model="gpt-4.1-mini",
        prompt_version="graph-v1",
        seed=11,
    )
    adapter = LangGraphEventAdapter(recorder)
    adapter.record_events(
        [
            {
                "event": "on_chat_model_end",
                "node": "planner",
                "data": {
                    "input": "Plan how to answer the user question about refunds.",
                    "output": "I should call lookup_policy.",
                    "usage": {"total_tokens": 42},
                },
            },
            {
                "event": "on_tool_end",
                "node": "policy_lookup",
                "tool_name": "lookup_policy",
                "data": {
                    "input": {"topic": "refund window"},
                    "output": {"policy": "Refunds are allowed within 14 days."},
                },
            },
            {
                "event": "on_chat_model_end",
                "node": "responder",
                "data": {
                    "input": "Use the policy result to answer the customer.",
                    "output": "Refunds are available within 14 days of purchase.",
                },
            },
        ]
    )
    episode = recorder.finish(
        final_output="Refunds are available within 14 days of purchase.",
        success=True,
        metrics={"latency_ms": 58, "cost_usd": 0.0008},
    )
    output_path = Path(__file__).with_name("langgraph_episode.json")
    episode.save(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
