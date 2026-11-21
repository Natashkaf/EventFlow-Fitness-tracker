"""Тесты генерации тренировок и батчей."""

import random
from datetime import UTC, datetime

from generator.generation.anomalies import AnomalyPolicy
from generator.generation.catalog import CityCatalog, DeviceCatalog
from generator.generation.fitness import BatchGenerator
from generator.models import WorkoutType

DEVICES = DeviceCatalog(["ios", "watch"])
CITIES = CityCatalog(["Moscow", "Sochi"])
_AT = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)


def _policy(probability: float = 0.0, seed: int = 42) -> AnomalyPolicy:
    return AnomalyPolicy(probability, strength=3.0, rng=random.Random(seed))


def test_batch_covers_all_devices() -> None:
    generator = BatchGenerator(DEVICES, CITIES, seed=1, anomaly_policy=_policy())
    batch = generator.generate_batch(_AT, size=10)

    assert len(batch) == 10
    assert {w.device_id for w in batch} == {0, 1}


def test_generation_is_reproducible_with_seed() -> None:
    first = BatchGenerator(DEVICES, CITIES, seed=7, anomaly_policy=_policy(seed=7))
    second = BatchGenerator(DEVICES, CITIES, seed=7, anomaly_policy=_policy(seed=7))

    b1 = first.generate_batch(_AT, 5)
    b2 = second.generate_batch(_AT, 5)

    assert [(w.duration_seconds, w.calories, w.steps, w.distance_m) for w in b1] == [
        (w.duration_seconds, w.calories, w.steps, w.distance_m) for w in b2
    ]


def test_every_workout_is_anomaly_when_probability_is_one() -> None:
    generator = BatchGenerator(
        DEVICES, CITIES, seed=2, anomaly_policy=_policy(probability=1.0, seed=2)
    )
    batch = generator.generate_batch(_AT, 20)

    assert all(w.is_anomaly for w in batch)
    assert all(w.anomaly_kind != "none" for w in batch)


def test_no_anomalies_when_probability_is_zero() -> None:
    generator = BatchGenerator(
        DEVICES, CITIES, seed=3, anomaly_policy=_policy(probability=0.0, seed=3)
    )
    batch = generator.generate_batch(_AT, 20)

    assert all(not w.is_anomaly for w in batch)
    assert all(w.anomaly_kind == "none" for w in batch)


def test_workout_type_is_valid_enum() -> None:
    generator = BatchGenerator(DEVICES, CITIES, seed=4, anomaly_policy=_policy())
    batch = generator.generate_batch(_AT, 50)

    assert all(isinstance(w.workout_type, WorkoutType) for w in batch)


def test_empty_catalog_yields_empty_batch() -> None:
    empty_devices = DeviceCatalog([])
    generator = BatchGenerator(empty_devices, CITIES, seed=1, anomaly_policy=_policy())

    assert generator.generate_batch(_AT, 10) == []