from __future__ import annotations

import enum
import random


class AnomalyKind(enum.StrEnum):
    INCREASED_ACTIVITY = 'increased_activity' # слишком высокая активность
    DECREASED_ACTIVITY = 'decreased_activity' # слишком низкая активность
    HIGH_HEART = 'high_heart' # высокий пульс
    LOW_HEART = 'low_heart' # низкий пульс
    HIGH_CALORIES = 'high_calories' #запредельно много калорий
    HIGH_STEPS = 'high_steps' # пошел из Москвы во Владивосток

class AnomalyPolicy:
    def __init__(self, probability: float, strength: float, rng: random.Random) -> None:
        self._probability = probability
        self._strength = strength
        self._rng = rng
    @property
    def strength(self) -> float:
        return self._strength

    def decide(self) -> AnomalyKind | None:
        if self._rng.random() >= self._probability:
            return None
        return self._rng.choice(list(AnomalyKind))
