from __future__ import annotations

import random

from app.games.core.base_game import BaseGame, TrialResult, MIN_LEVEL, MAX_LEVEL
from app.games.stroop.config import COLORS, LEVEL_PARAMS, NEUTRAL_WORDS, ColorDef


class StroopGame(BaseGame):
    """Stroop test implementation with adaptive difficulty and stimulus balancing."""

    MAX_CONSECUTIVE_INCONGRUENT = 2
    MAX_SAME_STIMULUS_RUN = 1
    REROLL_ATTEMPTS = 6

    def __init__(self, user_id: str):
        """Initialize Stroop game with stimulus tracking and difficulty parameters."""
        super().__init__(
            game_slug="stroop",
            user_id=user_id,
            min_level=MIN_LEVEL,
            max_level=MAX_LEVEL,
        )
        self._consecutive_incongruent = 0
        self._last_stimulus_signature: tuple[str, str, str] | None = None
        self._same_stimulus_run = 0

    def _get_level_params(self) -> dict:
        """Return configuration parameters for current difficulty level."""
        return LEVEL_PARAMS.get(self.level, LEVEL_PARAMS[MIN_LEVEL])

    def _available_colors(self) -> list[ColorDef]:
        """Return list of colors available at current difficulty level."""
        num = self._get_level_params()["num_colors"]
        return COLORS[:num]

    def _pick_stimulus_type(self) -> str:
        """Select stimulus type based on level probabilities and consecutive incongruent limit."""
        params = self._get_level_params()

        if self._consecutive_incongruent >= self.MAX_CONSECUTIVE_INCONGRUENT:
            total = params["congruent_prob"] + params["neutral_prob"]
            if total <= 0:
                return "congruent"
            r = random.random() * total
            return "congruent" if r < params["congruent_prob"] else "neutral"

        r = random.random()
        if r < params["congruent_prob"]:
            return "congruent"
        if r < params["congruent_prob"] + params["incongruent_prob"]:
            return "incongruent"
        return "neutral"

    def _generate_stimulus(self, stimulus_type: str) -> dict:
        """Generate stimulus parameters for specified type with random color selection."""
        colors = self._available_colors()
        ink_color = random.choice(colors)

        if stimulus_type == "congruent":
            word = ink_color.name
        elif stimulus_type == "incongruent":
            other_colors = [c for c in colors if c.name != ink_color.name]
            word = random.choice(other_colors).name if other_colors else ink_color.name
        else:
            word = random.choice(NEUTRAL_WORDS)

        return {
            "word": word,
            "ink_color_name": ink_color.name,
            "ink_color_rgb": ink_color.rgb,
            "correct_key": ink_color.key,
            "stimulus_type": stimulus_type,
        }

    def _build_trial_params(self, stimulus: dict) -> dict:
        """Enrich stimulus with level config and trial metadata."""
        params = self._get_level_params()
        return {
            **stimulus,
            "stimulus_duration": params["stimulus_duration"],
            "level": self.level,
            "trial_index": self.current_trial_index,
            "total_trials": self.total_trials,
            "available_keys": [c.key for c in self._available_colors()],
        }

    def _next_stimulus(self, stimulus_type: str) -> dict:
        """Generate stimulus with re-rolling to avoid excessive repetition."""
        stimulus = self._generate_stimulus(stimulus_type)

        for _ in range(self.REROLL_ATTEMPTS - 1):
            sig = self._stimulus_signature(stimulus)
            if sig != self._last_stimulus_signature or self._same_stimulus_run < self.MAX_SAME_STIMULUS_RUN:
                break
            stimulus = self._generate_stimulus(stimulus_type)

        current_sig = self._stimulus_signature(stimulus)
        if current_sig == self._last_stimulus_signature:
            self._same_stimulus_run += 1
        else:
            self._last_stimulus_signature = current_sig
            self._same_stimulus_run = 1

        return stimulus

    def start_trial_with_type(self, stimulus_type: str) -> dict:
        """Generate trial with explicit stimulus type using normal game logic."""
        stimulus = self._next_stimulus(stimulus_type)

        if stimulus_type == "incongruent":
            self._consecutive_incongruent += 1
        else:
            self._consecutive_incongruent = 0

        return self._build_trial_params(stimulus)

    def start_trial(self) -> dict:
        """Generate next trial with automatically selected stimulus type."""
        stimulus_type = self._pick_stimulus_type()
        return self.start_trial_with_type(stimulus_type)

    def get_correct_answer(self, trial_params: dict) -> str:
        """Return the correct key response for given trial."""
        return trial_params["correct_key"]

    def get_key_color_name(self, key: str) -> str | None:
        """Return color name associated with given key."""
        color_map = self.get_key_color_map()
        if key in color_map:
            return color_map[key].name
        return None

    def evaluate_trial(
        self,
        trial_params: dict,
        response: str | None,
        reaction_time_ms: float,
    ) -> TrialResult:
        """Evaluate trial and return result with stimulus, response, and scoring payloads."""
        correct_answer = self.get_correct_answer(trial_params)
        is_correct = response == correct_answer

        correct_color = trial_params.get("ink_color_name")
        response_color = None
        if response:
            response_color = self.get_key_color_name(response)

        stimulus_payload = {
            "trial_index": trial_params.get("trial_index"),
            "stimulus_type": trial_params.get("stimulus_type"),
            "word": trial_params.get("word"),
            "ink_color_name": correct_color.lower() if isinstance(correct_color, str) else None,
        }
        response_payload = {
            "response": response,
            "reaction_time_ms": reaction_time_ms,
        }
        scoring_payload = {
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "correct_color": correct_color.lower() if isinstance(correct_color, str) else None,
            "response_color": response_color.lower() if isinstance(response_color, str) else None,
        }

        result = TrialResult(
            stimulus_params=trial_params,
            response=response,
            reaction_time_ms=reaction_time_ms,
            is_correct=is_correct,
            stimulus_payload=stimulus_payload,
            response_payload=response_payload,
            scoring_payload=scoring_payload,
        )
        self.trials.append(result)
        self.current_trial_index += 1
        self._adjust_level()
        return result

    def begin_run(self):
        """Reset run state and clear stimulus tracking."""
        self._consecutive_incongruent = 0
        self._last_stimulus_signature = None
        self._same_stimulus_run = 0
        super().begin_run()

    @staticmethod
    def _stimulus_signature(stimulus: dict) -> tuple[str, str, str]:
        """Generate unique signature for stimulus deduplication."""
        return (
            str(stimulus.get("word", "")),
            str(stimulus.get("ink_color_name", "")),
            str(stimulus.get("stimulus_type", "")),
        )

    @staticmethod
    def get_key_color_map() -> dict[str, ColorDef]:
        """Return mapping from keyboard keys to color definitions."""
        return {c.key: c for c in COLORS}
