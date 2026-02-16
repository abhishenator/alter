"""
Service layer bridging the API to ALTER core logic.

Centralizes user/state loading, saving, and all business operations.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import uuid

from alter.core.user_model import UserModel, Goal
from alter.core.state import SystemState
from alter.core.meta_loop import MetaLoop
from alter.core.constitution import Constitution


class AlterService:
    """Service layer for ALTER operations."""

    def __init__(self, data_dir: str = "data/user_data"):
        self.data_dir = Path(data_dir)

    def user_exists(self, user_id: str) -> bool:
        """Check if a user exists."""
        return (self.data_dir / user_id / "user_model.json").exists()

    def _load(self, user_id: str) -> tuple:
        """Load user, state, and create meta-loop."""
        user = UserModel.load(user_id)
        state = SystemState.load(user_id)
        constitution = Constitution.load()
        meta_loop = MetaLoop(state=state, constitution=constitution)
        return user, state, meta_loop, constitution

    def _save(self, user: UserModel, state: SystemState) -> None:
        """Save user and state."""
        user.save()
        state.save()

    # User Operations

    def init_user(self, user_id: str, purpose: Optional[str] = None) -> dict:
        """Initialize a new user."""
        user = UserModel.create_new(user_id=user_id)
        if purpose:
            user.set_purpose(purpose)
        state = SystemState.create(user_model=user)
        self._save(user, state)
        return {
            "user_id": user.user_id,
            "purpose": user.purpose_statement,
            "created_at": user.created_at.isoformat()
        }

    def get_status(self, user_id: str) -> dict:
        """Get full user status."""
        user, state, _, constitution = self._load(user_id)
        domains = constitution.get_life_domains()
        active_goals = user.get_active_goals()

        return {
            "user_id": user.user_id,
            "purpose": user.purpose_statement,
            "active_goals_count": len(active_goals),
            "total_goals": len(user.goals),
            "cycle_count": state.meta_state.cycle_count,
            "last_execution": state.meta_state.last_execution.isoformat() if state.meta_state.last_execution else None,
            "life_domains": [
                {"id": d.id, "name": d.name, "description": d.description}
                for d in domains
            ],
            "personality_traits": user.personality_traits,
            "strengths": user.strengths,
            "growth_areas": user.growth_areas
        }

    def set_purpose(self, user_id: str, purpose: str, notes: str = "") -> dict:
        """Set or update user's purpose."""
        user, state, _, _ = self._load(user_id)
        user.set_purpose(purpose, notes)
        self._save(user, state)
        return {
            "current": user.purpose_statement,
            "history": [
                {"statement": ph.statement, "set_at": ph.set_at.isoformat()}
                for ph in user.purpose_history
            ]
        }

    def get_purpose(self, user_id: str) -> dict:
        """Get user's purpose and history."""
        user, _, _, _ = self._load(user_id)
        return {
            "current": user.purpose_statement,
            "history": [
                {"statement": ph.statement, "set_at": ph.set_at.isoformat()}
                for ph in user.purpose_history
            ]
        }

    # Goal Operations

    def list_goals(self, user_id: str, domain: Optional[str] = None,
                   horizon: Optional[str] = None, status: Optional[str] = None) -> dict:
        """List goals with optional filters."""
        user, _, _, _ = self._load(user_id)
        goals = user.goals

        if domain:
            goals = [g for g in goals if g.domain == domain]
        if horizon:
            goals = [g for g in goals if g.time_horizon == horizon]
        if status:
            goals = [g for g in goals if g.status == status]

        return {
            "goals": [self._goal_to_dict(g) for g in goals],
            "total": len(goals)
        }

    def add_goal(self, user_id: str, description: str, domain: str,
                 time_horizon: str = "quarter", parent_goal_id: Optional[str] = None) -> dict:
        """Add a new goal."""
        user, state, _, _ = self._load(user_id)
        goal = Goal(
            id=str(uuid.uuid4()),
            domain=domain,
            description=description,
            time_horizon=time_horizon,
            parent_goal_id=parent_goal_id
        )
        user.add_goal(goal)
        self._save(user, state)
        return self._goal_to_dict(goal)

    def complete_goal(self, user_id: str, goal_id: str,
                      outcome: str = "success", notes: str = "") -> dict:
        """Mark a goal as completed."""
        user, state, _, _ = self._load(user_id)
        # Find by partial ID match
        full_id = self._resolve_goal_id(user, goal_id)
        if not full_id:
            raise ValueError(f"Goal '{goal_id}' not found")
        user.complete_goal(full_id, outcome=outcome, notes=notes)
        self._save(user, state)
        goal = user.get_goal(full_id)
        return self._goal_to_dict(goal)

    # Cycle Operations

    def run_cycle(self, user_id: str) -> dict:
        """Run a complete meta-loop cycle."""
        user, state, meta_loop, _ = self._load(user_id)
        plan = meta_loop.plan()
        result = meta_loop.run_cycle()
        state.meta_state.cycle_count += 1
        state.meta_state.last_execution = datetime.now()
        self._save(user, state)
        return {
            "cycle_completed": result.cycle_completed,
            "cycle_id": result.cycle_id,
            "phases_executed": result.phases_executed,
            "missions_created": result.missions_created,
            "strategies_count": len(plan.strategies),
            "tasks_count": len(plan.tasks),
            "agents_dispatched": 0
        }

    def run_daily_planning(self, user_id: str) -> dict:
        """Run daily planning cycle."""
        user, state, meta_loop, _ = self._load(user_id)
        result = meta_loop.run_daily_planning()
        self._save(user, state)
        return {
            "cycle_type": result.cycle_type,
            "date": datetime.now().date().isoformat(),
            "tasks": result.daily_plan.get("tasks", []) if result.daily_plan else []
        }

    def run_weekly_reflection(self, user_id: str) -> dict:
        """Run weekly reflection."""
        user, state, meta_loop, _ = self._load(user_id)
        result = meta_loop.run_weekly_reflection()
        self._save(user, state)
        return {
            "cycle_type": result.cycle_type,
            "insights": result.weekly_insights or {},
            "adjustments": result.adjustments_made or []
        }

    def run_monthly_planning(self, user_id: str) -> dict:
        """Run monthly planning."""
        user, state, meta_loop, _ = self._load(user_id)
        result = meta_loop.run_monthly_planning()
        self._save(user, state)
        return {
            "cycle_type": result.cycle_type,
            "goal_adjustments": result.goal_adjustments or []
        }

    # Daily Data Operations

    def record_daily_data(self, user_id: str, data: dict) -> dict:
        """Record daily metrics."""
        user, state, _, _ = self._load(user_id)
        user.record_daily_data(data)
        self._save(user, state)
        return {"message": "Daily data recorded", "date": data.get("date", datetime.now().date().isoformat())}

    def get_daily_data(self, user_id: str, date_str: str) -> dict:
        """Get daily data for a specific date."""
        user, _, _, _ = self._load(user_id)
        return user.get_daily_data(date_str)

    def get_weekly_stats(self, user_id: str, week_start: str) -> dict:
        """Get weekly aggregated stats."""
        user, _, _, _ = self._load(user_id)
        start_date = date.fromisoformat(week_start)
        return user.get_weekly_stats(start_date)

    def get_patterns(self, user_id: str) -> list:
        """Get detected patterns."""
        user, _, _, _ = self._load(user_id)
        patterns = user.detect_patterns()
        return [{"description": p.description, "confidence": p.confidence} for p in patterns]

    # Constitution Operations

    def get_constitution(self) -> dict:
        """Get the current constitution."""
        constitution = Constitution.load()
        principles = constitution.core_principles
        domains = constitution.get_life_domains()

        return {
            "version": constitution.version,
            "constitution_type": constitution.constitution_type,
            "principles": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "rules": p.rules,
                    "weight": p.weight
                }
                for p in principles
            ],
            "domains": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "metrics": d.metrics,
                    "minimum_standards": d.minimum_standards
                }
                for d in domains
            ]
        }

    # Helpers

    def _goal_to_dict(self, goal: Goal) -> dict:
        """Convert a Goal to a dict for API response."""
        return {
            "id": goal.id,
            "domain": goal.domain,
            "description": goal.description,
            "time_horizon": goal.time_horizon,
            "parent_goal_id": goal.parent_goal_id,
            "status": goal.status,
            "outcome": goal.outcome,
            "created_at": goal.created_at.isoformat(),
            "completed_at": goal.completed_at.isoformat() if goal.completed_at else None
        }

    def _resolve_goal_id(self, user: UserModel, partial_id: str) -> Optional[str]:
        """Resolve a partial goal ID to a full one."""
        for goal in user.goals:
            if goal.id.startswith(partial_id) or goal.id == partial_id:
                return goal.id
        return None
