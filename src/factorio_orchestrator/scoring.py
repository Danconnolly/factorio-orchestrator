"""Score conversion deliberately limited to benchmark evaluator output."""
from typing import Any, Mapping


def benchmark_score(result: Mapping[str, Any]) -> float | None:
    if result.get("eligible_for_scoring") is not True:
        return None
    score = result.get("score")
    if not isinstance(score, Mapping) or not isinstance(score.get("score"), (int, float)):
        return None
    return float(score["score"])
