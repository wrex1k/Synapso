"""Memory Grid game configuration and constants."""

LEVEL_PARAMS: dict[int, dict] = {
    1: {"grid_size": 3, "pattern_min": 3, "pattern_max": 5, "display_ms": 1200, "response_ms": 3000, "cluster_factor": 0.0},
    2: {"grid_size": 4, "pattern_min": 5, "pattern_max": 7, "display_ms": 1400, "response_ms": 4200, "cluster_factor": 0.0},
    3: {"grid_size": 5, "pattern_min": 7, "pattern_max": 9, "display_ms": 1800, "response_ms": 5000, "cluster_factor": 0.35},
    4: {"grid_size": 6, "pattern_min": 9, "pattern_max": 12, "display_ms": 2000, "response_ms": 5200, "cluster_factor": 0.50},
    5: {"grid_size": 7, "pattern_min": 11, "pattern_max": 15, "display_ms": 2200, "response_ms": 5400, "cluster_factor": 0.55},
    6: {"grid_size": 8, "pattern_min": 13, "pattern_max": 18, "display_ms": 2400, "response_ms": 5800, "cluster_factor": 0.60},
}

RT_PENALTY_THRESHOLD_PER_LEVEL: dict[int, int] = {
    level: params["response_ms"] for level, params in LEVEL_PARAMS.items()
}


def get_rt_penalty_thresholds() -> dict[int, int]:
    return dict(RT_PENALTY_THRESHOLD_PER_LEVEL)
