"""
Parse — Structured output parsing for LLM tick results.

The LLM returns JSON matching the TickResult schema. This module:
1. Parses the JSON into a validated Pydantic model
2. Falls back to extracting JSON from markdown code blocks if direct parse fails
3. Returns a TickResult with all the structured data the engine needs

A failed parse is cheap — the system runs continuously, and the next tick
will retry with fresh context. No state is modified on parse failure.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# TickResult Model — The structured output from an LLM tick
# ---------------------------------------------------------------------------


class TickObservation(BaseModel):
    """An observation the LLM made during its review."""
    domain: str = ""
    aspect: str = ""
    observation: str = ""
    significance: str = "noise"  # "noise" | "signal" | "critical"


class TickInsight(BaseModel):
    """A pattern or connection the LLM identified."""
    description: str = ""
    domains: List[str] = Field(default_factory=list)
    confidence: float = 0.5


class TickDecision(BaseModel):
    """A decision the LLM made about what to do."""
    action: str = ""  # "update_expectation" | "notify_user" | "store_question" | "resolve_question" | "no_action"
    target: str = ""
    detail: str = ""
    question_id: Optional[str] = None


class WorldModelUpdate(BaseModel):
    """An update to the world model."""
    domain: str = ""
    aspect: str = ""
    new_description: Optional[str] = None
    new_numeric_value: Optional[float] = None
    reasoning: str = ""


class TickNotification(BaseModel):
    """A notification to surface to the user."""
    message: str = ""
    urgency: str = "low"  # "low" | "medium" | "high"


class NewDormantQuestion(BaseModel):
    """A new dormant question to store."""
    question: str = ""
    domain: str = ""
    resolution_signals: List[str] = Field(default_factory=list)
    context: str = ""


class ResolvedQuestion(BaseModel):
    """A dormant question that was resolved."""
    question_id: str = ""
    resolution: str = ""


class DormantQuestionChanges(BaseModel):
    """Changes to dormant questions."""
    new: List[NewDormantQuestion] = Field(default_factory=list)
    resolved: List[ResolvedQuestion] = Field(default_factory=list)


class TickSummary(BaseModel):
    """Summary of the period for hierarchical memory."""
    content: str = ""
    key_insights: List[str] = Field(default_factory=list)
    key_facts: Dict[str, Any] = Field(default_factory=dict)
    prediction_errors_summary: str = ""


class GoalSuggestion(BaseModel):
    """A suggested goal or sub-goal from the thinking loop."""
    description: str = ""
    domain: str = ""
    time_horizon: str = "week"  # day | week | month | quarter | year
    parent_goal_description: str = ""  # links to existing goal
    reasoning: str = ""


class GoalAnalysis(BaseModel):
    """Structured thought unit analyzing one goal aspect."""
    goal: str = ""
    domain: str = ""
    current_state: str = ""
    whats_stopping_me: str = ""
    whats_inefficient: str = ""
    possibilities: str = ""
    next_action: str = ""
    confidence: float = 0.7


class Discovery(BaseModel):
    """Proactive insight beyond current goals — things the user might not have considered."""
    title: str = ""
    insight: str = ""
    domain: str = ""
    actionable: str = ""
    confidence: float = 0.5


class TickResult(BaseModel):
    """
    The complete structured output from an LLM tick.

    Every field is optional — the LLM includes only what's relevant.
    The engine (Phase C3) reads this to update state.
    """
    observations: List[TickObservation] = Field(default_factory=list)
    insights: List[TickInsight] = Field(default_factory=list)
    decisions: List[TickDecision] = Field(default_factory=list)
    world_model_updates: List[WorldModelUpdate] = Field(default_factory=list)
    narrative: str = ""
    notifications: List[TickNotification] = Field(default_factory=list)
    dormant_questions: DormantQuestionChanges = Field(default_factory=DormantQuestionChanges)
    goal_suggestions: List[GoalSuggestion] = Field(default_factory=list)
    goal_analyses: List[GoalAnalysis] = Field(default_factory=list)
    discoveries: List[Discovery] = Field(default_factory=list)
    summary: Optional[TickSummary] = None


# ---------------------------------------------------------------------------
# Parsing Functions
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised when LLM output cannot be parsed into a TickResult."""
    pass


def parse_tick_result(raw_text: str) -> TickResult:
    """
    Parse LLM output into a TickResult.

    Strategy:
    1. Try direct JSON parse
    2. Try extracting JSON from markdown code blocks
    3. Try extracting JSON from the first { to the last }
    4. Raise ParseError if nothing works

    A parse failure is not catastrophic — the engine will skip this tick
    and retry on the next cycle. No state is modified on failure.
    """
    # 1. Try direct JSON parse
    try:
        data = json.loads(raw_text.strip())
        return TickResult.model_validate(data)
    except (json.JSONDecodeError, Exception):
        pass

    # 2. Try extracting from markdown code blocks
    json_str = _extract_json_from_markdown(raw_text)
    if json_str:
        try:
            data = json.loads(json_str)
            return TickResult.model_validate(data)
        except (json.JSONDecodeError, Exception):
            pass

    # 3. Try extracting from first { to last }
    json_str = _extract_json_braces(raw_text)
    if json_str:
        try:
            data = json.loads(json_str)
            return TickResult.model_validate(data)
        except (json.JSONDecodeError, Exception):
            pass

    raise ParseError(
        f"Could not parse LLM output into TickResult. "
        f"Raw text starts with: {raw_text[:200]!r}"
    )


def _extract_json_from_markdown(text: str) -> Optional[str]:
    """Extract JSON from markdown code blocks (```json ... ``` or ``` ... ```)."""
    # Try ```json ... ``` first
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        match = match.strip()
        if match.startswith("{"):
            return match

    return None


def _extract_json_braces(text: str) -> Optional[str]:
    """Extract JSON by finding the first { and matching last }."""
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]

    return None
