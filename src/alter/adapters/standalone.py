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
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from alter.consciousness.config import TickType
from alter.consciousness.engine import ConsciousnessEngine
from alter.consciousness.llm import ThinkFn, create_think_fn
from alter.consciousness.observe import observe_daily_data
from alter.consciousness.state import ConsciousnessState, InboxItem, Observation

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

        # Configurable thought loops — each has enabled state and schedule
        self.thought_loops: Dict[str, Dict[str, Any]] = {
            "daily_review": {
                "label": "Daily Review",
                "description": "Reflect on the day — what happened, how goals are tracking, what to do next.",
                "enabled": True,
                "schedule": {"hour": 22, "minute": 0},
                "schedule_type": "daily",
            },
            "weekly_reflect": {
                "label": "Weekly Reflection",
                "description": "Step back and assess the whole week — wins, gaps, course corrections.",
                "enabled": True,
                "schedule": {"day_of_week": "sun", "hour": 20},
                "schedule_type": "weekly",
            },
            "monthly_deep": {
                "label": "Monthly Deep Review",
                "description": "Big picture — am I living the life I said I wanted? What needs to change?",
                "enabled": True,
                "schedule": {"day": 1, "hour": 10},
                "schedule_type": "monthly",
            },
            "goal_analysis": {
                "label": "Goal Deep-Dive",
                "description": "Structured analysis per goal — blockers, inefficiencies, possibilities, next action.",
                "enabled": True,
                "schedule": {"day_of_week": "wed", "hour": 21},
                "schedule_type": "weekly",
            },
            "discovery": {
                "label": "Discovery & Exploration",
                "description": "Proactive insights beyond current goals — opportunities, risks, blind spots.",
                "enabled": True,
                "schedule": {"day": 15, "hour": 10},
                "schedule_type": "monthly",
            },
        }

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
        """Create APScheduler with consciousness tick jobs from thought_loops config."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()

        # Hourly observe — pre-attentive signal detection (no LLM, always on)
        scheduler.add_job(
            self._run_hourly, trigger="cron",
            minute=0, id="hourly_observe",
            name="Hourly Observation",
        )

        # Schedule each enabled thought loop
        for loop_id, config in self.thought_loops.items():
            if not config.get("enabled", False):
                continue
            scheduler.add_job(
                self._run_tick, trigger="cron",
                args=[loop_id],
                id=loop_id,
                name=config.get("label", loop_id),
                **config["schedule"],
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
                self._log_tick_details(tick_type, result)
        except Exception:
            logger.exception("Tick %s failed", tick_type)

    # ------------------------------------------------------------------
    # Manual triggers (from API)
    # ------------------------------------------------------------------

    async def trigger_tick(self, tick_type: str, context: Optional[str] = None) -> Optional[Any]:
        """Manually trigger a thinking tick. Returns TickResult or None."""
        result = await self.engine.tick(tick_type, user_context=context)
        if result:
            self._log_tick_details(f"manual_{tick_type}", result)
        return result

    async def trigger_observe(self) -> List[Observation]:
        """Manually trigger hourly observation. Returns observations."""
        observations = await self.engine.hourly_observe_async()
        if observations:
            # Log each observation individually
            for o in observations:
                self._log_activity("observation", {
                    "domain": o.domain,
                    "aspect": o.aspect,
                    "summary": o.summary,
                    "severity": o.severity,
                    "tick_type": "observe",
                })
            self._log_activity("manual_observe", {
                "observation_count": len(observations),
            })
        return observations

    # ------------------------------------------------------------------
    # Activity log (for web UI thought stream)
    # ------------------------------------------------------------------

    def _log_tick_details(self, tick_type: str, result) -> None:
        """Expand a TickResult into individual activity entries so the stream feels alive."""
        now = datetime.now().isoformat()

        # 1. Log each observation as its own thought
        for obs in result.observations:
            self._log_activity("observation", {
                "domain": obs.domain,
                "aspect": obs.aspect,
                "summary": obs.observation,
                "significance": obs.significance,
                "tick_type": tick_type,
            })

        # 2. Log each insight → route to inbox
        for ins in result.insights:
            self._log_activity("insight", {
                "summary": ins.description,
                "domains": ins.domains,
                "confidence": ins.confidence,
                "tick_type": tick_type,
            })
            self._route_to_inbox(
                item_type="insight",
                title=ins.description[:80],
                body=ins.description,
                domain=ins.domains[0] if ins.domains else "",
                source_tick=tick_type,
            )

        # 3. Log each decision → route to inbox
        action_labels = {
            "notify_user": "Heads up",
            "update_expectation": "Updated expectation",
            "store_question": "New question",
            "resolve_question": "Question answered",
        }
        for dec in result.decisions:
            if dec.action == "no_action":
                continue
            self._log_activity("decision", {
                "action": dec.action,
                "target": dec.target,
                "summary": dec.detail,
                "tick_type": tick_type,
            })
            label = action_labels.get(dec.action, dec.action.replace("_", " ").title())
            self._route_to_inbox(
                item_type="decision",
                title=dec.detail[:80] if dec.detail else (f"{label}: {dec.target}" if dec.target else label),
                body=dec.detail,
                domain=dec.target,
                source_tick=tick_type,
                actionable=dec.detail,
            )

        # 4. Log notifications → route to inbox
        for notif in result.notifications:
            self._log_activity("notification", {
                "summary": notif.message,
                "urgency": notif.urgency,
                "tick_type": tick_type,
            })
            self._route_to_inbox(
                item_type="notification",
                title=notif.message[:80],
                body=notif.message,
                domain=getattr(notif, "domain", ""),
                source_tick=tick_type,
            )

        # 5. Log narrative update
        if result.narrative:
            self._log_activity("narrative_update", {
                "summary": result.narrative[:200],
                "tick_type": tick_type,
            })

        # 6. Log new dormant questions
        if result.dormant_questions and result.dormant_questions.new:
            for q in result.dormant_questions.new:
                self._log_activity("new_question", {
                    "summary": q.question,
                    "domain": q.domain,
                    "tick_type": tick_type,
                })

        # 7. Log resolved questions
        if result.dormant_questions and result.dormant_questions.resolved:
            for q in result.dormant_questions.resolved:
                self._log_activity("question_resolved", {
                    "summary": q.resolution,
                    "question_id": q.question_id,
                    "tick_type": tick_type,
                })

        # 8. Log world model updates
        for upd in result.world_model_updates:
            self._log_activity("world_update", {
                "domain": upd.domain,
                "aspect": upd.aspect,
                "summary": upd.reasoning or upd.new_description or "",
                "tick_type": tick_type,
            })

        # 8b. Log goal suggestions → route to inbox
        for gs in result.goal_suggestions:
            self._log_activity("goal_suggestion", {
                "summary": gs.description,
                "domain": gs.domain,
                "time_horizon": gs.time_horizon,
                "parent_goal": gs.parent_goal_description,
                "reasoning": gs.reasoning,
                "tick_type": tick_type,
            })
            self._route_to_inbox(
                item_type="goal_suggestion",
                title=gs.description[:80],
                body=gs.reasoning or gs.description,
                domain=gs.domain,
                source_tick=tick_type,
                actionable=gs.description,
                suggested_goal={
                    "description": gs.description,
                    "domain": gs.domain,
                    "time_horizon": gs.time_horizon,
                    "parent_goal": gs.parent_goal_description,
                },
            )

        # 8c. Log goal analyses — structured thought units per goal
        for ga in result.goal_analyses:
            self._log_activity("goal_analysis", {
                "summary": ga.goal,
                "domain": ga.domain,
                "current_state": ga.current_state,
                "whats_stopping_me": ga.whats_stopping_me,
                "whats_inefficient": ga.whats_inefficient,
                "possibilities": ga.possibilities,
                "next_action": ga.next_action,
                "confidence": ga.confidence,
                "tick_type": tick_type,
            })

        # 8d. Log discoveries → route to inbox
        for disc in result.discoveries:
            self._log_activity("discovery", {
                "summary": disc.title,
                "insight": disc.insight,
                "domain": disc.domain,
                "actionable": disc.actionable,
                "confidence": disc.confidence,
                "tick_type": tick_type,
            })
            self._route_to_inbox(
                item_type="discovery",
                title=disc.title[:80],
                body=disc.insight,
                domain=disc.domain,
                source_tick=tick_type,
                actionable=disc.actionable,
            )

        # 9. Summary entry (aggregate — still useful for the header)
        self._log_activity(tick_type, {
            "observations": len(result.observations),
            "insights": len(result.insights),
            "decisions": len(result.decisions),
            "notifications": len(result.notifications),
            "goal_analyses": len(result.goal_analyses),
            "discoveries": len(result.discoveries),
            "narrative_preview": (result.narrative[:100] + "...") if result.narrative else "",
        })

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

    VALID_DOMAINS = {"health", "career", "wealth", "relationships", "emotions", "growth"}

    @staticmethod
    def _normalize_domain(raw: str) -> str:
        """Map free-text domain to a known life domain."""
        raw_lower = raw.lower().strip()
        if raw_lower in StandaloneAdapter.VALID_DOMAINS:
            return raw_lower
        # Common LLM misnames
        mapping = {
            "fitness": "health", "nutrition": "health", "sleep": "health", "wellness": "health",
            "exercise": "health", "physical": "health",
            "money": "wealth", "finance": "wealth", "financial": "wealth", "income": "wealth",
            "job": "career", "work": "career", "professional": "career", "skill": "career",
            "family": "relationships", "social": "relationships", "friends": "relationships",
            "community": "relationships", "romantic": "relationships",
            "mental": "emotions", "mood": "emotions", "stress": "emotions", "happiness": "emotions",
            "anxiety": "emotions", "emotional": "emotions", "wellbeing": "emotions",
            "learning": "growth", "purpose": "growth", "personal": "growth", "education": "growth",
            "calendar": "growth", "productivity": "growth",
        }
        for keyword, domain in mapping.items():
            if keyword in raw_lower:
                return domain
        return "general"

    def _route_to_inbox(
        self,
        item_type: str,
        title: str,
        body: str,
        domain: str,
        source_tick: str,
        actionable: str = "",
        suggested_goal: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Route a consciousness output to the persisted inbox."""
        domain = self._normalize_domain(domain)
        linked_goal_id = self._find_goal_for_domain(domain, suggested_goal)
        item = InboxItem(
            item_type=item_type,
            title=title,
            body=body,
            domain=domain,
            source_tick=source_tick,
            actionable=actionable,
            suggested_goal=suggested_goal,
            linked_goal_id=linked_goal_id,
        )
        self.consciousness_state.add_inbox_item(item)

    def _find_goal_for_domain(
        self, domain: str, suggested_goal: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Find the most relevant active goal for a thought stream item.

        Strategy:
        1. If suggested_goal has a parent_goal description, match by description
        2. Otherwise match by domain, preferring broader time horizons
        """
        active_goals = self.user_model.get_active_goals()
        if not active_goals:
            return None

        # If the suggestion references a parent goal, try to find it by description
        if suggested_goal and suggested_goal.get("parent_goal"):
            parent_desc = suggested_goal["parent_goal"].lower()
            for g in active_goals:
                if g.description.lower() in parent_desc or parent_desc in g.description.lower():
                    return g.id

        # Match by domain — prefer broader horizons (life > year > quarter > month > week)
        horizon_priority = ["life", "5_year", "1_year", "quarter", "month", "week", "day"]
        domain_goals = [g for g in active_goals if g.domain == domain]
        if domain_goals:
            domain_goals.sort(
                key=lambda g: horizon_priority.index(g.time_horizon)
                if g.time_horizon in horizon_priority else 99
            )
            return domain_goals[0].id

        return None

    def get_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity entries (newest first)."""
        return list(reversed(self._activity_log[-limit:]))

    # ------------------------------------------------------------------
    # Thought Loop Configuration
    # ------------------------------------------------------------------

    def get_thought_loops(self) -> Dict[str, Dict[str, Any]]:
        """Get all thought loop configurations."""
        return self.thought_loops

    def update_thought_loop(self, loop_id: str, enabled: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Enable or disable a thought loop. Returns updated config or None if not found."""
        if loop_id not in self.thought_loops:
            return None
        if enabled is not None:
            self.thought_loops[loop_id]["enabled"] = enabled
            # Reschedule if running
            if self._running and self._scheduler:
                self._reschedule_loop(loop_id)
        return self.thought_loops[loop_id]

    def _reschedule_loop(self, loop_id: str) -> None:
        """Add or remove a scheduled job for a thought loop."""
        if not self._scheduler:
            return
        config = self.thought_loops.get(loop_id)
        if not config:
            return
        # Remove existing job if present
        try:
            self._scheduler.remove_job(loop_id)
        except Exception:
            pass
        # Add back if enabled
        if config.get("enabled", False):
            self._scheduler.add_job(
                self._run_tick, trigger="cron",
                args=[loop_id],
                id=loop_id,
                name=config.get("label", loop_id),
                **config["schedule"],
            )

    def get_status(self) -> Dict[str, Any]:
        """Get consciousness engine status for the API."""
        state = self.consciousness_state
        pending_inbox = state.get_pending_inbox()
        return {
            "running": self.is_running,
            "user_id": self.user_id,
            "provider": self.provider,
            "model": self.model,
            "narrative": state.narrative,
            "world_model_domains": state.world_model.get_domains(),
            "pending_notifications": len(state.get_pending_notifications()),
            "pending_inbox_count": len(pending_inbox),
            "dormant_questions": len(state.get_unresolved_questions()),
            "daily_token_usage": state.get_daily_token_usage(),
            "activity_count": len(self._activity_log),
            "inbox_pending": len(pending_inbox),
            "skills": self.skill_registry.skill_names,
            "thought_loops": {
                k: {"label": v["label"], "enabled": v["enabled"], "schedule_type": v["schedule_type"]}
                for k, v in self.thought_loops.items()
            },
        }
