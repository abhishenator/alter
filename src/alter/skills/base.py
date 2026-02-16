"""
Skill Base — The interface every skill implements.

A skill is a sense organ. It knows how to:
1. Collect data from an external source (observe)
2. Bootstrap initial expectations into the world model (bootstrap)
3. Declare what domains and data fields it provides (metadata)

Skills produce data in UserModel.daily_data format:
    {"domain": {"metric": value, ...}}

The consciousness engine's observe_daily_data() then compares this
against world model expectations to produce prediction errors.
Skills never produce Observations directly — that's the engine's job.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillMetric:
    """A metric that a skill can provide."""
    name: str                   # "sleep_hours", "exercise_minutes"
    domain: str                 # "health", "calendar", "journal"
    description: str            # "Hours of sleep last night"
    unit: str = ""              # "hours", "minutes", "count", "1-10"
    typical_range: Optional[tuple] = None  # (6.0, 9.0) for sleep_hours


@dataclass
class SkillExpectation:
    """An initial expectation a skill bootstraps into the world model."""
    domain: str
    aspect: str                 # Human-readable: "sleep", "exercise"
    description: str            # NL for LLM: "Sleeps 7-8 hours on weeknights"
    data_field: str             # Maps to daily_data key: "sleep_hours"
    default_value: float        # Starting numeric_value: 7.5
    default_range: Optional[tuple] = None  # Starting numeric_range: (7.0, 8.0)
    initial_confidence: float = 0.1  # Low — hasn't been observed yet


@dataclass
class SkillInfo:
    """Metadata about a skill for registry and discovery."""
    name: str                   # "health", "calendar", "journal"
    description: str            # What this skill perceives
    domains: List[str]          # Life domains it covers
    metrics: List[SkillMetric] = field(default_factory=list)
    version: str = "1.0"


class Skill(ABC):
    """
    Base class for all ALTER skills.

    A skill collects data from an external source and feeds it into
    the consciousness engine via UserModel.daily_data. It also declares
    what metrics it provides and can bootstrap initial world model
    expectations.

    Usage:
        skill = HealthSkill(config={"source": "manual"})
        data = await skill.collect()
        # data = {"health": {"sleep_hours": 7, "exercise_minutes": 30}}
        user_model.record_daily_data({"date": "2026-02-16", **data})
    """

    @abstractmethod
    def info(self) -> SkillInfo:
        """Return metadata about this skill."""
        ...

    @abstractmethod
    async def collect(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Collect current data from this skill's source.

        Returns data in daily_data format:
            {"domain": {"metric": value, ...}}

        This is the skill's core operation. Implementations may read
        from APIs, files, databases, or user input.
        """
        ...

    def bootstrap_expectations(self) -> List[SkillExpectation]:
        """
        Return initial expectations for the world model.

        Called once when a skill is first registered. The engine
        creates low-confidence expectations from these, which
        gradually gain confidence as data accumulates.

        Override this to provide domain-specific defaults.
        """
        return []

    async def validate(self) -> bool:
        """
        Check if this skill's data source is available.

        Returns True if the skill can collect data. Useful for
        checking API keys, file paths, network connectivity, etc.

        Override for skills that need external resources.
        """
        return True

    @property
    def name(self) -> str:
        return self.info().name

    @property
    def domains(self) -> List[str]:
        return self.info().domains
