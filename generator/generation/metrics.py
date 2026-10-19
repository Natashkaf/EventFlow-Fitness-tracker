from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from generator.models import WorkoutType
from .seasonality import annual_factor, diurnal_factor

@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Профиль устройства — «фон» для генерации значений."""

    mean_steps: int
    steps_amplitude: int
    mean_heart_rate: int
    heart_rate_amplitude: int

@dataclass(frozen=True, slots=True)
class WorkoutContext:
    """Контекст для самплеров одной тренировки."""
    at: datetime
    duration_seconds: int
    workout_type: WorkoutType  # ← добавили тип активности

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

class MetricSampler(ABC):
    """Базовый контракт стратегии: вернуть значение метрики для контекста."""

    @abstractmethod
    def sample(self, ctx: WorkoutContext, rng: random.Random) -> float: ...

class StepsSampler(MetricSampler):
    """Шаги зависят от длительности тренировки."""

    def __init__(self, profile: DeviceProfile) -> None:
        self._profile = profile

    def sample(self, ctx: WorkoutContext, rng: random.Random) -> float:
        # Чем дольше тренировка, тем больше шагов
        hours = ctx.duration_seconds / 3600.0
        base = self._profile.mean_steps * hours

        noise = rng.gauss(0.0, self._profile.steps_amplitude)
        return round(base + noise, 0)


class HeartRateSampler(MetricSampler):
    """Пульс зависит от типа тренировки и времени суток."""

    def __init__(self, profile: DeviceProfile) -> None:
        self._profile = profile


    def sample(self, ctx: WorkoutContext, rng: random.Random) -> float:
        # HIIT и бег дают пульс выше, йога — ниже
        type_factor = {
            WorkoutType.HIIT: 1.2,
            WorkoutType.RUNNING: 1.1,
            WorkoutType.CYCLING: 1.0,
            WorkoutType.STRENGTH: 0.9,
            WorkoutType.YOGA: 0.7,
        }.get(ctx.workout_type, 1.0)

        base = (
                       self._profile.mean_heart_rate
                       + self._profile.heart_rate_amplitude * diurnal_factor(ctx.at)
               ) * type_factor

        return round(base + rng.gauss(0.0, self._noise_std), 0)


class CaloriesSampler(MetricSampler):
    """Калории зависят от длительности и типа активности."""

    def __init__(self, profile: DeviceProfile, noise_std: float = 50.0) -> None:
        self._profile = profile
        self._noise_std = noise_std

    def sample(self, ctx: WorkoutContext, rng: random.Random) -> float:
        # Коэффициент сжигания зависит от типа активности
        type_factor = {
            WorkoutType.RUNNING: 10.0,
            WorkoutType.CYCLING: 8.0,
            WorkoutType.SWIMMING: 9.0,
            WorkoutType.STRENGTH: 6.0,
            WorkoutType.YOGA: 3.0,
            WorkoutType.HIIT: 12.0,
        }.get(ctx.workout_type, 8.0)

        # Базовые калории + влияние длительности
        minutes = ctx.duration_seconds / 60.0
        base = (minutes * type_factor)

        return round(base + rng.gauss(0.0, self._noise_std), 1)