"""
Bootstrap — Connect skills to the consciousness engine's world model.

When a skill is first registered, it provides default expectations
(e.g., "sleeps 7-8 hours"). This module creates low-confidence
Expectation objects from those defaults and installs them into the
world model — but only if no expectation exists for that aspect yet.

This is the cold start mechanism: skills declare reasonable defaults,
the engine begins with weak priors, and observation data gradually
strengthens them over 7-14 days.
"""

from __future__ import annotations

import logging
from typing import List

from alter.consciousness.state import Expectation, WorldModel
from alter.skills.base import SkillExpectation
from alter.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


def bootstrap_skills(
    registry: SkillRegistry,
    world_model: WorldModel,
) -> List[Expectation]:
    """
    Bootstrap skill expectations into the world model.

    Only creates expectations that don't already exist (by domain + aspect).
    Returns the list of newly created expectations.

    Args:
        registry: Skill registry with registered skills
        world_model: The engine's world model to populate
    """
    created: List[Expectation] = []

    for skill_exp in registry.get_all_expectations():
        # Skip if the world model already has this expectation
        existing = world_model.get_expectation(skill_exp.domain, skill_exp.aspect)
        if existing:
            logger.debug(
                "Skipping bootstrap for %s.%s — already exists (confidence=%.2f)",
                skill_exp.domain, skill_exp.aspect, existing.confidence,
            )
            continue

        # Create a new low-confidence expectation
        expectation = Expectation(
            domain=skill_exp.domain,
            aspect=skill_exp.aspect,
            description=skill_exp.description,
            numeric_value=skill_exp.default_value,
            numeric_range=skill_exp.default_range,
            data_field=skill_exp.data_field,
            confidence=skill_exp.initial_confidence,
            data_points=0,
        )
        world_model.set_expectation(expectation)
        created.append(expectation)

        logger.info(
            "Bootstrapped expectation: %s.%s = %.1f (confidence=%.2f)",
            skill_exp.domain, skill_exp.aspect,
            skill_exp.default_value, skill_exp.initial_confidence,
        )

    return created
