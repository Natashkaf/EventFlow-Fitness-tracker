"""Тесты самплеров и генератора тренировок: диапазоны, зависимости от типа, корреляции."""

import random
from datetime import UTC, datetime

from generator.generation.catalog import CityCatalog, DeviceCatalog
from generator.generation.anomalies import AnomalyPolicy
from generator.generation.fitness import BatchGenerator
from generator.models import WorkoutType


def _make_generator(seed: int = 42, anomaly_prob: float = 0.0) -> BatchGenerator:
    devices = ["ios", "android", "watch"]
    cities = ["Moscow", "Sochi"]

    device_catalog = DeviceCatalog(devices)
    city_catalog = CityCatalog(cities)

    policy = AnomalyPolicy(
        probability=anomaly_prob,
        strength=3.0,
        rng=random.Random(seed),
    )
    return BatchGenerator(device_catalog, city_catalog, seed, policy)


def test_heart_rate_in_physiological_range() -> None:
    batch_gen = _make_generator(anomaly_prob=0.0)
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=100)

    for w in workouts:
        assert 40 <= w.heart_rate <= 220, f"Пульс вне диапазона: {w.heart_rate}"


def test_calories_are_positive() -> None:

    batch_gen = _make_generator(anomaly_prob=0.0)
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=50)

    for w in workouts:
        assert w.calories > 0.0, f"Калории <= 0: {w.calories}"


def test_steps_non_negative() -> None:
    batch_gen = _make_generator(anomaly_prob=0.0)
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=50)

    for w in workouts:
        assert w.steps >= 0, f"Отрицательные шаги: {w.steps}"


def test_distance_zero_for_strength_and_yoga() -> None:
    batch_gen = _make_generator(anomaly_prob=0.0)
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=200)

    for w in workouts:
        if w.workout_type in (WorkoutType.STRENGTH, WorkoutType.YOGA):
            assert w.distance_m == 0.0, f"У {w.workout_type} есть дистанция: {w.distance_m}"


def test_distance_positive_for_running_cycling_swimming() -> None:
    batch_gen = _make_generator(anomaly_prob=0.0)
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=200)
    distance_types = (WorkoutType.RUNNING, WorkoutType.CYCLING, WorkoutType.SWIMMING)

    for w in workouts:
        if w.workout_type in distance_types:
            assert w.distance_m > 0.0, f"У {w.workout_type} нет дистанции"


def test_anomaly_kind_is_none_when_not_anomaly() -> None:
    batch_gen = _make_generator(anomaly_prob=0.0)  # выключаем аномалии
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=50)

    for w in workouts:
        assert not w.is_anomaly
        assert w.anomaly_kind == "none"


def test_anomalies_triggered_when_probability_high() -> None:
    batch_gen = _make_generator(anomaly_prob=1.0)  # 100% аномалий
    now = datetime(2024, 6, 15, 12, tzinfo=UTC)

    workouts = batch_gen.generate_batch(now, size=50)

    for w in workouts:
        assert w.is_anomaly is True
        assert w.anomaly_kind != "none", "Аномалия есть, а тип не указан"