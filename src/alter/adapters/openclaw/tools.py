"""
Tool Definitions — What ALTER exposes as an OpenClaw skill.

Each tool is a function that OpenClaw can invoke on behalf of the user.
Tools receive the adapter instance and return structured results that
OpenClaw formats for the user's channel (WhatsApp, Discord, etc.).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from alter.adapters.openclaw.adapter import OpenClawAdapter


def alter_status(adapter: OpenClawAdapter) -> Dict[str, Any]:
    """Get consciousness engine status."""
    return adapter.get_status()


async def alter_reflect(
    adapter: OpenClawAdapter,
    tick_type: str = "daily_review",
) -> Dict[str, Any]:
    """Trigger a conscious thinking cycle."""
    valid_types = ["daily_review", "weekly_reflect", "monthly_deep"]
    if tick_type not in valid_types:
        return {"error": f"Invalid tick_type. Must be one of: {valid_types}"}

    result = await adapter.trigger_tick(tick_type)
    if result is None:
        return {"status": "completed", "detail": "Tick ran but parse failed"}

    response: Dict[str, Any] = {
        "status": "completed",
        "tick_type": tick_type,
        "observations": len(result.observations),
        "insights": [
            {"description": i.description, "confidence": i.confidence}
            for i in result.insights
        ],
        "decisions": [
            {"action": d.action, "target": d.target}
            for d in result.decisions
        ],
        "notifications": [n.message for n in result.notifications],
    }

    if result.narrative:
        response["narrative"] = result.narrative

    return response


async def alter_observe(adapter: OpenClawAdapter) -> Dict[str, Any]:
    """Run pre-attentive observation (no LLM)."""
    observations = await adapter.trigger_observe()
    return {
        "observation_count": len(observations),
        "observations": [
            {
                "domain": o.domain,
                "aspect": o.aspect,
                "severity": o.severity,
                "summary": o.summary,
                "prediction_error": round(o.prediction_error, 3),
            }
            for o in observations
        ],
    }


def alter_narrative(adapter: OpenClawAdapter) -> Dict[str, Any]:
    """Get the current narrative thread."""
    state = adapter.consciousness_state
    return {
        "narrative": state.narrative,
        "history_count": len(state.narrative_history),
    }


def alter_questions(adapter: OpenClawAdapter) -> Dict[str, Any]:
    """Get dormant questions and their readiness."""
    state = adapter.consciousness_state
    unresolved = state.get_unresolved_questions()
    ready = state.get_ready_questions()

    return {
        "total_unresolved": len(unresolved),
        "ready_count": len(ready),
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "domain": q.domain,
                "readiness": round(q.readiness, 2),
                "ready": q.is_ready(),
                "resolution_signals": q.resolution_signals,
            }
            for q in unresolved
        ],
    }


def alter_notify(adapter: OpenClawAdapter) -> Dict[str, Any]:
    """Get and deliver pending notifications."""
    state = adapter.consciousness_state
    pending = state.get_pending_notifications()

    # Mark them as delivered
    for n in pending:
        state.mark_notification_delivered(n["id"])

    if adapter.engine.auto_save:
        state.save()

    return {
        "notification_count": len(pending),
        "notifications": [
            {
                "message": n["message"],
                "urgency": n.get("context", {}).get("urgency", "normal"),
                "timestamp": n.get("timestamp", ""),
            }
            for n in pending
        ],
    }


# Registry of all tools for OpenClaw discovery
TOOLS = {
    "alter_status": {
        "fn": alter_status,
        "description": "Get consciousness engine status",
        "async": False,
    },
    "alter_reflect": {
        "fn": alter_reflect,
        "description": "Trigger a conscious thinking cycle",
        "async": True,
        "parameters": {
            "tick_type": {
                "type": "string",
                "description": "Type of reflection: daily_review, weekly_reflect, monthly_deep",
                "default": "daily_review",
            },
        },
    },
    "alter_observe": {
        "fn": alter_observe,
        "description": "Run pre-attentive observation check (no LLM)",
        "async": True,
    },
    "alter_narrative": {
        "fn": alter_narrative,
        "description": "Get the current life narrative",
        "async": False,
    },
    "alter_questions": {
        "fn": alter_questions,
        "description": "Show dormant questions and readiness",
        "async": False,
    },
    "alter_notify": {
        "fn": alter_notify,
        "description": "Get and deliver pending notifications",
        "async": False,
    },
}
