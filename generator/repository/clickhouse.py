"""ClickHouse-реализация репозитория.

Батчевая вставка тренировок одним запросом ``INSERT`` (а не по строке) и
идемпотентная инициализация таблиц при первом запуске. Соединение создаётся
лениво и переиспользуется.

Примечание: материализованные представления и агрегирующие таблицы разбираются
в отдельном воркшопе по ClickHouse, здесь — только таблицы-источники.
"""

from __future__ import annotations

from typing import Any

import clickhouse_connect

from generator.config import ClickHouseSettings
from generator.models import City, Device, Workout

from .base import Repository

_DEVICES_COLUMNS = [
    "device_id",
    "name",
    "platform",
    "model",
    "supports_gps",
    "supports_heart_rate",
]

_CITIES_COLUMNS = [
    "city_id",
    "name",
    "region",
    "country",
    "latitude",
    "longitude",
    "population",
]

_WORKOUTS_COLUMNS = [
    "device_id",
    "city_id",
    "timestamp",
    "duration_seconds",
    "calories",
    "heart_rate",
    "steps",
    "workout_type",
    "is_anomaly",
    "anomaly_kind",
    "distance"
]


class ClickHouseRepository(Repository):
    """Пишет данные в ClickHouse через HTTP-интерфейс (клиент clickhouse-connect)."""

    def __init__(self, settings: ClickHouseSettings) -> None:
        self._settings = settings
        self._client: Any | None = None

    def _conn(self) -> Any:
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._settings.host,
                port=self._settings.port,
                username=self._settings.user,
                password=self._settings.password,
                database=self._settings.database,
            )
        return self._client

    def ensure_schema(self) -> None:
        """Создаёт таблицы, если их ещё нет (идемпотентно)."""
        db = self._settings.database
        self._conn().command(f"CREATE DATABASE IF NOT EXISTS {db}")
        self._conn().command(
            f"""
            CREATE TABLE IF NOT EXISTS {db}.devices (
                device_id UInt32,
                name String,
                platform String,
                model String,
                supports_gps UInt8,
                supports_heart_rate UInt8
            ) ENGINE = MergeTree
            ORDER BY device_id
            """
        )
        self._conn().command(
            f"""
            CREATE TABLE IF NOT EXISTS {db}.cities (
                city_id UInt32,
                name String,
                region String,
                country String,
                latitude Float64,
                longitude Float64,
                population UInt32
            ) ENGINE = MergeTree
            ORDER BY city_id
            """
        )
        self._conn().command(
            f"""
            CREATE TABLE IF NOT EXISTS {db}.workouts (
                device_id UInt32,
                city_id UInt32,
                timestamp DateTime64(3, 'UTC'),
                duration_seconds UInt32,
                calories Float64,
                heart_rate UInt16,
                steps UInt32,
                workout_type String,
                is_anomaly UInt8,
                anomaly_kind String,
                distance_m Float64   
            ) ENGINE = MergeTree
            PARTITION BY toYYYYMM(timestamp)
            ORDER BY (device_id, timestamp)
            """
        )

    def upsert_devices(self, devices: list[Device]) -> None:
        rows = [
            (
                d.device_id,
                d.name,
                d.platform,
                d.model,
                int(d.supports_gps),
                int(d.supports_heart_rate),
            )
            for d in devices
        ]
        if rows:
            self._conn().insert(
                f"{self._settings.database}.devices",
                rows,
                column_names=_DEVICES_COLUMNS,
            )

    def upsert_cities(self, cities: list[City]) -> None:
        rows = [
            (
                c.city_id,
                c.name,
                c.region,
                c.country,
                c.latitude,
                c.longitude,
                c.population,
            )
            for c in cities
        ]
        if rows:
            self._conn().insert(
                f"{self._settings.database}.cities",
                rows,
                column_names=_CITIES_COLUMNS,
            )

    def insert_workouts(self, workouts: list[Workout]) -> None:
        rows = [
            (
                w.device_id,
                w.city_id,
                w.timestamp,
                w.duration_seconds,
                w.calories,
                w.heart_rate,
                w.steps,
                w.workout_type.value,
                int(w.is_anomaly),
                w.anomaly_kind,
                w.distance,
            )
            for w in workouts
        ]
        if rows:
            self._conn().insert(
                f"{self._settings.database}.workouts",
                rows,
                column_names=_WORKOUTS_COLUMNS,
            )