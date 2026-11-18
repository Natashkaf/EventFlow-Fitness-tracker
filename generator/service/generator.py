from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from generator.config import Settings
from generator.generation.fitness import BatchGenerator
from generator.repository.base import Repository
from generator.retry import RetryError, RetryPolicy

Clock = Callable[[], datetime]

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(UTC)


class GeneratorService:

    def __init__(
        self,
        *,
        settings: Settings,
        batch_generator: BatchGenerator,
        repository: Repository,
        retry: RetryPolicy,
        stop_event: threading.Event,
        clock: Clock = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._batch_generator = batch_generator
        self._repository = repository
        self._retry = retry
        self._stop_event = stop_event
        self._clock = clock
        self._sleep = sleep
        self._last_batch_started = 0.0

    def run(self) -> None:
        logger.info("Инициализация схемы и справочников...")
        self._repository.ensure_schema()
        self._write_reference_data()
        logger.info(
            "Справочники записаны: устройств %d, городов %d. "
            "Запуск генерации (батч %d записей, интервал %.2fs)",
            len(self._batch_generator.devices),
            len(self._batch_generator.cities),
            self._settings.generator.batch_size,
            self._settings.generator.interval_seconds,
        )

        try:
            while not self._stop_event.is_set():
                self._produce_and_store_batch()
        except RetryError as exc:
            logger.error("Запись данных не удалась: %s", exc)
        finally:
            logger.info("Генератор остановлен.")

    def run_once(self) -> None:
        logger.info("Инициализация схемы и справочников...")
        self._repository.ensure_schema()
        self._write_reference_data()
        self._produce_and_store_batch()
        logger.info("Один батч записан, завершение.")


    def _write_reference_data(self) -> None:
        devices = self._batch_generator.devices
        cities = self._batch_generator.cities
        self._retry.execute(lambda: self._repository.upsert_devices(devices))
        self._retry.execute(lambda: self._repository.upsert_cities(cities))

    def _produce_and_store_batch(self) -> None:
        started = time.monotonic()
        batch = self._batch_generator.generate_batch(
            self._clock(), self._settings.generator.batch_size
        )
        self._retry.execute(lambda: self._repository.insert_workouts(batch))
        anomalies = sum(1 for w in batch if w.is_anomaly)
        logger.debug(
            "Записано %d тренировок (аномалий: %d)", len(batch), anomalies
        )
        self._sleep(self._remaining(started))

    def _remaining(self, started: float) -> float:
        elapsed = time.monotonic() - started
        return max(0.0, self._settings.generator.interval_seconds - elapsed)


def build_service(
    *,
    settings: Settings,
    batch_generator: BatchGenerator,
    repository: Repository,
    stop_event: threading.Event,
) -> GeneratorService:
    retry = RetryPolicy(
        max_attempts=settings.generator.retry_max_attempts,
        base_delay=settings.generator.retry_base_delay_seconds,
        max_delay=settings.generator.retry_max_delay_seconds,
        backoff_factor=settings.generator.retry_backoff_factor,
    )
    return GeneratorService(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        retry=retry,
        stop_event=stop_event,
    )