from __future__ import annotations

import math
from typing import Any

from app.games.stroop.config import COLORS


_COLOR_MAP = {c.name.lower(): c.rgb for c in COLORS}

def _clamp01(value: float) -> float:
    """Clamp value to range 0-1."""
    return max(0.0, min(1.0, value))

def _stroop_accuracy(trial: Any) -> float:
    """Calculate accuracy score for Stroop trial with color proximity fallback."""
    is_correct = bool(getattr(trial, "is_correct", False))
    if is_correct:
        return 1.0

    payload = getattr(trial, "scoring_payload", {}) or {}
    correct_color = str(payload.get("correct_color") or "").lower()
    response_color = str(payload.get("response_color") or "").lower()
    if not correct_color or not response_color:
        return 0.0

    if correct_color not in _COLOR_MAP or response_color not in _COLOR_MAP:
        return 0.0

    r1, g1, b1 = _COLOR_MAP[correct_color]
    r2, g2, b2 = _COLOR_MAP[response_color]
    distance = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
    max_distance = math.sqrt(3 * 255 ** 2)
    normalized = min(1.0, distance / max_distance)
    proximity = _clamp01(1.0 - normalized)
    return min(0.20, proximity ** 3)

def _memory_grid_accuracy(trial: Any) -> float:
    """Calculate accuracy score for Memory Grid trial based on hits and false positives."""
    is_correct = bool(getattr(trial, "is_correct", False))
    if is_correct:
        return 1.0

    payload = getattr(trial, "scoring_payload", {}) or {}
    target = max(1, int(payload.get("target_count") or 1))
    hits = max(0, int(payload.get("hits") or 0))
    false_positives = max(0, int(payload.get("false_positives") or 0))

    score = (hits / target) - 0.5 * (false_positives / target)
    return _clamp01(score)

def _mental_rotation_accuracy(trial: Any) -> float:
    """Calculate accuracy score for Mental Rotation trial."""
    is_correct = bool(getattr(trial, "is_correct", False))
    return 1.0 if is_correct else 0.0


_ACCURACY_ADAPTERS = {
    "stroop": _stroop_accuracy,
    "memory_grid": _memory_grid_accuracy,
    "mental_rotation": _mental_rotation_accuracy,
}

def compute_trial_accuracy(game_slug: str, trial: Any) -> float:
    """Compute trial accuracy using game-specific adapter or fallback to binary correctness."""
    adapter = _ACCURACY_ADAPTERS.get(game_slug)
    if adapter is None:
        return 1.0 if bool(getattr(trial, "is_correct", False)) else 0.0
    return adapter(trial)
