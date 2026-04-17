"""Stroop game configuration and constants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorDef:
    name: str
    rgb: tuple[int, int, int]
    key: str


COLORS: list[ColorDef] = [
    ColorDef("RED", (220, 50, 50), "r"),
    ColorDef("YELLOW", (220, 200, 50), "y"),
    ColorDef("GREEN", (50, 180, 80), "g"),
    ColorDef("BLUE", (50, 100, 220), "b"),
    ColorDef("PURPLE", (150, 60, 200), "p"),
]

COLOR_MAP = {c.name.lower(): c.rgb for c in COLORS}

RT_PENALTY_THRESHOLD_PER_LEVEL = {
    1: 1500,
    2: 1400,
    3: 1300,
    4: 1200,
    5: 1100,
    6: 1000,
}


def get_rt_penalty_thresholds() -> dict[int, int]:
    return dict(RT_PENALTY_THRESHOLD_PER_LEVEL)


NEUTRAL_WORDS = [
    "TABLE", "CHAIR", "HOUSE", "PLATE", "GRASS", "CLOUD", "BRICK", "FLOOR"
]

LEVEL_PARAMS: dict[int, dict] = {
    1: {
        "stimulus_duration": 3000,
        "num_colors": 3,
        "congruent_prob": 0.70,
        "incongruent_prob": 0.15,
        "neutral_prob": 0.15,
    },
    2: {
        "stimulus_duration": 2500,
        "num_colors": 3,
        "congruent_prob": 0.55,
        "incongruent_prob": 0.25,
        "neutral_prob": 0.20,
    },
    3: {
        "stimulus_duration": 2200,
        "num_colors": 4,
        "congruent_prob": 0.45,
        "incongruent_prob": 0.35,
        "neutral_prob": 0.20,
    },
    4: {
        "stimulus_duration": 1800,
        "num_colors": 4,
        "congruent_prob": 0.30,
        "incongruent_prob": 0.45,
        "neutral_prob": 0.25,
    },
    5: {
        "stimulus_duration": 1500,
        "num_colors": 5,
        "congruent_prob": 0.20,
        "incongruent_prob": 0.55,
        "neutral_prob": 0.25,
    },
    6: {
        "stimulus_duration": 1200,
        "num_colors": 5,
        "congruent_prob": 0.15,
        "incongruent_prob": 0.60,
        "neutral_prob": 0.25,
    },
}
