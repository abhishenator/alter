"""
Health Skill — Sleep, exercise, heart rate, body metrics.

Data sources:
- Manual input (always available)
- Apple Health export (future)
- Fitbit / Whoop API (future)

Provides metrics:
    health.sleep_hours      — Hours of sleep last night
    health.exercise_minutes — Minutes of exercise today
    health.resting_hr       — Resting heart rate (bpm)
    health.steps            — Step count today
    health.weight           — Body weight (kg)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from alter.skills.base import Skill, SkillExpectation, SkillInfo, SkillMetric


class HealthSkill(Skill):
    """
    Health data skill.

    In manual mode, collect() returns data from a provided dict.
    In API mode (future), it would pull from Apple Health / Fitbit.

    Usage:
        skill = HealthSkill()
        data = await skill.collect(sleep_hours=7, exercise_minutes=30)
        # {"health": {"sleep_hours": 7, "exercise_minutes": 30}}
    """

    def __init__(self, source: str = "manual") -> None:
        self._source = source
        self._manual_data: Dict[str, float] = {}

    def info(self) -> SkillInfo:
        return SkillInfo(
            name="health",
            description="Health metrics: sleep, exercise, heart rate, steps, weight",
            domains=["health"],
            metrics=[
                SkillMetric(
                    name="sleep_hours", domain="health",
                    description="Hours of sleep last night",
                    unit="hours", typical_range=(6.0, 9.0),
                ),
                SkillMetric(
                    name="exercise_minutes", domain="health",
                    description="Minutes of exercise today",
                    unit="minutes", typical_range=(0.0, 120.0),
                ),
                SkillMetric(
                    name="resting_hr", domain="health",
                    description="Resting heart rate",
                    unit="bpm", typical_range=(50.0, 80.0),
                ),
                SkillMetric(
                    name="steps", domain="health",
                    description="Step count today",
                    unit="count", typical_range=(3000.0, 15000.0),
                ),
                SkillMetric(
                    name="weight", domain="health",
                    description="Body weight",
                    unit="kg", typical_range=(50.0, 120.0),
                ),
            ],
        )

    def set_data(self, **metrics: float) -> None:
        """Set manual data for the next collect() call."""
        self._manual_data.update(metrics)

    async def collect(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Collect health data.

        In manual mode, returns data from set_data() + any kwargs.
        kwargs override set_data values.
        """
        data = {**self._manual_data, **kwargs}
        # Filter to only known metric names
        known = {m.name for m in self.info().metrics}
        filtered = {k: float(v) for k, v in data.items() if k in known}
        return {"health": filtered} if filtered else {}

    def bootstrap_expectations(self) -> List[SkillExpectation]:
        return [
            SkillExpectation(
                domain="health", aspect="sleep",
                description="Sleeps 7-8 hours on weeknights",
                data_field="sleep_hours",
                default_value=7.5, default_range=(7.0, 8.0),
            ),
            SkillExpectation(
                domain="health", aspect="exercise",
                description="Exercises 30-60 minutes on workout days",
                data_field="exercise_minutes",
                default_value=45.0, default_range=(30.0, 60.0),
            ),
            SkillExpectation(
                domain="health", aspect="resting_heart_rate",
                description="Resting heart rate around 60-70 bpm",
                data_field="resting_hr",
                default_value=65.0, default_range=(60.0, 70.0),
            ),
            SkillExpectation(
                domain="health", aspect="daily_steps",
                description="Takes 7,000-10,000 steps daily",
                data_field="steps",
                default_value=8000.0, default_range=(7000.0, 10000.0),
            ),
        ]
