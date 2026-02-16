"""
High-level tests for Meta-Loop (Consciousness Layer).
"""

import pytest
from datetime import datetime


class TestMetaLoopCycle:
    """Tests for the main meta-loop cycle."""

    def test_meta_loop_initialization(self):
        """Should initialize meta-loop with system state."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        assert meta_loop.state == state
        assert meta_loop.current_phase is None

    def test_meta_loop_full_cycle(self):
        """Should execute full cycle: Reflect -> Reason -> Plan -> Execute -> Evolve."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        user.set_purpose("Live healthily and productively")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        result = meta_loop.run_cycle()

        assert result.cycle_completed is True
        assert result.phases_executed == ["reflect", "reason", "plan", "execute", "evolve"]
        assert result.missions_created is not None  # Should create missions for sub-agents

    def test_reflect_phase(self):
        """Should analyze current life state and progress."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        user.set_purpose("Build a successful startup")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        reflection = meta_loop.reflect()

        assert reflection.life_state is not None
        assert "domains" in reflection.life_state  # Status of all life domains
        assert reflection.progress_summary is not None
        assert reflection.patterns_identified is not None

    def test_reason_phase(self):
        """Should identify goals gap and determine priorities."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel
        from alter.core.user_model import Goal

        user = UserModel.create_new(user_id="test_user")
        user.set_purpose("Master system design")
        user.add_goal(Goal(
            id="g1",
            domain="growth",
            description="Complete distributed systems course",
            time_horizon="quarter"
        ))

        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        reasoning = meta_loop.reason()

        assert reasoning.goals_gap is not None  # Gap between current and desired state
        assert len(reasoning.priorities) > 0  # Prioritized list of what to focus on
        assert reasoning.tradeoffs_considered is not None

    def test_plan_phase(self):
        """Should create concrete strategies and task delegation."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")
        user.set_purpose("Improve health and fitness")
        user.add_goal(Goal(
            id="g1",
            domain="health",
            description="Run 5k in under 25 minutes",
            time_horizon="month"
        ))

        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        plan = meta_loop.plan()

        assert len(plan.strategies) > 0
        assert len(plan.tasks) > 0
        assert len(plan.agent_missions) > 0  # Missions to delegate to sub-agents

    def test_execute_phase(self):
        """Should orchestrate sub-agents and monitor execution."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        # Create some missions
        missions = [
            {"agent_id": "research_agent", "mission": "Research productivity tools"},
            {"agent_id": "health_agent", "mission": "Analyze sleep patterns"}
        ]

        execution = meta_loop.execute(missions)

        assert execution.agents_dispatched is not None
        assert execution.monitoring_active is True

    def test_evolve_phase(self):
        """Should update user model and refine goals based on learnings."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        # Simulate some agent reports and outcomes
        agent_reports = [
            {"agent_id": "research_agent", "findings": "Productivity peaks in morning"},
            {"agent_id": "health_agent", "findings": "Sleep quality improves with exercise"}
        ]

        evolution = meta_loop.evolve(agent_reports)

        assert evolution.model_updated is True
        assert evolution.learnings is not None


class TestMetaLoopScheduling:
    """Tests for meta-loop execution scheduling."""

    def test_daily_tactical_planning(self):
        """Should run daily morning planning cycle."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        result = meta_loop.run_daily_planning()

        assert result.cycle_type == "daily_tactical"
        assert result.daily_plan is not None
        assert "tasks" in result.daily_plan

    def test_weekly_strategic_reflection(self):
        """Should run weekly deep reflection cycle."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        result = meta_loop.run_weekly_reflection()

        assert result.cycle_type == "weekly_strategic"
        assert result.weekly_insights is not None
        assert result.adjustments_made is not None

    def test_monthly_strategic_planning(self):
        """Should run monthly strategy review and goal adjustment."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        result = meta_loop.run_monthly_planning()

        assert result.cycle_type == "monthly_strategic"
        assert result.goal_adjustments is not None


class TestMetaLoopConstitutionIntegration:
    """Tests for constitution integration in meta-loop."""

    def test_all_decisions_validated_by_constitution(self):
        """Should validate every decision through constitution."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel
        from alter.core.constitution import Constitution

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        constitution = Constitution.load()
        meta_loop = MetaLoop(state=state, constitution=constitution)

        # Run a cycle and check that decisions were validated
        result = meta_loop.run_cycle()

        assert result.constitution_checks_performed > 0
        assert result.constitution_violations == 0  # No violations

    def test_plan_rejected_by_constitution(self):
        """Should reject plans that violate constitution."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel
        from alter.core.constitution import Constitution

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        constitution = Constitution.load()
        meta_loop = MetaLoop(state=state, constitution=constitution)

        # Try to create a plan that violates constitution (e.g., no sleep for a week)
        bad_plan = {
            "tasks": [
                {"task": "work_24_7", "impact": {"health": -10, "productivity": 5}}
            ]
        }

        validation = meta_loop.validate_plan(bad_plan)

        assert validation.approved is False
        assert "constitution" in validation.rejection_reason.lower()

    def test_constitution_override_applied(self):
        """Should respect active constitution overrides."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel
        from alter.core.constitution import Constitution

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        constitution = Constitution.load()

        # Activate temporary override
        constitution.request_override({
            "type": "temporary",
            "rule_id": "health/sleep_hours",
            "duration_days": 3,
            "reason": "Project deadline"
        })

        meta_loop = MetaLoop(state=state, constitution=constitution)

        # Plan that would normally violate sleep rule should now be allowed
        plan_with_less_sleep = {
            "tasks": [{"task": "work_late", "sleep_hours": 6}]
        }

        validation = meta_loop.validate_plan(plan_with_less_sleep)

        assert validation.approved is True
        assert validation.override_applied is True


class TestMetaLoopGoalManagement:
    """Tests for goal hierarchy and management."""

    def test_translate_life_purpose_to_goals(self):
        """Should break down life purpose into concrete goals."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        user.set_purpose("Build meaningful products that help people live better lives")

        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        goals = meta_loop.translate_purpose_to_goals()

        # Should create goals at different time horizons
        assert len(goals) > 0
        assert any(g.time_horizon == "5_year" for g in goals)
        assert any(g.time_horizon == "1_year" for g in goals)

    def test_cascade_goals_to_daily_tasks(self):
        """Should break down high-level goals into daily tasks."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")

        quarterly_goal = Goal(
            id="q1",
            domain="growth",
            description="Learn system design",
            time_horizon="quarter"
        )
        user.add_goal(quarterly_goal)

        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        daily_tasks = meta_loop.cascade_goals_to_daily_tasks(date="2026-02-10")

        assert len(daily_tasks) > 0
        # Tasks should trace back to quarterly goal
        assert any(t.parent_goal_id == "q1" for t in daily_tasks)

    def test_goal_conflict_resolution(self):
        """Should resolve conflicts between competing goals."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")

        # Conflicting goals: Career advancement vs. Family time
        goal1 = Goal(
            id="career",
            domain="wealth",
            description="Get promoted to senior engineer",
            time_horizon="quarter"
        )

        goal2 = Goal(
            id="family",
            domain="relationships",
            description="Spend quality time with family",
            time_horizon="quarter"
        )

        user.add_goal(goal1)
        user.add_goal(goal2)

        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        # Should detect conflict and propose resolution
        conflicts = meta_loop.detect_goal_conflicts()
        assert len(conflicts) > 0

        resolution = meta_loop.resolve_goal_conflict(conflicts[0])
        assert resolution.strategy is not None  # How to balance both goals


class TestMetaLoopLearning:
    """Tests for meta-loop learning and adaptation."""

    def test_learn_from_outcomes(self):
        """Should improve reasoning based on past outcomes."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        # Simulate several cycles with outcomes
        for i in range(5):
            result = meta_loop.run_cycle()
            # Record outcome: strategies that prioritized health had better results
            meta_loop.record_cycle_outcome(
                cycle_id=result.cycle_id,
                satisfaction=9 if "health" in str(result) else 5
            )

        learnings = meta_loop.extract_learnings()

        assert len(learnings) > 0
        # Should learn that health-focused strategies lead to better outcomes

    def test_adapt_planning_based_on_patterns(self):
        """Should adapt planning approach based on user patterns."""
        from alter.core.meta_loop import MetaLoop
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        # User consistently has high energy in mornings, low in evenings
        for day in range(14):
            user.record_daily_data({
                "date": f"2026-02-{day+1:02d}",
                "health": {
                    "energy_morning": 8,
                    "energy_evening": 4
                }
            })

        state = SystemState.create(user_model=user)
        meta_loop = MetaLoop(state=state)

        plan = meta_loop.plan()

        # Should schedule important tasks in morning
        morning_tasks = [t for t in plan.tasks if "morning" in t.scheduled_time]
        evening_tasks = [t for t in plan.tasks if "evening" in t.scheduled_time]

        assert len(morning_tasks) > len(evening_tasks)
