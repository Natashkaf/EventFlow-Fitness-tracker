from __future__ import annotations

from generator.models import City, Device, Workout


class InMemoryRepository:

    def __init__(self) -> None:
        self.devices: list[Device] = []
        self.cities: list[City] = []
        self.workouts: list[Workout] = []

    def ensure_schema(self) -> None:...

    def upsert_devices(self, devices: list[Device]) -> None:
        by_id = {d.device_id: d for d in self.devices}
        for device in devices:
            by_id[device.device_id] = device
        self.devices = sorted(by_id.values(), key=lambda d: d.device_id)

    def upsert_cities(self, cities: list[City]) -> None:
        by_id = {c.city_id: c for c in self.cities}
        for city in cities:
            by_id[city.city_id] = city
        self.cities = sorted(by_id.values(), key=lambda c: c.city_id)

    def insert_workouts(self, workouts: list[Workout]) -> None:
        self.workouts.extend(workouts)