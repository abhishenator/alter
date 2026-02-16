"""
Calendar Skill — Meetings, focus time, deadlines.

Data sources:
- Manual input (always available)
- Google Calendar API (future)
- Outlook / CalDAV (future)

Provides metrics:
    calendar.meetings       — Number of meetings today
    calendar.meeting_hours  — Total hours in meetings
    calendar.focus_hours    — Uninterrupted focus time blocks (hours)
    calendar.deadlines      — Number of deadlines this week
"""

from __future__ import annotations

from typing import Any, Dict, List

from alter.skills.base import Skill, SkillExpectation, SkillInfo, SkillMetric


class CalendarSkill(Skill):
    """
    Calendar data skill.

    In manual mode, collect() returns data from kwargs or set_data().
    In API mode (future), it would pull from Google Calendar.
    """

    def __init__(self, source: str = "manual") -> None:
        self._source = source
        self._manual_data: Dict[str, float] = {}

    def info(self) -> SkillInfo:
        return SkillInfo(
            name="calendar",
            description="Calendar metrics: meetings, focus time, deadlines",
            domains=["calendar"],
            metrics=[
                SkillMetric(
                    name="meetings", domain="calendar",
                    description="Number of meetings today",
                    unit="count", typical_range=(0.0, 8.0),
                ),
                SkillMetric(
                    name="meeting_hours", domain="calendar",
                    description="Total hours in meetings today",
                    unit="hours", typical_range=(0.0, 6.0),
                ),
                SkillMetric(
                    name="focus_hours", domain="calendar",
                    description="Uninterrupted focus time blocks",
                    unit="hours", typical_range=(1.0, 5.0),
                ),
                SkillMetric(
                    name="deadlines", domain="calendar",
                    description="Deadlines within the week",
                    unit="count", typical_range=(0.0, 5.0),
                ),
            ],
        )

    def set_data(self, **metrics: float) -> None:
        """Set manual data for the next collect() call."""
        self._manual_data.update(metrics)

    async def collect(self, **kwargs: Any) -> Dict[str, Any]:
        """Collect calendar data."""
        data = {**self._manual_data, **kwargs}
        known = {m.name for m in self.info().metrics}
        filtered = {k: float(v) for k, v in data.items() if k in known}
        return {"calendar": filtered} if filtered else {}

    def bootstrap_expectations(self) -> List[SkillExpectation]:
        return [
            SkillExpectation(
                domain="calendar", aspect="meeting_load",
                description="Has 2-4 meetings on a typical workday",
                data_field="meetings",
                default_value=3.0, default_range=(2.0, 4.0),
            ),
            SkillExpectation(
                domain="calendar", aspect="focus_time",
                description="Gets 2-3 hours of uninterrupted focus time daily",
                data_field="focus_hours",
                default_value=2.5, default_range=(2.0, 3.0),
            ),
            SkillExpectation(
                domain="calendar", aspect="meeting_time",
                description="Spends 2-4 hours in meetings on a typical day",
                data_field="meeting_hours",
                default_value=3.0, default_range=(2.0, 4.0),
            ),
        ]
