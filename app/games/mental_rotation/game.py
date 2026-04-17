from __future__ import annotations

import random

from app.games.core.base_game import BaseGame, TrialResult
from app.games.mental_rotation.config import LEVEL_PARAMS, MAX_LEVEL, MIN_LEVEL, SHAPES


class MentalRotationGame(BaseGame):
    def __init__(self, user_id: str):
        super().__init__(
            game_slug="mental_rotation",
            user_id=user_id,
            min_level=MIN_LEVEL,
            max_level=MAX_LEVEL,
        )

    def _level_params(self) -> dict:
        return LEVEL_PARAMS.get(self.level, LEVEL_PARAMS[MIN_LEVEL])

    def start_trial(self) -> dict:
        p = self._level_params()
        shape_id = random.choice(p["shape_ids"])
        rotation_angle = random.randint(int(p["angle_min"]), int(p["angle_max"]))
        mirrored = random.random() < float(p["mirror_prob"])

        correct_key = "f" if mirrored else "k"

        return {
            "shape_id": shape_id,
            "shape_blocks": SHAPES[shape_id],
            "rotation_angle": rotation_angle,
            "mirrored": mirrored,
            "correct_key": correct_key,
            "stimulus_duration": int(p["display_ms"]),
            "level": self.level,
            "trial_index": self.current_trial_index,
            "total_trials": self.total_trials,
            "available_keys": ["k", "f"],
        }

    def get_correct_answer(self, trial_params: dict) -> str:
        return str(trial_params.get("correct_key", "f")).lower()

    def evaluate_trial(
        self,
        trial_params: dict,
        response: str | None,
        reaction_time_ms: float,
    ) -> TrialResult:
        response_key = response.lower() if isinstance(response, str) else None
        correct_key = self.get_correct_answer(trial_params)
        is_correct = response_key == correct_key

        shape_id = str(trial_params.get("shape_id"))
        rotation_angle = int(trial_params.get("rotation_angle", 0))
        mirrored = bool(trial_params.get("mirrored", False))

        result = TrialResult(
            stimulus_params=trial_params,
            response=response_key,
            reaction_time_ms=reaction_time_ms,
            is_correct=is_correct,
            stimulus_payload={
                "shape_id": shape_id,
                "rotation_angle": rotation_angle,
                "mirrored": mirrored,
                "level": trial_params.get("level"),
            },
            response_payload={
                "response_key": response_key,
                "reaction_time_ms": reaction_time_ms,
            },
            scoring_payload={
                "is_correct": is_correct,
                "shape_id": shape_id,
                "rotation_angle": rotation_angle,
                "mirrored": mirrored,
                "correct_key": correct_key,
                "response_key": response_key,
            },
        )

        self.trials.append(result)
        self.current_trial_index += 1
        self._adjust_level()
        return result

    def _adjust_level(self) -> None:
        window = 5
        if len(self.trials) < window:
            return

        recent = self.trials[-window:]
        performance = sum(1 for t in recent if t.is_correct) / window

        if performance >= 0.8 and self.level < self.max_level:
            self.level += 1
        elif performance <= 0.5 and self.level > self.min_level:
            self.level -= 1
