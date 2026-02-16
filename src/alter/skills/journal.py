"""
Journal Skill — Mood, energy, stress, and free-text reflections.

Data sources:
- Manual input (always available)
- Day One / Notion API (future)
- Plain text files (future)

Provides metrics:
    journal.mood      — Self-reported mood (1-10)
    journal.energy    — Self-reported energy level (1-10)
    journal.stress    — Self-reported stress level (1-10)
    journal.gratitude — Number of gratitude items noted

Also captures free-text entries that feed the narrative thread
during LLM ticks (via the "entry" field in raw_data).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from alter.skills.base import Skill, SkillExpectation, SkillInfo, SkillMetric


class JournalSkill(Skill):
    """
    Journal data skill.

    Captures both numeric self-reports (mood, energy, stress) and
    free-text entries. Numeric data feeds the world model via
    prediction errors. Text feeds the LLM during conscious ticks.
    """

    def __init__(self, source: str = "manual") -> None:
        self._source = source
        self._manual_data: Dict[str, Any] = {}

    def info(self) -> SkillInfo:
        return SkillInfo(
            name="journal",
            description="Journal metrics: mood, energy, stress, gratitude, reflections",
            domains=["emotions"],
            metrics=[
                SkillMetric(
                    name="mood", domain="emotions",
                    description="Self-reported mood",
                    unit="1-10", typical_range=(4.0, 8.0),
                ),
                SkillMetric(
                    name="energy", domain="emotions",
                    description="Self-reported energy level",
                    unit="1-10", typical_range=(4.0, 8.0),
                ),
                SkillMetric(
                    name="stress", domain="emotions",
                    description="Self-reported stress level",
                    unit="1-10", typical_range=(2.0, 6.0),
                ),
                SkillMetric(
                    name="gratitude", domain="emotions",
                    description="Number of gratitude items noted",
                    unit="count", typical_range=(0.0, 5.0),
                ),
            ],
        )

    def set_data(self, **data: Any) -> None:
        """Set manual data. Accepts metrics and 'entry' for free-text."""
        self._manual_data.update(data)

    async def collect(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Collect journal data.

        Numeric metrics go into emotions domain for world model comparison.
        Free-text 'entry' is stored separately for LLM context.
        """
        data = {**self._manual_data, **kwargs}
        known = {m.name for m in self.info().metrics}

        # Separate numeric metrics from text entry
        numeric = {k: float(v) for k, v in data.items() if k in known}
        result: Dict[str, Any] = {}

        if numeric:
            result["emotions"] = numeric

        # Free-text entry stored alongside numeric data
        entry = data.get("entry")
        if entry and isinstance(entry, str):
            if "emotions" not in result:
                result["emotions"] = {}
            result["emotions"]["journal_entry"] = entry

        return result

    def bootstrap_expectations(self) -> List[SkillExpectation]:
        return [
            SkillExpectation(
                domain="emotions", aspect="mood",
                description="Typical mood is 6-7 out of 10",
                data_field="mood",
                default_value=6.5, default_range=(6.0, 7.0),
            ),
            SkillExpectation(
                domain="emotions", aspect="energy",
                description="Typical energy level is 5-7 out of 10",
                data_field="energy",
                default_value=6.0, default_range=(5.0, 7.0),
            ),
            SkillExpectation(
                domain="emotions", aspect="stress",
                description="Typical stress level is 3-5 out of 10",
                data_field="stress",
                default_value=4.0, default_range=(3.0, 5.0),
            ),
        ]
