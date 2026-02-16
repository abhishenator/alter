"""
Skill Registry — Registration, discovery, and orchestration.

The registry is the bridge between skills and the consciousness engine.
It knows which skills are installed, can collect data from all of them,
and bootstraps their expectations into the world model.

Usage:
    registry = SkillRegistry()
    registry.register(HealthSkill())
    registry.register(CalendarSkill())

    # Collect data from all skills
    data = await registry.collect_all()
    # data = {"health": {"sleep_hours": 7, ...}, "calendar": {"meetings": 3, ...}}

    # Bootstrap expectations into world model
    expectations = registry.get_all_expectations()
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from alter.skills.base import Skill, SkillExpectation, SkillInfo

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Central registry for all installed skills.

    Owns:
    - Registration and deregistration of skills
    - Collecting data from all skills (or specific ones)
    - Gathering bootstrap expectations from all skills
    - Skill discovery and metadata queries
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill. Replaces any existing skill with the same name."""
        name = skill.name
        if name in self._skills:
            logger.info("Replacing existing skill: %s", name)
        self._skills[name] = skill
        logger.info(
            "Registered skill: %s (domains: %s, metrics: %d)",
            name,
            ", ".join(skill.domains),
            len(skill.info().metrics),
        )

    def unregister(self, name: str) -> Optional[Skill]:
        """Remove a skill by name. Returns the removed skill or None."""
        skill = self._skills.pop(name, None)
        if skill:
            logger.info("Unregistered skill: %s", name)
        return skill

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> List[SkillInfo]:
        """Get metadata for all registered skills."""
        return [s.info() for s in self._skills.values()]

    @property
    def skill_names(self) -> List[str]:
        """Names of all registered skills."""
        return list(self._skills.keys())

    @property
    def domains(self) -> List[str]:
        """All domains covered by registered skills (deduplicated)."""
        all_domains: List[str] = []
        seen: set = set()
        for skill in self._skills.values():
            for d in skill.domains:
                if d not in seen:
                    all_domains.append(d)
                    seen.add(d)
        return all_domains

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    async def collect_all(self) -> Dict[str, Any]:
        """
        Collect data from all registered skills.

        Returns merged daily_data dict:
            {"health": {...}, "calendar": {...}, ...}

        Skills that fail are logged and skipped — one broken skill
        doesn't prevent the others from collecting.
        """
        merged: Dict[str, Any] = {}
        for name, skill in self._skills.items():
            try:
                data = await skill.collect()
                for domain, metrics in data.items():
                    if domain in merged and isinstance(merged[domain], dict) and isinstance(metrics, dict):
                        merged[domain].update(metrics)
                    else:
                        merged[domain] = metrics
            except Exception:
                logger.exception("Skill %s failed to collect data", name)
        return merged

    async def collect_skill(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Collect data from a single skill by name."""
        skill = self._skills.get(name)
        if not skill:
            raise KeyError(f"No skill registered with name: {name!r}")
        return await skill.collect(**kwargs)

    # ------------------------------------------------------------------
    # Bootstrap expectations
    # ------------------------------------------------------------------

    def get_all_expectations(self) -> List[SkillExpectation]:
        """Get bootstrap expectations from all registered skills."""
        expectations: List[SkillExpectation] = []
        for skill in self._skills.values():
            expectations.extend(skill.bootstrap_expectations())
        return expectations

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    async def validate_all(self) -> Dict[str, bool]:
        """Check which skills have valid data sources."""
        results: Dict[str, bool] = {}
        for name, skill in self._skills.items():
            try:
                results[name] = await skill.validate()
            except Exception:
                logger.exception("Skill %s validation failed", name)
                results[name] = False
        return results
