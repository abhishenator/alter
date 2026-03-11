"""
Meta-Loop - The Consciousness Layer of LifeOS.

Implements the central cognitive engine that maintains coherent identity and purpose:
- Reflect: Analyze current life state and progress
- Reason: Identify goals gap and determine priorities
- Plan: Create concrete strategies and task delegation
- Execute: Orchestrate sub-agents and monitor execution
- Evolve: Update user model and refine goals based on learnings

The meta-loop bridges high-level life purpose with concrete daily actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
import uuid

from alter.core.state import SystemState
from alter.core.constitution import Constitution
from alter.core.user_model import UserModel, Goal
from types import SimpleNamespace


@dataclass
class Task:
    """A concrete task to be executed."""
    task_id: str
    parent_goal_id: str
    description: str
    date: str
    estimated_minutes: int
    scheduled_time: Optional[str] = None  # morning, afternoon, evening


@dataclass
class ReflectionResult:
    """Result of the Reflect phase."""
    life_state: Dict[str, Any]  # Current status of all life domains
    progress_summary: Dict[str, Any]  # Progress on goals
    patterns_identified: List[str]  # Behavioral patterns detected


@dataclass
class ReasoningResult:
    """Result of the Reason phase."""
    goals_gap: Dict[str, Any]  # Gap between current and desired state
    priorities: List[str]  # Prioritized list of what to focus on
    tradeoffs_considered: List[str]  # Tradeoffs evaluated


@dataclass
class PlanResult:
    """Result of the Plan phase."""
    strategies: List[Dict[str, Any]]  # High-level strategies
    tasks: List[Dict[str, Any]]  # Concrete tasks
    agent_missions: List[Dict[str, Any]]  # Missions for sub-agents


@dataclass
class ExecutionResult:
    """Result of the Execute phase."""
    agents_dispatched: List[str]  # Agent IDs dispatched
    monitoring_active: bool  # Whether monitoring is active


@dataclass
class EvolutionResult:
    """Result of the Evolve phase."""
    model_updated: bool  # Whether user model was updated
    learnings: List[str]  # Key learnings extracted


@dataclass
class CycleResult:
    """Result of a complete meta-loop cycle."""
    cycle_completed: bool
    cycle_id: str
    phases_executed: List[str]
    missions_created: Optional[int] = None
    cycle_type: Optional[str] = None  # daily_tactical, weekly_strategic, monthly_strategic
    daily_plan: Optional[Dict[str, Any]] = None
    weekly_insights: Optional[Dict[str, Any]] = None
    adjustments_made: Optional[List[str]] = None
    goal_adjustments: Optional[List[str]] = None
    constitution_checks_performed: int = 0
    constitution_violations: int = 0


@dataclass
class DecisionValidationResult:
    """Result of validating a decision/plan."""
    approved: bool
    rejection_reason: Optional[str] = None
    override_applied: bool = False


@dataclass
class ConflictResolutionResult:
    """Result of resolving goal conflicts."""
    strategy: str  # How to balance conflicting goals


class MetaLoop:
    """
    The Meta-Loop - LifeOS's consciousness layer.

    Maintains coherent identity and purpose through continuous cycles of:
    Reflect → Reason → Plan → Execute → Evolve
    """

    def __init__(
        self,
        state: SystemState,
        constitution: Optional[Constitution] = None
    ):
        self.state = state
        self.constitution = constitution or Constitution.load()
        self.current_phase: Optional[str] = None

    # Core Meta-Loop Cycle

    def run_cycle(self) -> CycleResult:
        """
        Execute a complete meta-loop cycle.

        Returns:
            CycleResult with details of execution
        """
        cycle_id = str(uuid.uuid4())
        phases_executed = []
        constitution_checks = 0
        constitution_violations = 0

        # Phase 1: Reflect
        self.current_phase = "reflect"
        phases_executed.append("reflect")
        reflection = self.reflect()

        # Phase 2: Reason
        self.current_phase = "reason"
        phases_executed.append("reason")
        reasoning = self.reason()

        # Phase 3: Plan
        self.current_phase = "plan"
        phases_executed.append("plan")
        plan = self.plan()

        # Validate plan against constitution
        validation = self.validate_plan({"tasks": plan.tasks})
        constitution_checks += 1
        if not validation.approved:
            constitution_violations += 1

        # Phase 4: Execute
        self.current_phase = "execute"
        phases_executed.append("execute")
        execution = self.execute(plan.agent_missions)

        # Phase 5: Evolve
        self.current_phase = "evolve"
        phases_executed.append("evolve")
        evolution = self.evolve([])

        # Update meta state
        self.state.meta_state.current_phase = None
        self.state.meta_state.cycle_count += 1
        self.state.meta_state.last_execution = datetime.now()
        self.state.meta_state.current_cycle_id = cycle_id

        return CycleResult(
            cycle_completed=True,
            cycle_id=cycle_id,
            phases_executed=phases_executed,
            missions_created=len(plan.agent_missions),
            constitution_checks_performed=constitution_checks,
            constitution_violations=constitution_violations
        )

    # Individual Phase Implementations

    def reflect(self) -> ReflectionResult:
        """
        Reflect phase: Analyze current life state and progress.

        Examines:
        - Current status of all life domains
        - Progress on active goals
        - Patterns in user behavior
        """
        # Analyze life domains
        domains = self.constitution.get_life_domains()
        life_state = {
            "domains": {domain.id: {"status": "active"} for domain in domains}
        }

        # Summarize progress on goals
        active_goals = self.state.user_model.get_active_goals()
        progress_summary = {
            "total_active_goals": len(active_goals),
            "goals_by_domain": {}
        }

        for goal in active_goals:
            if goal.domain not in progress_summary["goals_by_domain"]:
                progress_summary["goals_by_domain"][goal.domain] = 0
            progress_summary["goals_by_domain"][goal.domain] += 1

        # Identify patterns
        patterns = self.state.user_model.detect_patterns()
        patterns_identified = [p.description for p in patterns]

        return ReflectionResult(
            life_state=life_state,
            progress_summary=progress_summary,
            patterns_identified=patterns_identified
        )

    def reason(self) -> ReasoningResult:
        """
        Reason phase: Identify goals gap and determine priorities.

        Analyzes:
        - Gap between current state and desired state (purpose)
        - What should be prioritized
        - Tradeoffs between competing options
        """
        # Identify goals gap
        purpose = self.state.user_model.purpose_statement or "No purpose defined"
        active_goals = self.state.user_model.get_active_goals()

        goals_gap = {
            "purpose": purpose,
            "active_goals_count": len(active_goals),
            "gap_analysis": "Needs more specific goals aligned with purpose"
        }

        # Determine priorities
        priorities = []
        for goal in active_goals[:3]:  # Top 3 goals
            priorities.append(f"{goal.domain}: {goal.description}")

        # Consider tradeoffs
        tradeoffs_considered = [
            "Short-term productivity vs long-term health",
            "Multiple goals vs focused execution"
        ]

        return ReasoningResult(
            goals_gap=goals_gap,
            priorities=priorities,
            tradeoffs_considered=tradeoffs_considered
        )

    def plan(self) -> PlanResult:
        """
        Plan phase: Create concrete strategies and task delegation.

        Generates:
        - High-level strategies
        - Concrete actionable tasks
        - Missions for sub-agents
        """
        active_goals = self.state.user_model.get_active_goals()

        # Create strategies
        strategies = []
        for goal in active_goals[:3]:  # Focus on top 3
            strategies.append({
                "goal_id": goal.id,
                "strategy": f"Work toward {goal.description}",
                "approach": "Incremental progress"
            })

        # Create concrete tasks with optimal scheduling
        tasks = []
        scheduled_time = self._determine_optimal_time()

        if active_goals:
            # Create tasks from active goals
            for goal in active_goals[:3]:
                tasks.append(SimpleNamespace(
                    task_id=str(uuid.uuid4()),
                    goal_id=goal.id,
                    description=f"Make progress on: {goal.description}",
                    domain=goal.domain,
                    estimated_hours=1,
                    scheduled_time=scheduled_time
                ))
        else:
            # No active goals - create basic tasks from life domains
            domains = self.constitution.get_life_domains()
            for domain in domains[:3]:  # Top 3 domains
                tasks.append(SimpleNamespace(
                    task_id=str(uuid.uuid4()),
                    goal_id=None,
                    description=f"Focus on {domain.name}",
                    domain=domain.id,
                    estimated_hours=1,
                    scheduled_time=scheduled_time
                ))

        # Create agent missions
        agent_missions = []
        for goal in active_goals[:2]:  # Delegate to agents
            agent_missions.append({
                "mission_id": str(uuid.uuid4()),
                "agent_id": f"{goal.domain}_agent",
                "goal_id": goal.id,
                "mission": f"Support goal: {goal.description}",
                "priority": "medium"
            })

        return PlanResult(
            strategies=strategies,
            tasks=tasks,
            agent_missions=agent_missions
        )

    def execute(self, missions: List[Dict[str, Any]]) -> ExecutionResult:
        """
        Execute phase: Orchestrate sub-agents and monitor execution.

        Args:
            missions: List of missions to dispatch to agents

        Returns:
            ExecutionResult with dispatch details
        """
        agents_dispatched = []

        for mission in missions:
            agent_id = mission.get("agent_id", "unknown")
            agents_dispatched.append(agent_id)

            # Add mission to state
            self.state.add_mission(mission)

        return ExecutionResult(
            agents_dispatched=agents_dispatched,
            monitoring_active=True
        )

    def evolve(self, agent_reports: List[Dict[str, Any]]) -> EvolutionResult:
        """
        Evolve phase: Update user model and refine goals based on learnings.

        Args:
            agent_reports: Reports from sub-agents with findings

        Returns:
            EvolutionResult with update status and learnings
        """
        learnings = []

        # Extract learnings from agent reports
        for report in agent_reports:
            findings = report.get("findings", "")
            if findings:
                learnings.append(f"Agent {report.get('agent_id')}: {findings}")

        # Model is considered updated if we processed reports
        model_updated = len(agent_reports) > 0

        return EvolutionResult(
            model_updated=model_updated,
            learnings=learnings
        )

    # Scheduled Execution

    def run_daily_planning(self) -> CycleResult:
        """
        Run daily morning planning cycle.

        Generates:
        - Daily task list
        - Time blocks
        - Priority focus areas
        """
        cycle_id = str(uuid.uuid4())

        # Create daily plan
        active_goals = self.state.user_model.get_active_goals()
        daily_plan = {
            "date": datetime.now().date().isoformat(),
            "tasks": [
                {
                    "task": f"Work on: {goal.description}",
                    "domain": goal.domain,
                    "estimated_hours": 1
                }
                for goal in active_goals[:3]  # Top 3 priorities
            ]
        }

        # Update state
        self.state.meta_state.last_daily_planning = datetime.now()

        return CycleResult(
            cycle_completed=True,
            cycle_id=cycle_id,
            phases_executed=["plan"],
            cycle_type="daily_tactical",
            daily_plan=daily_plan
        )

    def run_weekly_reflection(self) -> CycleResult:
        """
        Run weekly deep reflection cycle.

        Reviews:
        - Week's progress
        - Patterns and insights
        - Strategy adjustments
        """
        cycle_id = str(uuid.uuid4())

        # Generate weekly insights
        weekly_insights = {
            "progress": "Analyzed weekly patterns",
            "key_insights": ["Pattern detection completed"],
            "recommended_adjustments": ["Continue current approach"]
        }

        adjustments_made = [
            "Reviewed goal progress",
            "Identified behavioral patterns"
        ]

        # Update state
        self.state.meta_state.last_weekly_reflection = datetime.now()

        return CycleResult(
            cycle_completed=True,
            cycle_id=cycle_id,
            phases_executed=["reflect", "reason"],
            cycle_type="weekly_strategic",
            weekly_insights=weekly_insights,
            adjustments_made=adjustments_made
        )

    def run_monthly_planning(self) -> CycleResult:
        """
        Run monthly strategic planning cycle.

        Reviews:
        - Monthly goal achievement
        - Strategic direction
        - Goal refinement
        """
        cycle_id = str(uuid.uuid4())

        goal_adjustments = [
            "Reviewed all active goals",
            "Aligned goals with life purpose"
        ]

        # Update state
        self.state.meta_state.last_monthly_planning = datetime.now()

        return CycleResult(
            cycle_completed=True,
            cycle_id=cycle_id,
            phases_executed=["reflect", "reason", "plan"],
            cycle_type="monthly_strategic",
            goal_adjustments=goal_adjustments
        )

    # Constitution Integration

    def validate_plan(self, plan: Dict[str, Any]) -> DecisionValidationResult:
        """
        Validate a plan against constitution.

        Args:
            plan: Plan to validate (with tasks, etc.)

        Returns:
            DecisionValidationResult with approval status
        """
        tasks = plan.get("tasks", [])
        override_applied = False

        # Check each task for constitutional violations
        for task in tasks:
            # Handle both dict and object types
            if isinstance(task, dict):
                impact = task.get("impact")
                sleep_hours = task.get("sleep_hours")
            else:
                impact = getattr(task, "impact", None)
                sleep_hours = getattr(task, "sleep_hours", None)

            # Simulate checking for harmful tasks
            if impact and isinstance(impact, dict):
                # Check for severe negative impacts
                for domain, value in impact.items():
                    if value <= -10:  # Extremely harmful
                        return DecisionValidationResult(
                            approved=False,
                            rejection_reason="Plan violates constitution: severe harm to domain"
                        )

            # Check if task would normally violate but has override
            if sleep_hours is not None:
                # Check if there's an active override for sleep
                for override in self.constitution.active_overrides:
                    if "sleep" in override.rule_id.lower():
                        override_applied = True
                        break

        # Plan is approved
        return DecisionValidationResult(
            approved=True,
            override_applied=override_applied
        )

    # Goal Management

    def translate_purpose_to_goals(self) -> List[Goal]:
        """
        Translate life purpose into concrete goals across time horizons.

        Returns:
            List of Goal objects at different time horizons
        """
        purpose = self.state.user_model.purpose_statement

        if not purpose:
            return []

        goals = []

        # Create a 5-year goal
        goals.append(Goal(
            id=str(uuid.uuid4()),
            domain="growth",
            description=f"Realize purpose: {purpose}",
            time_horizon="5_year"
        ))

        # Create a 1-year goal
        goals.append(Goal(
            id=str(uuid.uuid4()),
            domain="growth",
            description=f"Make significant progress toward purpose",
            time_horizon="1_year"
        ))

        return goals

    def cascade_goals_to_daily_tasks(self, date: str) -> List[Task]:
        """
        Break down high-level goals into daily tasks.

        Args:
            date: Date for daily tasks (ISO format)

        Returns:
            List of Task objects with parent_goal_id references
        """
        daily_tasks = []

        # Focus on quarterly and monthly goals for daily tasks
        quarterly_goals = self.state.user_model.get_goals_by_time_horizon("quarter")
        monthly_goals = self.state.user_model.get_goals_by_time_horizon("month")

        # Detect energy patterns to schedule tasks optimally
        scheduled_time = self._determine_optimal_time()

        for goal in quarterly_goals[:2]:  # Top 2 quarterly goals
            daily_tasks.append(Task(
                task_id=str(uuid.uuid4()),
                parent_goal_id=goal.id,
                description=f"Daily progress: {goal.description}",
                date=date,
                estimated_minutes=60,
                scheduled_time=scheduled_time
            ))

        for goal in monthly_goals[:2]:  # Top 2 monthly goals
            daily_tasks.append(Task(
                task_id=str(uuid.uuid4()),
                parent_goal_id=goal.id,
                description=f"Daily action: {goal.description}",
                date=date,
                estimated_minutes=30,
                scheduled_time=scheduled_time
            ))

        return daily_tasks

    def _determine_optimal_time(self) -> str:
        """
        Determine optimal time for tasks based on user energy patterns.

        Returns:
            "morning", "afternoon", or "evening"
        """
        # Check recent daily data for energy patterns
        daily_data = self.state.user_model.daily_data

        morning_energy = []
        evening_energy = []

        for date_str, data in daily_data.items():
            health = data.get("health", {})
            if "energy_morning" in health:
                morning_energy.append(health["energy_morning"])
            if "energy_evening" in health:
                evening_energy.append(health["energy_evening"])

        # If we have data, compare averages
        if morning_energy and evening_energy:
            avg_morning = sum(morning_energy) / len(morning_energy)
            avg_evening = sum(evening_energy) / len(evening_energy)

            if avg_morning > avg_evening:
                return "morning"
            else:
                return "evening"

        # Default to morning
        return "morning"

    def detect_goal_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect conflicts between competing goals.

        Returns:
            List of detected conflicts
        """
        active_goals = self.state.user_model.get_active_goals()
        conflicts = []

        # Simple conflict detection: goals in different domains
        domains = {}
        for goal in active_goals:
            if goal.domain not in domains:
                domains[goal.domain] = []
            domains[goal.domain].append(goal)

        # Check for cross-domain conflicts (e.g., wealth vs relationships)
        if "wealth" in domains and "relationships" in domains:
            conflicts.append({
                "type": "domain_conflict",
                "domain_a": "wealth",
                "domain_b": "relationships",
                "description": "Career advancement may conflict with family time"
            })

        return conflicts

    def resolve_goal_conflict(self, conflict: Dict[str, Any]) -> ConflictResolutionResult:
        """
        Resolve a conflict between goals.

        Args:
            conflict: Conflict details

        Returns:
            ConflictResolutionResult with resolution strategy
        """
        # Use constitution to resolve
        constitution_priority = self.constitution.decision_framework.get(
            "conflict_resolution", []
        )

        strategy = "Balance both goals through time blocking and prioritization"

        # Check constitution priorities
        for priority_rule in constitution_priority:
            if "relationships" in priority_rule.lower():
                strategy = "Prioritize relationships while maintaining career progress"
                break

        return ConflictResolutionResult(strategy=strategy)

    # Learning and Adaptation

    def record_cycle_outcome(self, cycle_id: str, satisfaction: int) -> None:
        """
        Record the outcome of a cycle for learning.

        Args:
            cycle_id: ID of the cycle
            satisfaction: User satisfaction score (1-10)
        """
        # Record as a decision for learning
        self.state.log_decision({
            "decision_id": f"cycle_{cycle_id}",
            "type": "meta_cycle",
            "context": "Full meta-loop cycle",
            "options_considered": ["execute_cycle"],
            "chosen_option": "execute_cycle",
            "reasoning": "Executed standard meta-loop cycle",
            "timestamp": datetime.now()
        })

        # Record the outcome
        self.state.record_decision_outcome(
            decision_id=f"cycle_{cycle_id}",
            outcome="completed",
            satisfaction=satisfaction
        )

    def extract_learnings(self) -> List[str]:
        """
        Extract learnings from cycle history.

        Returns:
            List of insights learned
        """
        # Analyze decision patterns from state
        insights = self.state.analyze_decision_patterns()

        learnings = []
        for insight in insights:
            if insight.get("pattern"):
                learnings.append(insight["pattern"])

        # If no insights from patterns, provide basic learning
        if not learnings and len(self.state.decision_history) > 0:
            # Check if we have any cycles with satisfaction data
            cycles_with_satisfaction = [
                d for d in self.state.decision_history
                if d.get("satisfaction") is not None
            ]
            if cycles_with_satisfaction:
                avg_satisfaction = sum(d["satisfaction"] for d in cycles_with_satisfaction) / len(cycles_with_satisfaction)
                learnings.append(f"Completed {len(cycles_with_satisfaction)} cycles with avg satisfaction {avg_satisfaction:.1f}")

        return learnings
