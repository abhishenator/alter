"""
Standalone Adapter — Wire APScheduler + ConsciousnessEngine for `alter serve`.

This adapter makes ALTER conscious when running as a web server:
- APScheduler fires ticks on schedule (hourly, daily, weekly, monthly)
- langchain provides the think_fn (LLM abstraction)
- Activity log captures thoughts for the web UI

Usage:
    adapter = StandaloneAdapter(user_id="default", provider="anthropic")
    adapter.start()   # Begin scheduled thinking
    adapter.stop()    # Shutdown gracefully
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from alter.consciousness.config import TickType
from alter.consciousness.engine import ConsciousnessEngine
from alter.consciousness.llm import ThinkFn, create_think_fn
from alter.consciousness.observe import observe_daily_data
from alter.consciousness.state import ConsciousnessState, Observation

logger = logging.getLogger(__name__)

# Maximum activity log entries to retain
MAX_ACTIVITY_LOG = 200


class StandaloneAdapter:
    """
    Wires APScheduler + ConsciousnessEngine for alter serve.

    The adapter owns:
    - Loading user data and creating the engine
    - Scheduling ticks via APScheduler
    - Activity log for the web UI thought stream
    - Manual tick/observe triggers (from API)

    The adapter does NOT own:
    - Which LLM to use (configured via provider/model args)
    - How to deliver notifications (engine queues them in state)
    - The web server itself (FastAPI owns that)
    """

    def __init__(
        self,
        user_id: str,
        provider: str = "anthropic",
        model: Optional[str] = None,
        think_fn: Optional[ThinkFn] = None,
        auto_start: bool = False,
    ):
        self.user_id = user_id
        self.provider = provider
        self.model = model

        # Load components
        self.user_model = self._load_user_model()
        self.consciousness_state = ConsciousnessState.load(user_id)
        self.constitution = self._load_constitution()

        # Create or use provided think_fn
        if think_fn:
            self._think_fn = think_fn
        else:
            self._think_fn = create_think_fn(provider, model)

        # Set up skill registry with default skills
        self.skill_registry = self._create_skill_registry()

        # Create engine
        self.engine = ConsciousnessEngine(
            consciousness_state=self.consciousness_state,
            user_model=self.user_model,
            constitution=self.constitution,
            think_fn=self._think_fn,
            auto_save=True,
            skill_registry=self.skill_registry,
        )

        # Bootstrap skill expectations into world model
        if self.skill_registry.skill_names:
            from alter.skills.bootstrap import bootstrap_skills
            bootstrap_skills(self.skill_registry, self.consciousness_state.world_model)

        # Activity log for web UI
        self._activity_log: List[Dict[str, Any]] = []

        # Scheduler (lazy init — only created when start() is called)
        self._scheduler = None
        self._running = False

        if auto_start:
            self.start()

    def _load_user_model(self):
        """Load user model, creating a new one if not found."""
        from alter.core.user_model import UserModel
        try:
            return UserModel.load(self.user_id)
        except FileNotFoundError:
            logger.info("No user model found for %s, creating new one", self.user_id)
            user = UserModel.create_new(self.user_id)
            user.save()
            return user

    def _load_constitution(self):
        """Load constitution, returning None if not found."""
        try:
            from alter.core.constitution import Constitution
            return Constitution.load()
        except Exception:
            logger.info("No constitution found, running without it")
            return None

    def _create_skill_registry(self):
        """Create a skill registry with default skills."""
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        from alter.skills.calendar import CalendarSkill
        from alter.skills.journal import JournalSkill

        registry = SkillRegistry()
        registry.register(HealthSkill())
        registry.register(CalendarSkill())
        registry.register(JournalSkill())
        return registry

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------

    def _create_scheduler(self):
        """Create APScheduler with consciousness tick jobs."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()

        # Hourly observe — pre-attentive signal detection (no LLM)
        scheduler.add_job(
            self._run_hourly, trigger="cron",
            minute=0, id="hourly_observe",
            name="Hourly Observation",
        )

        # Daily review — full LLM tick every day at 22:00
        scheduler.add_job(
            self._run_tick, trigger="cron",
            args=[TickType.DAILY_REVIEW.value],
            hour=22, id="daily_review",
            name="Daily Review",
        )

        # Weekly reflect — every Sunday at 20:00
        scheduler.add_job(
            self._run_tick, trigger="cron",
            args=[TickType.WEEKLY_REFLECT.value],
            day_of_week="sun", hour=20,
            id="weekly_reflect",
            name="Weekly Reflection",
        )

        # Monthly deep — 1st of month at 10:00
        scheduler.add_job(
            self._run_tick, trigger="cron",
            args=[TickType.MONTHLY_DEEP.value],
            day=1, hour=10,
            id="monthly_deep",
            name="Monthly Deep Review",
        )

        return scheduler

    def start(self) -> None:
        """Start the consciousness scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._scheduler = self._create_scheduler()
        self._scheduler.start()
        self._running = True
        self._log_activity("engine_started", {
            "provider": self.provider,
            "model": self.model,
            "user_id": self.user_id,
        })
        logger.info(
            "Consciousness started for user %s (provider=%s, model=%s)",
            self.user_id, self.provider, self.model,
        )

    def stop(self) -> None:
        """Stop the consciousness scheduler."""
        if self._running and self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._running = False
            self._log_activity("engine_stopped", {})
            logger.info("Consciousness stopped for user %s", self.user_id)

    @property
    def is_running(self) -> bool:
        """Whether the scheduler is currently running."""
        return self._running

    # ------------------------------------------------------------------
    # Scheduled jobs
    # ------------------------------------------------------------------

    async def _run_hourly(self) -> None:
        """Scheduled job: hourly observation (async-safe)."""
        try:
            observations = await self.engine.hourly_observe_async()
            if observations:
                self._log_activity("hourly_observe", {
                    "observation_count": len(observations),
                    "observations": [
                        {
                            "domain": o.domain,
                            "aspect": o.aspect,
                            "severity": o.severity,
                            "summary": o.summary,
                        }
                        for o in observations
                    ],
                })
        except Exception:
            logger.exception("Hourly observe failed")

    async def _run_tick(self, tick_type: str) -> None:
        """Scheduled job: run a full thinking tick."""
        try:
            result = await self.engine.tick(tick_type)
            if result:
                self._log_activity(tick_type, {
                    "observations": len(result.observations),
                    "insights": len(result.insights),
                    "decisions": len(result.decisions),
                    "notifications": len(result.notifications),
                    "narrative_preview": (result.narrative[:100] + "...") if result.narrative else "",
                })
        except Exception:
            logger.exception("Tick %s failed", tick_type)

    # ------------------------------------------------------------------
    # Manual triggers (from API)
    # ------------------------------------------------------------------

    async def trigger_tick(self, tick_type: str) -> Optional[Any]:
        """Manually trigger a thinking tick. Returns TickResult or None."""
        result = await self.engine.tick(tick_type)
        if result:
            self._log_activity(f"manual_{tick_type}", {
                "observations": len(result.observations),
                "insights": len(result.insights),
                "decisions": len(result.decisions),
                "notifications": len(result.notifications),
            })
        return result

    async def trigger_observe(self) -> List[Observation]:
        """Manually trigger hourly observation. Returns observations."""
        observations = await self.engine.hourly_observe_async()
        if observations:
            self._log_activity("manual_observe", {
                "observation_count": len(observations),
            })
        return observations

    # ------------------------------------------------------------------
    # Activity log (for web UI thought stream)
    # ------------------------------------------------------------------

    def _log_activity(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an activity entry for the thought stream."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data,
        }
        self._activity_log.append(entry)
        if len(self._activity_log) > MAX_ACTIVITY_LOG:
            self._activity_log = self._activity_log[-MAX_ACTIVITY_LOG:]

    def get_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity entries (newest first)."""
        return list(reversed(self._activity_log[-limit:]))

    def get_status(self) -> Dict[str, Any]:
        """Get consciousness engine status for the API."""
        state = self.consciousness_state
        return {
            "running": self.is_running,
            "user_id": self.user_id,
            "provider": self.provider,
            "model": self.model,
            "narrative": state.narrative,
            "world_model_domains": state.world_model.get_domains(),
            "pending_notifications": len(state.get_pending_notifications()),
            "dormant_questions": len(state.get_unresolved_questions()),
            "daily_token_usage": state.get_daily_token_usage(),
            "activity_count": len(self._activity_log),
            "skills": self.skill_registry.skill_names,
        }
