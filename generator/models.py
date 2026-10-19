from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime

class WorkoutType(enum.StrEnum):
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    STRENGTH = "strength"
    YOGA = "yoga"
    HIIT = "hiit"
@dataclass(frozen=True, slots=True)
class Device:
    """Справочная запись устройства (справочник/измерение)."""
    device_id: int
    name: str
    platform: str
    model: str
    supports_gps: bool
    supports_heart_rate: bool


@dataclass(frozen=True, slots=True)
class City:
    """Справочная запись города (справочник/измерение)."""
    city_id: int
    name: str
    region: str
    country: str
    latitude: float
    longitude: float
    population: int

@dataclass(frozen=True, slots=True)
class Workout:
    """Тренировка пользователя в конкретный момент времени (событие).

    Поля:
      * размерности — ``workout_type``, ``device_id``;
      * метрики     — ``duration_seconds``, ``calories``, ``heart_rate``, ``steps``;
      * флаг ``is_anomaly`` помечает редкие выбросы для последующего анализа.
    """

    device_id: int
    timestamp: datetime
    duration_seconds: int
    calories: float
    heart_rate: int
    steps: int
    workout_type: WorkoutType
    is_anomaly: bool