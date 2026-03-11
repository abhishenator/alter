"""
OpenClaw Adapter — Maps an OpenClaw session to LifeOS's consciousness engine.

Unlike StandaloneAdapter, OpenClaw provides:
- LLM via session.chat() — no need for langchain
- Scheduling via cron in SKILL.md — no APScheduler
- Notification delivery via session channels (WhatsApp, Discord, etc.)

The adapter just bridges the two systems:
    session.chat(prompt) → think_fn
    engine notifications → session.send_message()
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

from alter.consciousness.engine import ConsciousnessEngine
from alter.consciousness.llm import ThinkFn
from alter.consciousness.state import ConsciousnessState, Observation

logger = logging.getLogger(__name__)


@runtime_checkable
class OpenClawSession(Protocol):
    """Protocol for the OpenClaw session object.

    OpenClaw is an external package — we define a Protocol so LifeOS
    doesn't depend on it at import time. Any object with these methods
    will work.
    """

    def chat(self, prompt: str) -> str:
        """Send a prompt to the session's LLM and return the response."""
        ...

    def send_message(self, message: str) -> None:
        """Send a message to the user via the session's active channel."""
        ...

    @property
    def user_id(self) -> str:
        """The user ID associated with this session."""
        ...


class OpenClawAdapter:
    """
    LifeOS as an OpenClaw skill.

    Created once per OpenClaw session. OpenClaw tools (tools.py) call
    methods on this adapter, which delegates to ConsciousnessEngine.

    Usage (inside an OpenClaw skill loader):
        adapter = OpenClawAdapter(session)
        # Now tools.py functions can call adapter.get_status(), etc.
    """

    def __init__(
        self,
        session: OpenClawSession,
        user_id: Optional[str] = None,
        auto_save: bool = True,
    ):
        self.session = session
        self.user_id = user_id or session.user_id

        # Load state
        self.consciousness_state = ConsciousnessState.load(self.user_id)

        # Wrap session.chat as a think_fn
        self._think_fn: ThinkFn = self._make_think_fn(session)

        # Create engine (no user_model/constitution — OpenClaw keeps it simple)
        self.engine = ConsciousnessEngine(
            consciousness_state=self.consciousness_state,
            think_fn=self._think_fn,
            auto_save=auto_save,
        )

    @staticmethod
    def _make_think_fn(session: OpenClawSession) -> ThinkFn:
        """Wrap session.chat() as a ThinkFn."""
        def think(prompt: str) -> str:
            return session.chat(prompt)
        return think

    # ------------------------------------------------------------------
    # Tool-facing methods (called by tools.py)
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Status snapshot for alter_status tool."""
        state = self.consciousness_state
        return {
            "user_id": self.user_id,
            "narrative": state.narrative,
            "world_model_domains": state.world_model.get_domains(),
            "pending_notifications": len(state.get_pending_notifications()),
            "dormant_questions": len(state.get_unresolved_questions()),
            "daily_token_usage": state.get_daily_token_usage(),
        }

    async def trigger_tick(self, tick_type: str) -> Any:
        """Run a thinking tick. Returns TickResult or None."""
        result = await self.engine.tick(tick_type)
        if result and result.notifications:
            self._deliver_notifications(result)
        return result

    async def trigger_observe(self) -> List[Observation]:
        """Run pre-attentive observation. Returns observations."""
        return await self.engine.hourly_observe_async()

    # ------------------------------------------------------------------
    # Notification delivery via OpenClaw channel
    # ------------------------------------------------------------------

    def _deliver_notifications(self, result: Any) -> None:
        """Push notifications from a tick result to the user's channel."""
        for notification in result.notifications:
            try:
                self.session.send_message(notification.message)
            except Exception:
                logger.exception(
                    "Failed to deliver notification via OpenClaw channel: %s",
                    notification.message[:80],
                )
