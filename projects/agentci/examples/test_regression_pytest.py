from pathlib import Path


def test_math_agent_regression(episode_regression):
    root = Path(__file__).parent
    episode_regression.assert_match_files(
        root / "math_episode.json",
        root / "math_episode_latency_candidate.json",
        ignore_diff_prefixes=("metric:latency_ms",),
        check_candidate_replay=True,
    )
