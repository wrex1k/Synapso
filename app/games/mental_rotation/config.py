"""Mental Rotation game configuration and constants."""

SHAPES: dict[str, list[tuple[int, int]]] = {
    "T1": [(0, 0), (1, 0), (0, 1), (0, 2)],
    "T2": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "T3": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "T4": [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    "T5": [(0, 0), (1, 0), (1, 1), (2, 1), (1, 2)],
    "T6": [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3)],
}

LEVEL_PARAMS: dict[int, dict] = {
    1: {"angle_min": 15, "angle_max": 45, "shape_ids": ["T1", "T2"], "display_ms": 2000, "mirror_prob": 0.10},
    2: {"angle_min": 45, "angle_max": 75, "shape_ids": ["T1", "T2", "T3"], "display_ms": 1800, "mirror_prob": 0.20},
    3: {"angle_min": 75, "angle_max": 105, "shape_ids": ["T1", "T2", "T3", "T4"], "display_ms": 1600, "mirror_prob": 0.30},
    4: {"angle_min": 105, "angle_max": 135, "shape_ids": ["T1", "T2", "T3", "T4", "T5"], "display_ms": 1500, "mirror_prob": 0.40},
    5: {"angle_min": 135, "angle_max": 165, "shape_ids": ["T1", "T2", "T3", "T4", "T5", "T6"], "display_ms": 1400, "mirror_prob": 0.50},
    6: {"angle_min": 165, "angle_max": 180, "shape_ids": ["T1", "T2", "T3", "T4", "T5", "T6"], "display_ms": 1300, "mirror_prob": 0.60},
}

RT_PENALTY_THRESHOLD_PER_LEVEL: dict[int, int] = {
    level: int(params["display_ms"]) for level, params in LEVEL_PARAMS.items()
}


def get_rt_penalty_thresholds() -> dict[int, int]:
    return dict(RT_PENALTY_THRESHOLD_PER_LEVEL)
