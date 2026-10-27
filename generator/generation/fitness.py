"""Генератор тренировок для одного устройства."""

from __future__ import annotations

import random
from datetime import datetime

from generator.models import Device, Workout, WorkoutType

from .anomalies import AnomalyKind, AnomalyPolicy
from .catalog import DeviceCatalog
from .metrics import (
    DeviceProfile,
    DurationSampler,
    MetricSampler,
    StepsSampler,
    HeartRateSampler,
    CaloriesSampler,
    WorkoutContext,
)


class WorkoutGenerator:

    def __init__(
            self,
            device: Device,
            profile: DeviceProfile,
            anomaly_policy: AnomalyPolicy,
            rng: random.Random,
    ) -> None:
        self._device = device
        self._rng = rng
        self._anomaly_policy = anomaly_policy
        self._duration: MetricSampler = DurationSampler(profile)
        self._steps: MetricSampler = StepsSampler(profile)
        self._heart_rate: MetricSampler = HeartRateSampler(profile)
        self._calories: MetricSampler = CaloriesSampler(profile)

    @property
    def device(self) -> Device:
        return self._device

    def generate(self, at: datetime) -> Workout:
        anomaly = self._anomaly_policy.decide()
        rng = self._rng

        workout_type = rng.choice(list(WorkoutType))

        ctx = WorkoutContext(at=at, duration_seconds=0, workout_type=workout_type)
        duration = self._duration.sample(ctx, rng)
        duration = self._apply_duration_anomaly(duration, anomaly)

        ctx = WorkoutContext(at=at, duration_seconds=int(duration), workout_type=workout_type)
        steps = self._apply_steps_anomaly(self._steps.sample(ctx, rng), anomaly)
        heart_rate = self._apply_heart_rate_anomaly(self._heart_rate.sample(ctx, rng), anomaly)
        calories = self._apply_calories_anomaly(self._calories.sample(ctx, rng), anomaly)

        return Workout(
            device_id=self._device.device_id,
            timestamp=at,
            workout_type=workout_type,
            duration_seconds=int(duration),
            steps=int(steps),
            heart_rate=int(heart_rate),
            calories=calories,
            is_anomaly=anomaly is not None,
        )


    def _apply_duration_anomaly(
            self, value: float, anomaly: AnomalyKind | None
    ) -> float:
        strength = self._anomaly_policy.strength
        if anomaly == AnomalyKind.INCREASED_ACTIVITY:
            return round(value * strength, 0)
        return value

    def _apply_steps_anomaly(
            self, value: float, anomaly: AnomalyKind | None
    ) -> float:
        strength = self._anomaly_policy.strength
        if anomaly == AnomalyKind.HIGH_STEPS:
            return round(value * strength, 0)
        return value

    def _apply_heart_rate_anomaly(
            self, value: float, anomaly: AnomalyKind | None
    ) -> float:
        strength = self._anomaly_policy.strength
        if anomaly == AnomalyKind.HIGH_HEART :
            return round(value * strength, 0)
        return value

    def _apply_calories_anomaly(
            self, value: float, anomaly: AnomalyKind | None
    ) -> float:
        strength = self._anomaly_policy.strength
        if anomaly == AnomalyKind.HIGH_CALORIES:
            return round(value * strength, 1)
        return value


class BatchGenerator:

    def __init__(self, catalog: DeviceCatalog, seed: int, anomaly_policy: AnomalyPolicy) -> None:
        rng = random.Random(seed)
        self._per_device = [
            WorkoutGenerator(d, catalog.profile_for(d), anomaly_policy, rng)
            for d in catalog.devices()
        ]

    @property
    def devices(self) -> list[Device]:
        return [g.device for g in self._per_device]

    def generate_batch(self, at: datetime, size: int) -> list[Workout]:
        if not self._per_device:
            return []
        workouts: list[Workout] = []
        for index in range(size):
            generator = self._per_device[index % len(self._per_device)]
            workouts.append(generator.generate(at))
        return workouts