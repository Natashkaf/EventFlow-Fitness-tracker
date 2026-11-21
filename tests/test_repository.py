"""Тесты in-memory репозитория: дедупликация справочников и накопление тренировок."""

from datetime import UTC, datetime

from generator.models import City, Device, Workout, WorkoutType
from generator.repository.in_memory import InMemoryRepository


def _device(did: int, name: str, model: str = "X") -> Device:
    return Device(
        device_id=did,
        name=name,
        platform="ios",
        model=model,
        supports_gps=True,
        supports_heart_rate=True,
    )


def _city(cid: int, name: str) -> City:
    return City(
        city_id=cid,
        name=name,
        region="Region",
        country="Russia",
        latitude=0.0,
        longitude=0.0,
        population=1000000,
    )


def _workout(did: int, cid: int, at: datetime) -> Workout:
    return Workout(
        device_id=did,
        city_id=cid,
        timestamp=at,
        duration_seconds=1800,
        calories=300.0,
        heart_rate=140,
        steps=5000,
        distance_m=5000.0,
        workout_type=WorkoutType.RUNNING,
        is_anomaly=False,
        anomaly_kind="none",
    )


def test_upsert_devices_updates_by_id() -> None:
    repo = InMemoryRepository()
    repo.upsert_devices([_device(1, "Phone"), _device(2, "Watch")])
    repo.upsert_devices([_device(1, "Phone", model="NewModel")])

    assert [d.device_id for d in repo.devices] == [1, 2]
    assert repo.devices[0].model == "NewModel"


def test_upsert_cities_updates_by_id() -> None:
    repo = InMemoryRepository()
    repo.upsert_cities([_city(1, "Moscow"), _city(2, "Sochi")])
    repo.upsert_cities([_city(1, "Moscow Updated")])

    assert [c.city_id for c in repo.cities] == [1, 2]
    assert repo.cities[0].name == "Moscow Updated"


def test_insert_workouts_appends_batches() -> None:
    repo = InMemoryRepository()
    at = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)

    repo.insert_workouts([_workout(1, 1, at), _workout(2, 1, at)])
    repo.insert_workouts([_workout(1, 2, at)])

    assert len(repo.workouts) == 3