"""
System State Management - Tracks the entire ALTER system state.

Manages:
- User model (identity, goals, preferences)
- Meta-loop state (current phase, cycle count)
- Agent states (status, missions)
- Decision history and outcomes
- System checkpointing and persistence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from collections import defaultdict

from alter.core.user_model import UserModel


@dataclass
class MetaLoopState:
    """State of the meta-loop execution."""
    current_phase: Optional[str] = None  # reflect, reason, plan, execute, evolve
    cycle_count: int = 0
    last_execution: Optional[datetime] = None
    last_daily_planning: Optional[datetime] = None
    last_weekly_reflection: Optional[datetime] = None
    last_monthly_planning: Optional[datetime] = None
    current_cycle_id: Optional[str] = None


@dataclass
class AgentState:
    """State of a sub-agent."""
    agent_id: str
    status: str  # idle, running, completed, failed
    current_mission_id: Optional[str] = None
    last_execution: Optional[datetime] = None
    total_missions_completed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """A decision made by the meta-loop."""
    decision_id: str
    type: str
    context: str
    options_considered: List[str]
    chosen_option: str
    reasoning: str
    timestamp: datetime
    outcome: Optional[str] = None  # success, partial, failure
    actual_result: Optional[str] = None
    satisfaction: Optional[int] = None  # 1-10
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemState:
    """
    Central state management for the ALTER system.

    This class maintains the complete state of the system including:
    - User model (who they are, what they want)
    - Meta-loop state (where we are in the cycle)
    - Agent states (what agents are doing)
    - Decision history (what we've decided and how it worked out)
    """

    def __init__(
        self,
        user_model: UserModel,
        meta_state: Optional[MetaLoopState] = None,
        agent_states: Optional[Dict[str, AgentState]] = None,
        decision_history: Optional[List[Decision]] = None,
        missions: Optional[List[Dict[str, Any]]] = None,
        reports: Optional[List[Dict[str, Any]]] = None
    ):
        self.user_model = user_model
        self.meta_state = meta_state or MetaLoopState()
        self.agent_states = agent_states or {}
        self.decision_history = decision_history or []
        self.missions = missions or []  # Pending/active missions
        self.reports = reports or []  # Agent reports

    @classmethod
    def create(cls, user_model: UserModel) -> SystemState:
        """Create a new system state with initialized components."""
        return cls(user_model=user_model)

    # Decision Management

    def log_decision(self, decision: Dict[str, Any]) -> None:
        """
        Log a decision made by the meta-loop.

        Args:
            decision: Dict with decision details (decision_id, type, context, etc.)
        """
        # Store as dict with full structure
        decision_entry = {
            "decision_id": decision.get("decision_id", ""),
            "type": decision.get("type", ""),
            "context": decision.get("context", ""),
            "options_considered": decision.get("options_considered", []),
            "chosen_option": decision.get("chosen_option", ""),
            "reasoning": decision.get("reasoning", ""),
            "timestamp": decision.get("timestamp", datetime.now()),
            "outcome": None,
            "actual_result": None,
            "satisfaction": None,
            "metadata": decision.get("metadata", {})
        }

        self.decision_history.append(decision_entry)

    def record_decision_outcome(
        self,
        decision_id: str,
        outcome: str,
        actual_result: Optional[str] = None,
        satisfaction: Optional[int] = None
    ) -> None:
        """Record the outcome of a decision for learning."""
        for decision in self.decision_history:
            if decision["decision_id"] == decision_id:
                decision["outcome"] = outcome
                decision["actual_result"] = actual_result
                decision["satisfaction"] = satisfaction
                break

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific decision by ID."""
        for decision in self.decision_history:
            if decision["decision_id"] == decision_id:
                return decision
        return None

    def analyze_decision_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyze decision history to identify patterns.

        Returns insights about which types of decisions lead to good outcomes.
        """
        insights = []

        # Group decisions by type
        type_outcomes: Dict[str, List[int]] = defaultdict(list)

        for decision in self.decision_history:
            if decision.get("outcome") and decision.get("satisfaction") is not None:
                type_outcomes[decision["type"]].append(decision["satisfaction"])

        # Analyze which types have better outcomes
        for decision_type, satisfactions in type_outcomes.items():
            if len(satisfactions) >= 3:  # Need at least 3 data points
                avg_satisfaction = sum(satisfactions) / len(satisfactions)

                if avg_satisfaction >= 7:
                    insights.append({
                        "pattern": f"{decision_type} decisions have high success rate",
                        "decision_type": decision_type,
                        "avg_satisfaction": avg_satisfaction,
                        "sample_size": len(satisfactions),
                        "recommendation": f"Continue with current approach for {decision_type}"
                    })
                elif avg_satisfaction <= 4:
                    insights.append({
                        "pattern": f"{decision_type} decisions have low success rate",
                        "decision_type": decision_type,
                        "avg_satisfaction": avg_satisfaction,
                        "sample_size": len(satisfactions),
                        "recommendation": f"Review and adjust approach for {decision_type}"
                    })

        # Temporal patterns
        insights.extend(self._analyze_temporal_patterns())

        return insights

    def _analyze_temporal_patterns(self) -> List[Dict[str, Any]]:
        """Analyze time-based patterns in decisions."""
        patterns = []

        # Group by time of day (simple implementation)
        morning_decisions = []
        evening_decisions = []

        for decision in self.decision_history:
            satisfaction = decision.get("satisfaction")
            if satisfaction is not None:
                timestamp = decision.get("timestamp")
                if isinstance(timestamp, datetime):
                    hour = timestamp.hour
                elif isinstance(timestamp, str):
                    hour = datetime.fromisoformat(timestamp).hour
                else:
                    continue

                if 6 <= hour < 12:
                    morning_decisions.append(satisfaction)
                elif 18 <= hour < 24:
                    evening_decisions.append(satisfaction)

        # Compare morning vs evening decision quality
        if len(morning_decisions) >= 3 and len(evening_decisions) >= 3:
            morning_avg = sum(morning_decisions) / len(morning_decisions)
            evening_avg = sum(evening_decisions) / len(evening_decisions)

            if morning_avg > evening_avg + 1:
                patterns.append({
                    "pattern": "Morning decisions tend to have better outcomes",
                    "morning_avg": morning_avg,
                    "evening_avg": evening_avg,
                    "recommendation": "Schedule important decisions in the morning"
                })

        return patterns

    # Agent State Management

    def update_agent_state(self, agent_id: str, state: AgentState) -> None:
        """Update the state of a specific agent."""
        self.agent_states[agent_id] = state

    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get the current state of an agent."""
        return self.agent_states.get(agent_id)

    def get_active_agents(self) -> List[str]:
        """Get list of currently active agent IDs."""
        return [
            agent_id
            for agent_id, state in self.agent_states.items()
            if state.status == "running"
        ]

    # Mission Management

    def add_mission(self, mission: Dict[str, Any]) -> None:
        """Add a mission to the queue."""
        self.missions.append(mission)

    def get_pending_missions(self) -> List[Dict[str, Any]]:
        """Get all pending missions."""
        return [m for m in self.missions if m.get("status") == "pending"]

    # Report Management

    def add_report(self, report: Dict[str, Any]) -> None:
        """Add an agent report."""
        self.reports.append(report)

    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent agent reports."""
        return sorted(
            self.reports,
            key=lambda r: r.get("timestamp", datetime.min),
            reverse=True
        )[:limit]

    # Persistence

    def to_dict(self) -> Dict[str, Any]:
        """Serialize system state to dictionary."""
        return {
            "user_model": self.user_model.to_dict(),
            "meta_state": {
                "current_phase": self.meta_state.current_phase,
                "cycle_count": self.meta_state.cycle_count,
                "last_execution": self.meta_state.last_execution.isoformat() if self.meta_state.last_execution else None,
                "last_daily_planning": self.meta_state.last_daily_planning.isoformat() if self.meta_state.last_daily_planning else None,
                "last_weekly_reflection": self.meta_state.last_weekly_reflection.isoformat() if self.meta_state.last_weekly_reflection else None,
                "last_monthly_planning": self.meta_state.last_monthly_planning.isoformat() if self.meta_state.last_monthly_planning else None,
                "current_cycle_id": self.meta_state.current_cycle_id
            },
            "agent_states": {
                agent_id: {
                    "agent_id": state.agent_id,
                    "status": state.status,
                    "current_mission_id": state.current_mission_id,
                    "last_execution": state.last_execution.isoformat() if state.last_execution else None,
                    "total_missions_completed": state.total_missions_completed,
                    "metadata": state.metadata
                }
                for agent_id, state in self.agent_states.items()
            },
            "decision_history": [
                {
                    **d,
                    "timestamp": d["timestamp"].isoformat() if isinstance(d["timestamp"], datetime) else d["timestamp"]
                }
                for d in self.decision_history
            ],
            "missions": self.missions,
            "reports": self.reports
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SystemState:
        """Deserialize system state from dictionary."""
        # Parse user model
        user_model = UserModel.from_dict(data["user_model"])

        # Parse meta state
        meta_data = data.get("meta_state", {})
        meta_state = MetaLoopState(
            current_phase=meta_data.get("current_phase"),
            cycle_count=meta_data.get("cycle_count", 0),
            last_execution=datetime.fromisoformat(meta_data["last_execution"]) if meta_data.get("last_execution") else None,
            last_daily_planning=datetime.fromisoformat(meta_data["last_daily_planning"]) if meta_data.get("last_daily_planning") else None,
            last_weekly_reflection=datetime.fromisoformat(meta_data["last_weekly_reflection"]) if meta_data.get("last_weekly_reflection") else None,
            last_monthly_planning=datetime.fromisoformat(meta_data["last_monthly_planning"]) if meta_data.get("last_monthly_planning") else None,
            current_cycle_id=meta_data.get("current_cycle_id")
        )

        # Parse agent states
        agent_states = {}
        for agent_id, agent_data in data.get("agent_states", {}).items():
            agent_states[agent_id] = AgentState(
                agent_id=agent_data["agent_id"],
                status=agent_data["status"],
                current_mission_id=agent_data.get("current_mission_id"),
                last_execution=datetime.fromisoformat(agent_data["last_execution"]) if agent_data.get("last_execution") else None,
                total_missions_completed=agent_data.get("total_missions_completed", 0),
                metadata=agent_data.get("metadata", {})
            )

        # Parse decision history (stored as dicts)
        decision_history = []
        for d in data.get("decision_history", []):
            decision_entry = {**d}
            # Convert timestamp string back to datetime
            if isinstance(d.get("timestamp"), str):
                decision_entry["timestamp"] = datetime.fromisoformat(d["timestamp"])
            decision_history.append(decision_entry)

        return cls(
            user_model=user_model,
            meta_state=meta_state,
            agent_states=agent_states,
            decision_history=decision_history,
            missions=data.get("missions", []),
            reports=data.get("reports", [])
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Save system state to disk."""
        if path is None:
            path = Path(f"data/user_data/{self.user_model.user_id}/system_state.json")

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, user_id: str, path: Optional[Path] = None) -> SystemState:
        """Load system state from disk."""
        if path is None:
            path = Path(f"data/user_data/{user_id}/system_state.json")

        with open(path, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)
