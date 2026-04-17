"""Mental Rotation game configuration and constants."""

MIN_LEVEL = 1
MAX_LEVEL = 6

SHAPES: dict[str, list[tuple[int, int]]] = {
    "T1": [(0, 0), (1, 0), (0, 1), (0, 2)],
    "T2": [(0, 0), (1, 0), (1, 1), (1, 2)],
    "T3": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "T4": [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    "T5": [(0, 0), (1, 0), (1, 1), (2, 1), (1, 2)],
    "T6": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
}

LEVEL_PARAMS: dict[int, dict] = {
    1: {"angle_min": 0, "angle_max": 30, "shape_ids": ["T1", "T2"], "display_ms": 2000, "mirror_prob": 0.00},
    2: {"angle_min": 30, "angle_max": 60, "shape_ids": ["T1", "T2", "T3"], "display_ms": 1800, "mirror_prob": 0.20},
    3: {"angle_min": 60, "angle_max": 90, "shape_ids": ["T1", "T2", "T3", "T4"], "display_ms": 1600, "mirror_prob": 0.30},
    4: {"angle_min": 90, "angle_max": 120, "shape_ids": ["T1", "T2", "T3", "T4", "T5"], "display_ms": 1400, "mirror_prob": 0.40},
    5: {"angle_min": 120, "angle_max": 150, "shape_ids": ["T1", "T2", "T3", "T4", "T5", "T6"], "display_ms": 1200, "mirror_prob": 0.50},
    6: {"angle_min": 150, "angle_max": 180, "shape_ids": ["T1", "T2", "T3", "T4", "T5", "T6"], "display_ms": 1000, "mirror_prob": 0.60},
}

RT_PENALTY_THRESHOLD_PER_LEVEL: dict[int, int] = {
    level: int(params["display_ms"]) for level, params in LEVEL_PARAMS.items()
}


def get_rt_penalty_thresholds() -> dict[int, int]:
    return dict(RT_PENALTY_THRESHOLD_PER_LEVEL)
