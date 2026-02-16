"""
Context Assembly — Builds the right context for each tick type.

This is WHERE ALTER's intelligence lives. The LLM can only think about
what's in context. Assembling the right information — not too much,
not too little — determines the quality of every thought.

The assembler reads from three sources:
    - ConsciousnessState (observations, world model, narrative, dormant questions)
    - UserModel (goals, purpose, personality, daily data)
    - Constitution (principles, domains)

Each tick type gets a different "view" of the user's life:
    - Daily:   raw recent data, focused on today
    - Weekly:  daily summaries, cross-domain synthesis
    - Monthly: weekly summaries, purpose + identity review
    - Urgent:  focused on the triggering domain only
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from alter.consciousness.config import TickType, TOKEN_BUDGETS
from alter.consciousness.state import (
    ConsciousnessState,
    DormantQuestion,
    Expectation,
    Observation,
    Summary,
    WorldModel,
)


# ---------------------------------------------------------------------------
# Token Estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """
    Fast token estimate: ~4 characters per token.

    Used during assembly for budget enforcement. Exact counting
    happens once, right before the API call (Phase C3).
    """
    return max(1, len(text) // 4)



# ---------------------------------------------------------------------------
# Section Formatters
# ---------------------------------------------------------------------------


def format_narrative(narrative: str) -> str:
    """Format the narrative thread for context."""
    if not narrative:
        return "No narrative established yet. This is early in our understanding of this person."
    return narrative


def format_world_model(world_model: WorldModel, domains: Optional[List[str]] = None) -> str:
    """Format world model expectations for context."""
    if not world_model.expectations:
        return "No expectations formed yet."

    lines = []
    target_domains = domains or list(world_model.expectations.keys())

    for domain in target_domains:
        expectations = world_model.expectations.get(domain, [])
        if not expectations:
            continue
        lines.append(f"### {domain.title()}")
        for exp in expectations:
            conf_pct = f"{exp.confidence * 100:.0f}%"
            line = f"- {exp.description} (confidence: {conf_pct})"
            if exp.numeric_value is not None:
                line += f" [numeric: {exp.numeric_value}"
                if exp.numeric_range:
                    line += f", range: {exp.numeric_range[0]}-{exp.numeric_range[1]}"
                line += "]"
            lines.append(line)

    return "\n".join(lines) if lines else "No expectations formed yet."


def format_observations(observations: List[Observation]) -> str:
    """Format observations for context."""
    if not observations:
        return "No observations in this period."

    lines = []
    for obs in observations:
        severity_marker = ""
        if obs.severity == "elevated":
            severity_marker = " [ELEVATED]"
        elif obs.severity == "critical":
            severity_marker = " [CRITICAL]"

        lines.append(f"- [{obs.timestamp[:16]}] {obs.summary}{severity_marker}")

    return "\n".join(lines)


def format_dormant_questions(questions: List[DormantQuestion]) -> str:
    """Format dormant questions for context."""
    if not questions:
        return "No unresolved questions."

    lines = []
    for q in questions:
        readiness_pct = f"{q.readiness * 100:.0f}%"
        lines.append(f"- [{q.id}] {q.question} (readiness: {readiness_pct}, domain: {q.domain})")
        if q.resolution_signals:
            lines.append(f"  Signals: {', '.join(q.resolution_signals)}")

    return "\n".join(lines)


def format_ready_questions(questions: List[DormantQuestion]) -> str:
    """Format questions that have crossed the readiness threshold.

    These questions have accumulated enough evidence to attempt resolution.
    They are presented with higher urgency than regular dormant questions.
    """
    if not questions:
        return ""

    lines = [
        "The following questions have accumulated enough evidence to answer.",
        "Attempt to resolve them based on the available data.\n",
    ]
    for q in questions:
        readiness_pct = f"{q.readiness * 100:.0f}%"
        lines.append(f"- [{q.id}] {q.question} (readiness: {readiness_pct})")
        if q.context:
            lines.append(f"  Context: {q.context}")
        if q.resolution_signals:
            lines.append(f"  Signals: {', '.join(q.resolution_signals)}")

    return "\n".join(lines)


def format_goals(goals: List[Dict[str, Any]], active_only: bool = True) -> str:
    """Format goals for context."""
    if not goals:
        return "No goals set."

    filtered = goals
    if active_only:
        filtered = [g for g in goals if g.get("status") == "active"]

    if not filtered:
        return "No active goals."

    lines = []
    for g in filtered:
        line = f"- [{g.get('time_horizon', '?')}] {g.get('description', '?')} ({g.get('domain', '?')})"
        if g.get("status") != "active":
            line += f" — {g['status']}"
        lines.append(line)

    return "\n".join(lines)


def format_summaries(summaries: List[Summary]) -> str:
    """Format summaries for context."""
    if not summaries:
        return "No summaries available for this period."

    lines = []
    for s in summaries:
        lines.append(f"### {s.period_label}")
        lines.append(s.content)
        if s.key_insights:
            lines.append("Key insights:")
            for insight in s.key_insights:
                lines.append(f"  - {insight}")
        if s.prediction_errors_summary:
            lines.append(f"Prediction errors: {s.prediction_errors_summary}")
        lines.append("")  # blank line between summaries

    return "\n".join(lines)


def format_principles(principles: List[Dict[str, Any]], summary_only: bool = False) -> str:
    """Format constitution principles for context."""
    if not principles:
        return "No principles defined."

    lines = []
    for p in principles:
        if summary_only:
            lines.append(f"- {p.get('name', p.get('id', '?'))}: {p.get('description', '')}")
        else:
            lines.append(f"### {p.get('name', p.get('id', '?'))} (weight: {p.get('weight', '?')})")
            lines.append(p.get("description", ""))
            for rule in p.get("rules", []):
                lines.append(f"  - {rule}")
            lines.append("")

    return "\n".join(lines)


def format_personality(traits: Dict[str, int], preferences: Dict[str, Any]) -> str:
    """Format personality traits and preferences."""
    lines = []
    if traits:
        lines.append("Personality traits:")
        for trait, score in traits.items():
            lines.append(f"  - {trait}: {score}/10")
    if preferences:
        lines.append("Preferences:")
        for key, val in preferences.items():
            lines.append(f"  - {key}: {val}")
    return "\n".join(lines) if lines else "No personality data yet."


def format_purpose_history(purpose: Optional[str], history: List[Dict[str, Any]]) -> str:
    """Format purpose statement and its evolution."""
    lines = []
    if purpose:
        lines.append(f"Current purpose: {purpose}")
    if history:
        lines.append("\nPurpose evolution:")
        for entry in history[-5:]:  # Last 5 changes
            lines.append(f"  - [{entry.get('set_at', '?')}] {entry.get('statement', '?')}")
    return "\n".join(lines) if lines else "No purpose defined yet."


# ---------------------------------------------------------------------------
# Context Section — A unit of context with priority and token estimate
# ---------------------------------------------------------------------------


class ContextSection:
    """
    A section of context with a priority level.

    During assembly, sections are added in priority order. If the token
    budget is exceeded, lower-priority sections are dropped.
    """

    def __init__(self, name: str, header: str, content: str, priority: int):
        """
        Args:
            name: Section identifier (e.g., "narrative", "world_model")
            header: Markdown header for this section (e.g., "## Current Narrative")
            content: The formatted content
            priority: 1 = highest (always include), 10 = lowest (drop first)
        """
        self.name = name
        self.header = header
        self.content = content
        self.priority = priority

    @property
    def token_estimate(self) -> int:
        return estimate_tokens(self.full_text)

    @property
    def full_text(self) -> str:
        return f"{self.header}\n{self.content}"


# ---------------------------------------------------------------------------
# Context Assembler
# ---------------------------------------------------------------------------


class ContextAssembler:
    """
    Assembles context for a tick type from the three data sources.

    Usage:
        assembler = ContextAssembler(consciousness_state, user_model, constitution)
        context = assembler.assemble("daily_review")
        # context.sections → list of included ContextSections
        # context.full_text → the assembled prompt context
        # context.token_estimate → estimated tokens used
        # context.dropped → sections that didn't fit
    """

    def __init__(
        self,
        consciousness_state: ConsciousnessState,
        user_model: Optional[Any] = None,
        constitution: Optional[Any] = None,
    ):
        self.cs = consciousness_state
        self.user_model = user_model
        self.constitution = constitution

    def assemble(self, tick_type: str, trigger_domain: Optional[str] = None) -> AssembledContext:
        """
        Assemble context for a tick type.

        Args:
            tick_type: One of "daily_review", "weekly_reflect", "monthly_deep", "urgent"
            trigger_domain: For urgent ticks, the domain that triggered the event

        Returns:
            AssembledContext with sections, full_text, and metadata
        """
        if tick_type == TickType.DAILY_REVIEW.value:
            sections = self._daily_sections()
        elif tick_type == TickType.WEEKLY_REFLECT.value:
            sections = self._weekly_sections()
        elif tick_type == TickType.MONTHLY_DEEP.value:
            sections = self._monthly_sections()
        elif tick_type == TickType.URGENT.value:
            sections = self._urgent_sections(trigger_domain)
        else:
            sections = []

        budget = TOKEN_BUDGETS.get(tick_type, 5000)
        return self._fit_to_budget(sections, budget, tick_type)

    # --- Per-Tick Section Builders ---

    def _daily_sections(self) -> List[ContextSection]:
        """Build sections for daily review tick."""
        now = datetime.now()
        sections = []

        # Priority 1: Narrative (always included, guides attention)
        sections.append(ContextSection(
            name="narrative",
            header="## Current Narrative",
            content=format_narrative(self.cs.narrative),
            priority=1,
        ))

        # Priority 2: World model expectations
        sections.append(ContextSection(
            name="world_model",
            header="## Current Understanding (World Model)",
            content=format_world_model(self.cs.world_model),
            priority=2,
        ))

        # Priority 3: Today's observations (elevated+ errors first)
        elevated = self.cs.get_elevated_observations_since(now - timedelta(hours=24))
        all_obs = self.cs.get_observations_since(now - timedelta(hours=24))
        # Include elevated separately if any exist
        if elevated:
            sections.append(ContextSection(
                name="elevated_errors",
                header="## Prediction Errors Detected Today",
                content=format_observations(elevated),
                priority=3,
            ))
        sections.append(ContextSection(
            name="observations",
            header="## Recent Observations (Last 24h)",
            content=format_observations(all_obs),
            priority=4,
        ))

        # Priority 5: Active goals
        goals = self._get_goals_dicts(active_only=True)
        sections.append(ContextSection(
            name="goals",
            header="## Active Goals",
            content=format_goals(goals, active_only=True),
            priority=5,
        ))

        # Priority 6: Questions ready for resolution (high urgency)
        ready_questions = self.cs.get_ready_questions()
        if ready_questions:
            sections.append(ContextSection(
                name="ready_questions",
                header="## Questions Ready for Resolution",
                content=format_ready_questions(ready_questions),
                priority=3,  # Same priority as elevated errors — these are actionable
            ))

        # Priority 7: Top dormant questions (still marinating)
        questions = [
            q for q in self.cs.get_unresolved_questions(limit=5)
            if not q.is_ready()  # Exclude ready ones — already shown above
        ]
        sections.append(ContextSection(
            name="dormant_questions",
            header="## Unresolved Questions",
            content=format_dormant_questions(questions),
            priority=7,
        ))

        # Priority 8: Today's daily data (raw)
        today_data = self._get_today_daily_data()
        if today_data:
            sections.append(ContextSection(
                name="daily_data",
                header="## Today's Data",
                content=json.dumps(today_data, indent=2),
                priority=8,
            ))

        return sections

    def _weekly_sections(self) -> List[ContextSection]:
        """Build sections for weekly reflect tick."""
        now = datetime.now()
        sections = []

        # Priority 1: Narrative
        sections.append(ContextSection(
            name="narrative",
            header="## Current Narrative",
            content=format_narrative(self.cs.narrative),
            priority=1,
        ))

        # Priority 2: World model
        sections.append(ContextSection(
            name="world_model",
            header="## Current Understanding (World Model)",
            content=format_world_model(self.cs.world_model),
            priority=2,
        ))

        # Priority 3: Daily summaries (compressed, not raw observations)
        daily_summaries = self.cs.get_summaries("daily", limit=7)
        sections.append(ContextSection(
            name="daily_summaries",
            header="## This Week's Daily Summaries",
            content=format_summaries(daily_summaries),
            priority=3,
        ))

        # Priority 4: All goals
        goals = self._get_goals_dicts(active_only=False)
        sections.append(ContextSection(
            name="goals",
            header="## Goals",
            content=format_goals(goals, active_only=False),
            priority=4,
        ))

        # Priority 5: Questions ready for resolution
        ready_questions = self.cs.get_ready_questions()
        if ready_questions:
            sections.append(ContextSection(
                name="ready_questions",
                header="## Questions Ready for Resolution",
                content=format_ready_questions(ready_questions),
                priority=3,  # High priority — actionable this week
            ))

        # Priority 5: All dormant questions (excluding ready ones)
        questions = [
            q for q in self.cs.get_unresolved_questions()
            if not q.is_ready()
        ]
        sections.append(ContextSection(
            name="dormant_questions",
            header="## Unresolved Questions",
            content=format_dormant_questions(questions),
            priority=5,
        ))

        # Priority 6: Constitution principles summary
        principles = self._get_principles_dicts()
        sections.append(ContextSection(
            name="constitution",
            header="## Constitution Principles",
            content=format_principles(principles, summary_only=True),
            priority=6,
        ))

        # Priority 7: Elevated errors this week
        elevated = self.cs.get_elevated_observations_since(now - timedelta(days=7))
        if elevated:
            sections.append(ContextSection(
                name="elevated_errors",
                header="## Notable Prediction Errors This Week",
                content=format_observations(elevated),
                priority=7,
            ))

        return sections

    def _monthly_sections(self) -> List[ContextSection]:
        """Build sections for monthly deep tick."""
        sections = []

        # Priority 1: Narrative
        sections.append(ContextSection(
            name="narrative",
            header="## Current Narrative",
            content=format_narrative(self.cs.narrative),
            priority=1,
        ))

        # Priority 2: World model with history
        sections.append(ContextSection(
            name="world_model",
            header="## Current Understanding (World Model)",
            content=format_world_model(self.cs.world_model),
            priority=2,
        ))

        # Priority 3: Weekly summaries (compressed month)
        weekly_summaries = self.cs.get_summaries("weekly", limit=4)
        sections.append(ContextSection(
            name="weekly_summaries",
            header="## This Month's Weekly Summaries",
            content=format_summaries(weekly_summaries),
            priority=3,
        ))

        # Priority 4: Recent daily summaries (last week's detail)
        daily_summaries = self.cs.get_summaries("daily", limit=7)
        sections.append(ContextSection(
            name="daily_summaries",
            header="## Recent Daily Summaries",
            content=format_summaries(daily_summaries),
            priority=4,
        ))

        # Priority 5: All goals with history
        goals = self._get_goals_dicts(active_only=False)
        sections.append(ContextSection(
            name="goals",
            header="## Goals (All)",
            content=format_goals(goals, active_only=False),
            priority=5,
        ))

        # Priority 6: Constitution (full)
        principles = self._get_principles_dicts()
        sections.append(ContextSection(
            name="constitution",
            header="## Constitution",
            content=format_principles(principles, summary_only=False),
            priority=6,
        ))

        # Priority 7: Purpose history
        purpose, history = self._get_purpose_data()
        sections.append(ContextSection(
            name="purpose",
            header="## Life Purpose",
            content=format_purpose_history(purpose, history),
            priority=7,
        ))

        # Priority 8: Personality
        traits, prefs = self._get_personality_data()
        sections.append(ContextSection(
            name="personality",
            header="## Personality & Preferences",
            content=format_personality(traits, prefs),
            priority=8,
        ))

        # Priority 9: Questions ready for resolution
        ready_questions = self.cs.get_ready_questions()
        if ready_questions:
            sections.append(ContextSection(
                name="ready_questions",
                header="## Questions Ready for Resolution",
                content=format_ready_questions(ready_questions),
                priority=5,  # High priority for monthly review
            ))

        # Priority 9: All dormant questions (excluding ready ones)
        questions = [
            q for q in self.cs.get_unresolved_questions()
            if not q.is_ready()
        ]
        sections.append(ContextSection(
            name="dormant_questions",
            header="## Unresolved Questions",
            content=format_dormant_questions(questions),
            priority=9,
        ))

        return sections

    def _urgent_sections(self, trigger_domain: Optional[str] = None) -> List[ContextSection]:
        """Build sections for urgent tick (focused and fast)."""
        now = datetime.now()
        sections = []

        # Priority 1: Narrative (current focus only — truncated)
        narrative = self.cs.narrative
        if len(narrative) > 200:
            narrative = narrative[:200] + "..."
        sections.append(ContextSection(
            name="narrative",
            header="## Current Focus",
            content=format_narrative(narrative),
            priority=1,
        ))

        # Priority 2: World model for triggering domain only
        domains = [trigger_domain] if trigger_domain else None
        sections.append(ContextSection(
            name="world_model",
            header="## Relevant Expectations",
            content=format_world_model(self.cs.world_model, domains=domains),
            priority=2,
        ))

        # Priority 3: Recent observations (last 6h, same domain if specified)
        obs = self.cs.get_observations_since(now - timedelta(hours=6), domain=trigger_domain)
        sections.append(ContextSection(
            name="observations",
            header="## Recent Observations",
            content=format_observations(obs),
            priority=3,
        ))

        return sections

    # --- Helper Methods to Extract Data ---

    def _get_goals_dicts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Extract goals from UserModel as dicts."""
        if not self.user_model:
            return []
        goals = self.user_model.get_active_goals() if active_only else self.user_model.goals
        return [
            {
                "id": g.id,
                "domain": g.domain,
                "description": g.description,
                "time_horizon": g.time_horizon,
                "status": g.status,
            }
            for g in goals
        ]

    def _get_principles_dicts(self) -> List[Dict[str, Any]]:
        """Extract constitution principles as dicts."""
        if not self.constitution:
            return []
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "rules": p.rules,
                "weight": p.weight,
            }
            for p in self.constitution.core_principles
        ]

    def _get_today_daily_data(self) -> Dict[str, Any]:
        """Get today's daily data from UserModel."""
        if not self.user_model:
            return {}
        today = datetime.now().date().isoformat()
        return self.user_model.get_daily_data(today)

    def _get_purpose_data(self) -> tuple:
        """Get purpose statement and history."""
        if not self.user_model:
            return None, []
        history = [
            {"statement": ph.statement, "set_at": ph.set_at.isoformat()}
            for ph in self.user_model.purpose_history
        ]
        return self.user_model.purpose_statement, history

    def _get_personality_data(self) -> tuple:
        """Get personality traits and preferences."""
        if not self.user_model:
            return {}, {}
        return self.user_model.personality_traits, self.user_model.preferences

    # --- Budget Enforcement ---

    def _fit_to_budget(
        self,
        sections: List[ContextSection],
        budget: int,
        tick_type: str,
    ) -> AssembledContext:
        """
        Fit sections into the token budget, dropping lowest-priority sections first.

        Sections are added in priority order (1=highest). Once the budget is
        exceeded, remaining sections are dropped.
        """
        sorted_sections = sorted(sections, key=lambda s: s.priority)
        included = []
        dropped = []
        total_tokens = 0

        for section in sorted_sections:
            section_tokens = section.token_estimate
            if total_tokens + section_tokens <= budget:
                included.append(section)
                total_tokens += section_tokens
            else:
                dropped.append(section)

        return AssembledContext(
            tick_type=tick_type,
            sections=included,
            dropped=dropped,
            token_budget=budget,
            token_estimate=total_tokens,
        )


# ---------------------------------------------------------------------------
# Assembled Context — The output of assembly
# ---------------------------------------------------------------------------


class AssembledContext:
    """
    The result of context assembly.

    Contains the included sections (in priority order), dropped sections,
    and the full assembled text ready for prompt insertion.
    """

    def __init__(
        self,
        tick_type: str,
        sections: List[ContextSection],
        dropped: List[ContextSection],
        token_budget: int,
        token_estimate: int,
    ):
        self.tick_type = tick_type
        self.sections = sections
        self.dropped = dropped
        self.token_budget = token_budget
        self.token_estimate = token_estimate

    @property
    def full_text(self) -> str:
        """The assembled context as a single string, sections in priority order."""
        return "\n\n".join(s.full_text for s in self.sections)

    @property
    def section_names(self) -> List[str]:
        """Names of included sections."""
        return [s.name for s in self.sections]

    @property
    def dropped_names(self) -> List[str]:
        """Names of dropped sections."""
        return [s.name for s in self.dropped]

    def get_section(self, name: str) -> Optional[ContextSection]:
        """Get a specific section by name."""
        for s in self.sections:
            if s.name == name:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for debugging/logging."""
        return {
            "tick_type": self.tick_type,
            "sections": self.section_names,
            "dropped": self.dropped_names,
            "token_budget": self.token_budget,
            "token_estimate": self.token_estimate,
        }
