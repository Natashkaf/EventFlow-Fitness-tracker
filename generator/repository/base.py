from __future__ import annotations

from typing import Protocol

from generator.models import City, Device, Workout


class Repository(Protocol):

    def ensure_schema(self) -> None: ...

    def upsert_devices(self, devices: list[Device]) -> None: ...

    def upsert_cities(self, cities: list[City]) -> None: ...

    def upsert_cities(self, cities: list[City]) -> None: ...

    def insert_workouts(self, workouts: list[Workout]) -> None: ...