from __future__ import annotations

from pathlib import Path

from agentci.trace import EpisodeRecorder


def add(a: int, b: int) -> int:
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b


def main() -> None:
    recorder = EpisodeRecorder(
        episode_id="math-agent-demo",
        agent_name="toy-math-agent",
        model="demo-model",
        prompt_version="v1",
        seed=7,
    )

    prompt = "Compute (2 + 3) * 4 using tools when useful."
    recorder.model_call(prompt=prompt, response="I should call add, then multiply.")

    add_result = add(2, 3)
    recorder.tool_call("add", {"a": 2, "b": 3}, add_result)

    mul_result = multiply(add_result, 4)
    recorder.tool_call("multiply", {"a": add_result, "b": 4}, mul_result)

    recorder.model_call(prompt="Return the final answer.", response=str(mul_result))
    recorder.note("assertion", {"expected": "20", "actual": str(mul_result)})

    episode = recorder.finish(
        final_output=str(mul_result),
        success=(mul_result == 20),
        metrics={"latency_ms": 31, "cost_usd": 0.0002},
    )

    output_path = Path(__file__).with_name("math_episode.json")
    episode.save(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
