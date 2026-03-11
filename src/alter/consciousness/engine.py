"""
Consciousness Engine — The orchestrator.

This is where ALTER thinks for the first time. The engine wires together
all consciousness components into a single loop:

    Read state → Assemble context → Build prompt → Call LLM → Parse → Apply → Save

The engine owns:
    - tick(): the full thinking cycle for any tick type
    - apply_result(): translating LLM output into state mutations
    - hourly_observe(): pre-attentive signal detection (no LLM)

The engine does NOT own:
    - Scheduling (Phase C4 — standalone adapter with APScheduler)
    - Which LLM to use (injected via think_fn)
    - How to deliver notifications to the user (adapter responsibility)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from alter.consciousness.config import TickType
from alter.consciousness.context import ContextAssembler
from alter.consciousness.llm import ThinkFn
from alter.consciousness.observe import observe_daily_data
from alter.consciousness.parse import ParseError, TickResult, parse_tick_result
from alter.consciousness.prompts import build_prompt
from alter.consciousness.state import (
    ConsciousnessState,
    DormantQuestion,
    Observation,
    Summary,
)

logger = logging.getLogger(__name__)


# Map tick types to summary period types
TICK_TO_PERIOD = {
    TickType.DAILY_REVIEW.value: "daily",
    TickType.WEEKLY_REFLECT.value: "weekly",
    TickType.MONTHLY_DEEP.value: "monthly",
}


def _period_label_for_tick(tick_type: str) -> str:
    """Derive the summary period label for a tick type."""
    now = datetime.now()
    if tick_type == TickType.DAILY_REVIEW.value:
        return now.date().isoformat()  # "2026-02-16"
    elif tick_type == TickType.WEEKLY_REFLECT.value:
        return now.strftime("%G-W%V")  # "2026-W07" (ISO week)
    elif tick_type == TickType.MONTHLY_DEEP.value:
        return now.strftime("%Y-%m")   # "2026-02"
    return now.date().isoformat()


class ConsciousnessEngine:
    """
    The orchestrator that makes ALTER think.

    Usage:
        engine = ConsciousnessEngine(state, user_model, constitution, think_fn)

        # Full thinking cycle
        result = engine.tick_sync("daily_review")

        # Pre-attentive signal detection (hourly, no LLM)
        observations = engine.hourly_observe()

    The engine is stateless itself — all state lives in ConsciousnessState.
    It just reads, thinks, and writes.
    """

    def __init__(
        self,
        consciousness_state: ConsciousnessState,
        user_model: Optional[Any] = None,
        constitution: Optional[Any] = None,
        think_fn: Optional[ThinkFn] = None,
        auto_save: bool = True,
        skill_registry: Optional[Any] = None,
    ):
        """
        Args:
            consciousness_state: The shared blackboard (read/write)
            user_model: UserModel instance (read-only during ticks)
            constitution: Constitution instance (read-only during ticks)
            think_fn: LLM callable — takes prompt str, returns raw text
            auto_save: Whether to save state after each tick
            skill_registry: SkillRegistry for data collection (optional)
        """
        self.state = consciousness_state
        self.user_model = user_model
        self.constitution = constitution
        self.think_fn = think_fn
        self.auto_save = auto_save
        self.skill_registry = skill_registry

    # ------------------------------------------------------------------
    # Core: tick()
    # ------------------------------------------------------------------

    async def tick(
        self,
        tick_type: str,
        trigger_domain: Optional[str] = None,
        user_context: Optional[str] = None,
    ) -> Optional[TickResult]:
        """
        Run a full thinking cycle.

        1. Assemble context for this tick type
        2. Build the prompt
        3. Call the LLM via think_fn
        4. Parse the structured result
        5. Apply state mutations
        6. Save state

        Args:
            tick_type: "daily_review", "weekly_reflect", "monthly_deep", "urgent"
            trigger_domain: For urgent ticks, which domain triggered it
            user_context: Optional user-provided question/context (for Ask ALTER)

        Returns:
            TickResult on success, None on parse failure
        """
        if not self.think_fn:
            raise RuntimeError("No think_fn provided. Cannot run tick without an LLM.")

        logger.info("Starting %s tick for user %s", tick_type, self.state.user_id)

        # 1. Assemble context
        assembler = ContextAssembler(
            self.state, self.user_model, self.constitution,
            data_dir="data/user_data",
        )
        context = assembler.assemble(tick_type, trigger_domain=trigger_domain)
        logger.debug(
            "Context assembled: %d sections, ~%d tokens (budget: %d)",
            len(context.sections), context.token_estimate, context.token_budget,
        )

        # 2. Build prompt
        user_name = None
        if self.user_model and hasattr(self.user_model, 'user_id'):
            user_name = self.user_model.user_id
        prompt = build_prompt(tick_type, context, user_name=user_name, user_context=user_context)

        # 3. Call LLM
        logger.debug("Calling think_fn with prompt (%d chars)", len(prompt))
        raw_response = await asyncio.to_thread(self.think_fn, prompt)
        logger.debug("Received response (%d chars)", len(raw_response))

        # 4. Parse
        try:
            result = parse_tick_result(raw_response)
        except ParseError as e:
            logger.warning("Parse failed for %s tick: %s", tick_type, e)
            return None

        # 5. Apply state mutations
        self.apply_result(tick_type, result)

        # 6. Track tokens (approximate from char lengths)
        token_estimate = (len(prompt) + len(raw_response)) // 4
        self.state.record_token_usage(tick_type, token_estimate)

        # 7. Save
        if self.auto_save:
            self.state.save()

        logger.info(
            "Completed %s tick: %d observations, %d insights, %d decisions, %d notifications",
            tick_type,
            len(result.observations),
            len(result.insights),
            len(result.decisions),
            len(result.notifications),
        )

        return result

    def tick_sync(
        self,
        tick_type: str,
        trigger_domain: Optional[str] = None,
    ) -> Optional[TickResult]:
        """Synchronous wrapper for tick(). Convenient for CLI and testing."""
        return asyncio.run(self.tick(tick_type, trigger_domain=trigger_domain))

    # ------------------------------------------------------------------
    # Apply: state mutations from TickResult
    # ------------------------------------------------------------------

    def apply_result(self, tick_type: str, result: TickResult) -> None:
        """
        Apply a TickResult to the consciousness state.

        This is the write step — translating LLM reasoning into state changes.
        Each field of TickResult maps to a specific state mutation.
        """
        # 1. Update narrative
        if result.narrative:
            self.state.update_narrative(result.narrative)

        # 2. Apply world model updates
        for update in result.world_model_updates:
            exp = self.state.world_model.get_expectation(update.domain, update.aspect)
            if exp:
                if update.new_description:
                    exp.description = update.new_description
                if update.new_numeric_value is not None:
                    exp.numeric_value = update.new_numeric_value
                exp.last_confirmed = datetime.now().isoformat()
            else:
                # Create new expectation from LLM suggestion
                from alter.consciousness.state import Expectation
                new_exp = Expectation(
                    domain=update.domain,
                    aspect=update.aspect,
                    description=update.new_description or "",
                    numeric_value=update.new_numeric_value,
                    confidence=0.3,  # LLM-suggested, not yet observed
                )
                self.state.world_model.set_expectation(new_exp)

        # 3. Queue notifications
        for notification in result.notifications:
            self.state.add_notification(
                message=notification.message,
                context={"urgency": notification.urgency, "tick_type": tick_type},
            )

        # 4. Create new dormant questions
        for new_q in result.dormant_questions.new:
            self.state.add_dormant_question(DormantQuestion(
                question=new_q.question,
                context=new_q.context,
                domain=new_q.domain,
                resolution_signals=new_q.resolution_signals,
                created_by_tick=tick_type,
            ))

        # 5. Resolve dormant questions
        for resolved in result.dormant_questions.resolved:
            if resolved.question_id:
                self.state.resolve_question(resolved.question_id, resolved.resolution)

        # 6. Store summary for hierarchical memory
        if result.summary:
            period_type = TICK_TO_PERIOD.get(tick_type)
            if period_type:
                period_label = _period_label_for_tick(tick_type)
                self.state.add_summary(Summary(
                    period_type=period_type,
                    period_label=period_label,
                    content=result.summary.content,
                    key_insights=result.summary.key_insights,
                    key_facts=result.summary.key_facts,
                    prediction_errors_summary=result.summary.prediction_errors_summary,
                    observation_count=len(result.observations),
                    created_by_tick=tick_type,
                    domains_covered=list({
                        obs.domain for obs in result.observations if obs.domain
                    }),
                ))

        # 7. Compact old data (lightweight, runs after every tick)
        self.state.compact()

    # ------------------------------------------------------------------
    # Skill data collection
    # ------------------------------------------------------------------

    async def collect_skill_data(self) -> None:
        """
        Collect data from all registered skills and merge into daily_data.

        Calls registry.collect_all(), then records the merged data into
        the user model for today's date. Idempotent — can be called
        multiple times per day, later values overwrite earlier ones.
        """
        if not self.skill_registry or not self.user_model:
            return

        try:
            data = await self.skill_registry.collect_all()
            if data:
                today = datetime.now().date().isoformat()
                data["date"] = today
                self.user_model.record_daily_data(data)
                logger.info(
                    "Collected skill data: %s",
                    ", ".join(f"{k}({len(v) if isinstance(v, dict) else 1})" for k, v in data.items() if k != "date"),
                )
        except Exception:
            logger.exception("Failed to collect skill data")

    # ------------------------------------------------------------------
    # Hourly Observe: pre-attentive signal detection
    # ------------------------------------------------------------------

    def hourly_observe(self) -> List[Observation]:
        """
        Pre-attentive signal detection — Python-only, no LLM.

        Compares today's daily data against world model expectations.
        Stores observations in state. If any are CRITICAL, fires an
        urgent tick automatically (the watch event mechanism).

        Returns:
            List of observations produced
        """
        if not self.user_model:
            logger.debug("No user_model, skipping hourly observe")
            return []

        today = datetime.now().date().isoformat()
        daily_data = self.user_model.get_daily_data(today)
        if not daily_data:
            logger.debug("No daily data for %s, skipping hourly observe", today)
            return []

        # Run prediction error math
        observations = observe_daily_data(self.state.world_model, daily_data)
        if observations:
            self.state.add_observations(observations)
            logger.info(
                "Hourly observe: %d observations (%s)",
                len(observations),
                ", ".join(f"{o.aspect}={o.severity}" for o in observations),
            )

        # Update dormant question readiness based on new observations
        if observations:
            newly_ready = self.state.update_dormant_readiness(observations)
            if newly_ready:
                logger.info(
                    "Dormant questions now ready: %s",
                    [q.question[:50] for q in newly_ready],
                )

        # Check for critical signals → fire urgent tick
        critical = [o for o in observations if o.severity == "critical"]
        if critical and self.think_fn:
            logger.info("CRITICAL signals detected: %s — firing urgent tick",
                       [o.aspect for o in critical])
            # Record the watch event
            self.state.add_watch_event(critical)
            # Determine the primary domain for focused context
            trigger_domain = critical[0].domain
            # Fire urgent tick (sync since hourly_observe is sync)
            self.tick_sync("urgent", trigger_domain=trigger_domain)

        if self.auto_save:
            self.state.save()

        return observations

    async def hourly_observe_async(self) -> List[Observation]:
        """
        Async version of hourly_observe for use inside async event loops.

        Same logic as hourly_observe(), but fires urgent ticks via
        await self.tick() instead of self.tick_sync() (which uses
        asyncio.run() and would fail inside a running event loop).
        """
        if not self.user_model:
            logger.debug("No user_model, skipping hourly observe")
            return []

        today = datetime.now().date().isoformat()
        daily_data = self.user_model.get_daily_data(today)
        if not daily_data:
            logger.debug("No daily data for %s, skipping hourly observe", today)
            return []

        observations = observe_daily_data(self.state.world_model, daily_data)
        if observations:
            self.state.add_observations(observations)
            logger.info(
                "Hourly observe (async): %d observations (%s)",
                len(observations),
                ", ".join(f"{o.aspect}={o.severity}" for o in observations),
            )

        # Update dormant question readiness based on new observations
        if observations:
            newly_ready = self.state.update_dormant_readiness(observations)
            if newly_ready:
                logger.info(
                    "Dormant questions now ready: %s",
                    [q.question[:50] for q in newly_ready],
                )

        # Check for critical signals → fire urgent tick (async)
        critical = [o for o in observations if o.severity == "critical"]
        if critical and self.think_fn:
            logger.info("CRITICAL signals detected: %s — firing urgent tick",
                       [o.aspect for o in critical])
            self.state.add_watch_event(critical)
            trigger_domain = critical[0].domain
            await self.tick("urgent", trigger_domain=trigger_domain)

        if self.auto_save:
            self.state.save()

        return observations
