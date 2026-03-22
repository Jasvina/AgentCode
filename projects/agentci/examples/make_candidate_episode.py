from __future__ import annotations

from pathlib import Path

from agentci.schema import Episode


def main() -> None:
    baseline_path = Path(__file__).with_name("math_episode.json")
    candidate_path = Path(__file__).with_name("math_episode_candidate.json")
    latency_candidate_path = Path(__file__).with_name("math_episode_latency_candidate.json")

    episode = Episode.load(baseline_path)
    episode.prompt_version = "v2"
    episode.final_output = "19"
    episode.metrics["latency_ms"] = 34
    episode.steps[3].payload["response"] = "19"
    episode.steps[4].payload["actual"] = "19"

    episode.save(candidate_path)
    print(f"Wrote {candidate_path}")

    latency_candidate = Episode.load(baseline_path)
    latency_candidate.metrics["latency_ms"] = 52
    latency_candidate.save(latency_candidate_path)
    print(f"Wrote {latency_candidate_path}")


if __name__ == "__main__":
    main()
