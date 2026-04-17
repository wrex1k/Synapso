# Fallback reference reaction times for each game
FALLBACK_REFERENCE_RT: dict[str, int] = {
    "stroop": 700,
    "memory_grid": 1700,
    "mental_rotation": 1300,
}

# Minimum acceptable reaction time floor (35% of reference RT)
RT_FLOOR: dict[str, int] = {
    slug: round(rt * 0.35) for slug, rt in FALLBACK_REFERENCE_RT.items()
}

# K-factor values for PI calculation per game
K_PER_GAME: dict[str, int] = {
    "stroop": 650,
    "memory_grid": 2700,
    "mental_rotation": 1150,
}

# Rating accuracy thresholds for each game
RATING_ACCURACY_THRESHOLDS: dict[str, float] = {
    "stroop": 50.0,
    "memory_grid": 30.0,
    "mental_rotation": 50.0,
}
