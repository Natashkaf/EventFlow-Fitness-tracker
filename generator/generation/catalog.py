
from __future__ import annotations

from dataclasses import dataclass

from generator.models import Device

from .metrics import DeviceProfile

_GENERIC = DeviceProfile(
    mean_duration_seconds=2700,
    duration_amplitude_seconds=600,
    mean_steps = 5000,
    steps_amplitude = 500,
    mean_heart_rate= 140,
    heart_rate_amplitude=10
)
@dataclass(frozen=True, slots=True)
class _Template:
    name: str
    platform: str
    model: str
    supports_gps: bool
    supports_heart_rate: bool
    profile: DeviceProfile

_TEMPLATES: dict[str, _Template] = {
    "iPhone 15": _Template(
        "iPhone 15", "ios", "iPhone 15", True, True,
        DeviceProfile(mean_duration_seconds=2700, duration_amplitude_seconds=600, mean_steps=6000, steps_amplitude=400, mean_heart_rate=145, heart_rate_amplitude=8),
    ),
    "Galaxy Watch": _Template(
        "Galaxy Watch", "android",  "Galaxy Watch 6", True, True,
        DeviceProfile(mean_duration_seconds=2700, duration_amplitude_seconds=600, mean_steps=7500, steps_amplitude=600, mean_heart_rate=150, heart_rate_amplitude=12)
    ),
    "Web": _Template(
        "Web", "web", "Chrome", False, False,
        DeviceProfile(mean_duration_seconds=2700, duration_amplitude_seconds=600, mean_steps=0, steps_amplitude=0, mean_heart_rate=0, heart_rate_amplitude=0),
    )
}

class DeviceCatalog:
    def __init__(self, devices: list[str]) -> None:
        self._templates = [self._resolve(i) for i in devices]

    @staticmethod
    def _resolve(device_name: str) -> _Template:
        return _TEMPLATES.get(device_name,_Template(device_name, "unknown", "unknown",  False, False, _GENERIC))


    def devices(self) -> list[Device]:
        return [
            Device(
                device_id=index,
                name=t.name,
                platform=t.platform,
                model=t.model,
                supports_gps=t.supports_gps,
                supports_heart_rate=t.supports_heart_rate,
            )
            for index, t in enumerate(self._templates)
        ]

    def profile_for(self, device: Device) -> DeviceProfile:
        return next(t.profile for t in self._templates if t.name == device.name)

_CITY_TEMPLATES: dict[str, dict] = {
    "Vladivostok": {"region": "Primorsky Krai", "country": "Russia",
                    "latitude": 43.1155, "longitude": 131.8855, "population": 600000},
    "Moscow":      {"region": "Moscow", "country": "Russia",
                    "latitude": 55.7558, "longitude": 37.6173, "population": 12500000},
    "Kazan":       {"region": "Tatarstan", "country": "Russia",
                    "latitude": 55.7963, "longitude": 49.1088, "population": 1250000},
    "Sochi":       {"region": "Krasnodar Krai", "country": "Russia",
                    "latitude": 43.5855, "longitude": 39.7231, "population": 450000},
    "Irkutsk":     {"region": "Irkutsk Oblast", "country": "Russia",
                    "latitude": 52.2870, "longitude": 104.3050, "population": 620000},
}

_DEFAULT_CITY = {"region": "unknown", "country": "unknown",
                 "latitude": 0.0, "longitude": 0.0, "population": 0}


class CityCatalog:

    def __init__(self, city_names: list[str]) -> None:
        self._cities = [
            City(
                city_id=index + 1,
                name=name,
                region=_CITY_TEMPLATES.get(name, _DEFAULT_CITY)["region"],
                country=_CITY_TEMPLATES.get(name, _DEFAULT_CITY)["country"],
                latitude=_CITY_TEMPLATES.get(name, _DEFAULT_CITY)["latitude"],
                longitude=_CITY_TEMPLATES.get(name, _DEFAULT_CITY)["longitude"],
                population=_CITY_TEMPLATES.get(name, _DEFAULT_CITY)["population"],
            )
            for index, name in enumerate(city_names)
        ]

    def cities(self) -> list[City]:
        return list(self._cities)