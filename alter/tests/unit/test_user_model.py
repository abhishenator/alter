"""
High-level tests for User Model and State Management.
"""

import pytest
from datetime import datetime, timedelta


class TestUserModel:
    """Tests for user identity and goal model."""

    def test_create_new_user_model(self):
        """Should create new user model with default values."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        assert user.user_id == "test_user"
        assert user.purpose_statement is None  # Not yet defined
        assert len(user.goals) == 0
        assert user.created_at is not None

    def test_set_purpose_statement(self):
        """Should allow setting and updating life purpose."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        purpose = "Help others grow through technology and compassion"
        user.set_purpose(purpose)

        assert user.purpose_statement == purpose
        assert len(user.purpose_history) == 1

    def test_purpose_evolution_tracked(self):
        """Should track evolution of purpose over time."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        user.set_purpose("Purpose v1")
        user.set_purpose("Purpose v2")
        user.set_purpose("Purpose v3")

        assert len(user.purpose_history) == 3
        assert user.purpose_history[0].statement == "Purpose v1"
        assert user.purpose_statement == "Purpose v3"

    def test_add_goal_with_hierarchy(self):
        """Should support hierarchical goals (life -> 5yr -> 1yr -> quarter -> etc)."""
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")

        life_goal = Goal(
            id="life_1",
            domain="health",
            description="Maintain vibrant health throughout life",
            time_horizon="life"
        )

        year_goal = Goal(
            id="year_1",
            domain="health",
            description="Run a marathon",
            time_horizon="1_year",
            parent_goal_id="life_1"
        )

        user.add_goal(life_goal)
        user.add_goal(year_goal)

        assert len(user.goals) == 2
        assert user.get_goal("year_1").parent_goal_id == "life_1"

    def test_get_goals_by_time_horizon(self):
        """Should retrieve goals filtered by time horizon."""
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")

        user.add_goal(Goal(id="g1", domain="health", description="Goal 1", time_horizon="life"))
        user.add_goal(Goal(id="g2", domain="health", description="Goal 2", time_horizon="1_year"))
        user.add_goal(Goal(id="g3", domain="health", description="Goal 3", time_horizon="quarter"))

        quarterly_goals = user.get_goals_by_time_horizon("quarter")

        assert len(quarterly_goals) == 1
        assert quarterly_goals[0].id == "g3"

    def test_get_goals_by_domain(self):
        """Should retrieve goals filtered by life domain."""
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")

        user.add_goal(Goal(id="g1", domain="health", description="Health goal", time_horizon="quarter"))
        user.add_goal(Goal(id="g2", domain="wealth", description="Wealth goal", time_horizon="quarter"))
        user.add_goal(Goal(id="g3", domain="health", description="Health goal 2", time_horizon="quarter"))

        health_goals = user.get_goals_by_domain("health")

        assert len(health_goals) == 2

    def test_mark_goal_completed(self):
        """Should track goal completion and outcomes."""
        from alter.core.user_model import UserModel, Goal

        user = UserModel.create_new(user_id="test_user")

        goal = Goal(id="g1", domain="health", description="Run 5k", time_horizon="month")
        user.add_goal(goal)

        user.complete_goal("g1", outcome="success", notes="Ran 5k in 25 minutes")

        completed_goal = user.get_goal("g1")
        assert completed_goal.status == "completed"
        assert completed_goal.outcome == "success"


class TestPersonalityModel:
    """Tests for personality and preference tracking."""

    def test_initialize_personality_traits(self):
        """Should support personality trait definition."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        user.set_personality_traits({
            "openness": 8,
            "conscientiousness": 7,
            "extraversion": 5,
            "agreeableness": 9,
            "neuroticism": 3
        })

        assert user.personality_traits["openness"] == 8

    def test_track_preferences(self):
        """Should learn and track user preferences."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        user.set_preference("morning_person", True)
        user.set_preference("preferred_work_hours", "9am-5pm")
        user.set_preference("notification_style", "minimal")

        assert user.get_preference("morning_person") is True

    def test_track_strengths_and_growth_areas(self):
        """Should track identified strengths and growth areas."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        user.add_strength("System design")
        user.add_strength("Empathy")
        user.add_growth_area("Public speaking")

        assert "System design" in user.strengths
        assert "Public speaking" in user.growth_areas


class TestSystemState:
    """Tests for system state management."""

    def test_create_system_state(self):
        """Should create and initialize system state."""
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)

        assert state.user_model.user_id == "test_user"
        assert state.meta_state is not None
        assert state.agent_states == {}

    def test_meta_loop_state_tracking(self):
        """Should track meta-loop execution state."""
        from alter.core.state import SystemState, MetaLoopState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)

        # Simulate meta-loop cycle
        state.meta_state.current_phase = "reflect"
        state.meta_state.cycle_count = 1
        state.meta_state.last_execution = datetime.now()

        assert state.meta_state.current_phase == "reflect"

    def test_agent_state_tracking(self):
        """Should track individual agent states."""
        from alter.core.state import SystemState, AgentState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)

        # Add agent state
        agent_state = AgentState(
            agent_id="research_agent",
            status="running",
            current_mission_id="mission_1"
        )
        state.agent_states["research_agent"] = agent_state

        assert state.agent_states["research_agent"].status == "running"

    def test_save_and_load_state(self):
        """Should persist and restore system state."""
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        user.set_purpose("Test purpose")

        state = SystemState.create(user_model=user)
        state.save()

        # Load state
        loaded_state = SystemState.load(user_id="test_user")

        assert loaded_state.user_model.user_id == "test_user"
        assert loaded_state.user_model.purpose_statement == "Test purpose"


class TestLifeData:
    """Tests for life data tracking and aggregation."""

    def test_record_daily_data(self):
        """Should record daily metrics across domains."""
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")

        user.record_daily_data({
            "date": "2026-02-10",
            "health": {
                "sleep_hours": 7.5,
                "exercise_minutes": 45,
                "energy_level": 8
            },
            "emotions": {
                "mood": 7,
                "stress": 4
            }
        })

        daily_data = user.get_daily_data("2026-02-10")
        assert daily_data["health"]["sleep_hours"] == 7.5

    def test_aggregate_weekly_metrics(self):
        """Should aggregate data over weekly periods."""
        from alter.core.user_model import UserModel
        from datetime import date, timedelta

        user = UserModel.create_new(user_id="test_user")

        # Record 7 days of data
        base_date = date(2026, 2, 10)
        for i in range(7):
            user.record_daily_data({
                "date": (base_date + timedelta(days=i)).isoformat(),
                "health": {
                    "sleep_hours": 7 + (i % 2),  # Alternating 7 and 8
                    "exercise_minutes": 30 + (i * 5)
                }
            })

        weekly_stats = user.get_weekly_stats(base_date)

        assert "health" in weekly_stats
        assert "sleep_hours_avg" in weekly_stats["health"]

    def test_detect_patterns_over_time(self):
        """Should identify patterns in user behavior."""
        from alter.core.user_model import UserModel
        from datetime import date, timedelta

        user = UserModel.create_new(user_id="test_user")

        # Record consistent pattern: low energy on Mondays
        base_date = date(2026, 2, 10)  # Monday
        for week in range(4):
            for day in range(7):
                current_date = base_date + timedelta(weeks=week, days=day)
                energy = 5 if day == 0 else 8  # Monday is low

                user.record_daily_data({
                    "date": current_date.isoformat(),
                    "health": {"energy_level": energy}
                })

        patterns = user.detect_patterns()

        # Should detect "low energy on Mondays" pattern
        assert len(patterns) > 0
        assert any("monday" in p.description.lower() for p in patterns)


class TestDecisionHistory:
    """Tests for tracking system decisions and outcomes."""

    def test_log_decision(self):
        """Should log meta-loop decisions with reasoning."""
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)

        decision = {
            "decision_id": "dec_1",
            "type": "goal_prioritization",
            "context": "Morning planning",
            "options_considered": ["Option A", "Option B"],
            "chosen_option": "Option A",
            "reasoning": "Aligns better with long-term health goals",
            "timestamp": datetime.now()
        }

        state.log_decision(decision)

        assert len(state.decision_history) == 1
        assert state.decision_history[0]["decision_id"] == "dec_1"

    def test_track_decision_outcomes(self):
        """Should track actual outcomes of decisions for learning."""
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)

        decision = {
            "decision_id": "dec_1",
            "chosen_option": "Work on project A"
        }
        state.log_decision(decision)

        # Later: record outcome
        state.record_decision_outcome(
            decision_id="dec_1",
            outcome="success",
            actual_result="Project completed on time, high quality",
            satisfaction=8
        )

        decision_with_outcome = state.get_decision("dec_1")
        assert decision_with_outcome["outcome"] == "success"
        assert decision_with_outcome["satisfaction"] == 8

    def test_learn_from_decision_patterns(self):
        """Should identify which types of decisions lead to good outcomes."""
        from alter.core.state import SystemState
        from alter.core.user_model import UserModel

        user = UserModel.create_new(user_id="test_user")
        state = SystemState.create(user_model=user)

        # Log several decisions with outcomes
        for i in range(10):
            decision = {
                "decision_id": f"dec_{i}",
                "type": "morning_routine" if i < 5 else "evening_routine",
                "chosen_option": f"Option {i}"
            }
            state.log_decision(decision)

            # Morning routines work well, evening ones don't
            outcome = "success" if i < 5 else "failure"
            state.record_decision_outcome(f"dec_{i}", outcome=outcome, satisfaction=8 if i < 5 else 3)

        insights = state.analyze_decision_patterns()

        # Should learn that morning_routine decisions have better outcomes
        assert len(insights) > 0
        assert any("morning_routine" in str(i) for i in insights)
