"""
Tests for the Consciousness Layer — Phases C1, C2, C3, C4, C5, and C6.

Tests cover:
- Config: severity classification
- State: ConsciousnessState, WorldModel, Observation, DormantQuestion
- Observe: prediction error math, observation from daily data
- Context: context assembly per tick type, token budgets, section formatting
- Prompts: prompt building, cognitive architecture structure
- Parse: TickResult parsing, JSON extraction, fallback strategies
- Engine: ConsciousnessEngine tick/apply/observe (C3)
- Engine async: hourly_observe_async (C3)
- Adapter: StandaloneAdapter lifecycle, activity log, triggers (C4)
- Readiness: dormant question readiness tracking, signal matching (C5)
- Narrative: narrative history tracking, continuity (C5)
- Context: ready questions in context assembly (C5)
- Prompts: narrative continuity, ready question resolution (C5)
- OpenClaw: adapter, tools, session protocol, notification delivery (C6)
"""

import pytest
import json
from datetime import datetime, timedelta


# ─── Config Tests ───


class TestConfig:
    """Tests for consciousness configuration."""

    def test_classify_severity_normal(self):
        from alter.consciousness.config import classify_severity, Severity
        assert classify_severity(0.0) == Severity.NORMAL
        assert classify_severity(0.3) == Severity.NORMAL
        assert classify_severity(0.49) == Severity.NORMAL

    def test_classify_severity_elevated(self):
        from alter.consciousness.config import classify_severity, Severity
        assert classify_severity(0.5) == Severity.ELEVATED
        assert classify_severity(0.7) == Severity.ELEVATED
        assert classify_severity(0.79) == Severity.ELEVATED

    def test_classify_severity_critical(self):
        from alter.consciousness.config import classify_severity, Severity
        assert classify_severity(0.8) == Severity.CRITICAL
        assert classify_severity(0.9) == Severity.CRITICAL
        assert classify_severity(1.0) == Severity.CRITICAL

    def test_tick_type_values(self):
        from alter.consciousness.config import TickType
        assert TickType.HOURLY_PULSE.value == "hourly_pulse"
        assert TickType.DAILY_REVIEW.value == "daily_review"
        assert TickType.WEEKLY_REFLECT.value == "weekly_reflect"
        assert TickType.MONTHLY_DEEP.value == "monthly_deep"
        assert TickType.URGENT.value == "urgent"


# ─── Expectation Tests ───


class TestExpectation:
    """Tests for the Expectation dataclass."""

    def test_create_expectation(self):
        from alter.consciousness.state import Expectation
        exp = Expectation(
            domain="health",
            aspect="sleep",
            description="Sleeps 7-8 hours on weeknights",
            numeric_value=7.5,
            numeric_range=(7.0, 8.0),
            data_field="sleep_hours",
            confidence=0.8,
            data_points=14,
        )
        assert exp.domain == "health"
        assert exp.aspect == "sleep"
        assert exp.numeric_value == 7.5
        assert exp.confidence == 0.8

    def test_update_confidence_from_data_points(self):
        from alter.consciousness.state import Expectation
        exp = Expectation(domain="health", aspect="sleep", description="test")

        exp.data_points = 1
        exp.update_confidence()
        assert exp.confidence == 0.1

        exp.data_points = 7
        exp.update_confidence()
        assert exp.confidence == 0.5

        exp.data_points = 30
        exp.update_confidence()
        assert exp.confidence == 0.9

    def test_serialization_roundtrip(self):
        from alter.consciousness.state import Expectation
        exp = Expectation(
            domain="health",
            aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5,
            numeric_range=(7.0, 8.0),
            data_field="sleep_hours",
            confidence=0.7,
            data_points=10,
        )
        data = exp.to_dict()
        restored = Expectation.from_dict(data)
        assert restored.domain == exp.domain
        assert restored.aspect == exp.aspect
        assert restored.numeric_value == exp.numeric_value
        assert restored.numeric_range == exp.numeric_range
        assert restored.confidence == exp.confidence


# ─── World Model Tests ───


class TestWorldModel:
    """Tests for the WorldModel."""

    def test_empty_world_model(self):
        from alter.consciousness.state import WorldModel
        wm = WorldModel()
        assert wm.get_all_expectations() == []
        assert wm.get_domains() == []

    def test_set_and_get_expectation(self):
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        exp = Expectation(
            domain="health", aspect="sleep",
            description="7-8 hours", numeric_value=7.5,
            data_field="sleep_hours", confidence=0.7,
        )
        wm.set_expectation(exp)

        result = wm.get_expectation("health", "sleep")
        assert result is not None
        assert result.numeric_value == 7.5

    def test_update_existing_expectation(self):
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()

        exp1 = Expectation(domain="health", aspect="sleep", description="7h", numeric_value=7.0)
        wm.set_expectation(exp1)

        exp2 = Expectation(domain="health", aspect="sleep", description="8h", numeric_value=8.0)
        wm.set_expectation(exp2)

        # Should replace, not duplicate
        assert len(wm.expectations["health"]) == 1
        assert wm.get_expectation("health", "sleep").numeric_value == 8.0

    def test_get_numeric_expectations(self):
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        wm.set_expectation(Expectation(
            domain="health", aspect="sleep", description="7h",
            numeric_value=7.0, data_field="sleep_hours",
        ))
        wm.set_expectation(Expectation(
            domain="health", aspect="energy_pattern", description="high mornings",
            # No numeric_value → qualitative only
        ))

        numeric = wm.get_numeric_expectations()
        assert len(numeric) == 1
        assert numeric[0].aspect == "sleep"

    def test_serialization_roundtrip(self):
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        wm.set_expectation(Expectation(
            domain="health", aspect="sleep", description="7h",
            numeric_value=7.0, numeric_range=(6.5, 7.5),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))
        wm.context = {"health": {"note": "flu season"}}
        wm.last_updated = "2026-01-01T00:00:00"

        data = wm.to_dict()
        restored = WorldModel.from_dict(data)

        assert len(restored.get_all_expectations()) == 1
        assert restored.get_expectation("health", "sleep").numeric_value == 7.0
        assert restored.context["health"]["note"] == "flu season"


# ─── Observation Tests ───


class TestObservation:
    """Tests for the Observation dataclass."""

    def test_create_observation(self):
        from alter.consciousness.state import Observation
        obs = Observation(
            tick_type="hourly_pulse",
            domain="health",
            aspect="sleep",
            expected="7-8 hours",
            observed="5 hours",
            prediction_error=0.65,
            severity="elevated",
            summary="sleep notably below expected",
        )
        assert obs.domain == "health"
        assert obs.prediction_error == 0.65
        assert obs.id  # auto-generated

    def test_serialization_roundtrip(self):
        from alter.consciousness.state import Observation
        obs = Observation(
            tick_type="hourly_pulse", domain="health", aspect="sleep",
            prediction_error=0.5, severity="elevated",
        )
        data = obs.to_dict()
        restored = Observation.from_dict(data)
        assert restored.id == obs.id
        assert restored.prediction_error == 0.5


# ─── Dormant Question Tests ───


class TestDormantQuestion:
    """Tests for the DormantQuestion dataclass."""

    def test_create_dormant_question(self):
        from alter.consciousness.state import DormantQuestion
        q = DormantQuestion(
            question="What's driving the sleep decline?",
            context="Three nights of poor sleep",
            domain="health",
            resolution_signals=["sleep improvement", "stress reduction"],
        )
        assert not q.resolved
        assert q.readiness == 0.0

    def test_readiness_check(self):
        from alter.consciousness.state import DormantQuestion
        q = DormantQuestion(question="test", readiness=0.5, threshold=0.7)
        assert not q.is_ready()

        q.readiness = 0.8
        assert q.is_ready()

    def test_resolved_question_not_ready(self):
        from alter.consciousness.state import DormantQuestion
        q = DormantQuestion(question="test", readiness=0.9, resolved=True)
        assert not q.is_ready()

    def test_serialization_roundtrip(self):
        from alter.consciousness.state import DormantQuestion
        q = DormantQuestion(
            question="What's going on with work?",
            domain="career",
            resolution_signals=["mood data", "work hours"],
            readiness=0.3,
        )
        data = q.to_dict()
        restored = DormantQuestion.from_dict(data)
        assert restored.question == q.question
        assert restored.readiness == 0.3
        assert len(restored.resolution_signals) == 2


# ─── Consciousness State Tests ───


class TestConsciousnessState:
    """Tests for the ConsciousnessState (shared blackboard)."""

    def _make_state(self):
        from alter.consciousness.state import ConsciousnessState
        return ConsciousnessState(user_id="test_user")

    def test_create_empty_state(self):
        state = self._make_state()
        assert state.user_id == "test_user"
        assert state.narrative == ""
        assert len(state.observations) == 0

    def test_add_observation(self):
        from alter.consciousness.state import Observation
        state = self._make_state()
        obs = Observation(domain="health", aspect="sleep", prediction_error=0.5)
        state.add_observation(obs)
        assert len(state.observations) == 1

    def test_observations_time_range_query(self):
        from alter.consciousness.state import Observation
        state = self._make_state()

        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        recent_time = datetime.now().isoformat()

        state.add_observation(Observation(
            domain="health", aspect="sleep",
            prediction_error=0.3, timestamp=old_time,
        ))
        state.add_observation(Observation(
            domain="health", aspect="sleep",
            prediction_error=0.7, timestamp=recent_time,
        ))

        # Query for last 24 hours
        since = datetime.now() - timedelta(hours=24)
        results = state.get_observations_since(since)
        assert len(results) == 1
        assert results[0].prediction_error == 0.7

    def test_observations_domain_filter(self):
        from alter.consciousness.state import Observation
        state = self._make_state()

        now = datetime.now().isoformat()
        state.add_observation(Observation(domain="health", aspect="sleep", timestamp=now))
        state.add_observation(Observation(domain="career", aspect="hours", timestamp=now))

        since = datetime.now() - timedelta(hours=1)
        health_obs = state.get_observations_since(since, domain="health")
        assert len(health_obs) == 1
        assert health_obs[0].domain == "health"

    def test_elevated_observations_query(self):
        from alter.consciousness.state import Observation
        state = self._make_state()

        now = datetime.now().isoformat()
        state.add_observation(Observation(domain="health", severity="normal", timestamp=now))
        state.add_observation(Observation(domain="health", severity="elevated", timestamp=now))
        state.add_observation(Observation(domain="health", severity="critical", timestamp=now))

        since = datetime.now() - timedelta(hours=1)
        elevated = state.get_elevated_observations_since(since)
        assert len(elevated) == 2

    def test_dormant_question_lifecycle(self):
        from alter.consciousness.state import DormantQuestion
        state = self._make_state()

        q = DormantQuestion(
            question="Why is sleep declining?",
            domain="health",
            readiness=0.3,
        )
        state.add_dormant_question(q)
        assert len(state.get_unresolved_questions()) == 1
        assert len(state.get_ready_questions()) == 0

        # Increase readiness
        q.readiness = 0.8
        assert len(state.get_ready_questions()) == 1

        # Resolve
        state.resolve_question(q.id, "Stress from work deadline")
        assert len(state.get_unresolved_questions()) == 0
        assert q.resolved
        assert q.resolution == "Stress from work deadline"

    def test_dormant_question_pruning(self):
        from alter.consciousness.state import DormantQuestion
        from alter.consciousness.config import MAX_DORMANT_QUESTIONS
        state = self._make_state()

        # Add more than max
        for i in range(MAX_DORMANT_QUESTIONS + 5):
            state.add_dormant_question(DormantQuestion(
                question=f"Question {i}",
                readiness=i * 0.01,  # Increasing readiness
            ))

        # Should be capped at max
        assert len(state.dormant_questions) <= MAX_DORMANT_QUESTIONS

    def test_notifications(self):
        state = self._make_state()
        state.add_notification("You've been sleeping poorly this week")
        assert len(state.get_pending_notifications()) == 1

        notif_id = state.pending_notifications[0]["id"]
        state.mark_notification_delivered(notif_id)
        assert len(state.get_pending_notifications()) == 0

    def test_narrative_update(self):
        state = self._make_state()
        state.update_narrative("User is going through a career transition")
        assert state.narrative == "User is going through a career transition"

    def test_token_tracking(self):
        state = self._make_state()
        today = datetime.now().date().isoformat()
        state.record_token_usage("daily_review", 5000)
        state.record_token_usage("urgent", 3000)
        assert state.get_daily_token_usage(today) == 8000

    def test_serialization_roundtrip(self):
        from alter.consciousness.state import Observation, DormantQuestion, Expectation
        state = self._make_state()

        # Populate state
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep", description="7h",
            numeric_value=7.0, data_field="sleep_hours", confidence=0.7,
        ))
        state.add_observation(Observation(
            domain="health", aspect="sleep", prediction_error=0.5,
        ))
        state.add_dormant_question(DormantQuestion(
            question="Why sleep declining?", domain="health",
        ))
        state.update_narrative("Testing narrative")
        state.add_notification("Test notification")
        state.record_token_usage("daily_review", 5000)

        # Serialize and restore
        data = state.to_dict()
        restored = state.from_dict(data)

        assert restored.user_id == "test_user"
        assert len(restored.observations) == 1
        assert len(restored.dormant_questions) == 1
        assert restored.narrative == "Testing narrative"
        assert restored.world_model.get_expectation("health", "sleep").numeric_value == 7.0
        assert len(restored.pending_notifications) == 1

    def test_save_and_load(self, tmp_path):
        from alter.consciousness.state import Expectation, Observation
        state = self._make_state()
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep", description="7h",
            numeric_value=7.0, data_field="sleep_hours",
        ))
        state.add_observation(Observation(domain="health", aspect="sleep"))
        state.update_narrative("Test narrative")

        path = tmp_path / "consciousness_state.json"
        state.save(path)

        from alter.consciousness.state import ConsciousnessState
        loaded = ConsciousnessState.load("test_user", path)
        assert loaded.user_id == "test_user"
        assert loaded.narrative == "Test narrative"
        assert len(loaded.observations) == 1

    def test_load_nonexistent_creates_empty(self, tmp_path):
        from alter.consciousness.state import ConsciousnessState
        path = tmp_path / "nonexistent.json"
        state = ConsciousnessState.load("test_user", path)
        assert state.user_id == "test_user"
        assert len(state.observations) == 0


# ─── Summary / Memory Tests ───


class TestSummary:
    """Tests for the Summary dataclass."""

    def test_create_summary(self):
        from alter.consciousness.state import Summary
        s = Summary(
            period_type="daily",
            period_label="2026-02-16",
            content="Sleep was poor, mood declined. Work deadline stress.",
            key_insights=["Sleep-mood correlation detected"],
            key_facts={"avg_sleep": 5.5, "avg_mood": 4.0},
            domains_covered=["health", "emotions"],
            observation_count=12,
        )
        assert s.period_type == "daily"
        assert len(s.key_insights) == 1

    def test_serialization_roundtrip(self):
        from alter.consciousness.state import Summary
        s = Summary(
            period_type="weekly",
            period_label="2026-W07",
            content="Burnout risk emerging",
            key_insights=["Sleep declining", "Exercise dropped"],
            key_facts={"total_observations": 84},
            domains_covered=["health", "career"],
            observation_count=84,
        )
        data = s.to_dict()
        restored = Summary.from_dict(data)
        assert restored.period_label == "2026-W07"
        assert restored.content == "Burnout risk emerging"
        assert len(restored.key_insights) == 2


class TestSummaryStorage:
    """Tests for summary storage and retrieval in ConsciousnessState."""

    def _make_state(self):
        from alter.consciousness.state import ConsciousnessState
        return ConsciousnessState(user_id="test_user")

    def test_add_summary(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        state.add_summary(Summary(
            period_type="daily", period_label="2026-02-16",
            content="Day summary",
        ))
        assert len(state.summaries.get("daily", [])) == 1

    def test_replace_existing_summary(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        state.add_summary(Summary(
            period_type="daily", period_label="2026-02-16",
            content="First version",
        ))
        state.add_summary(Summary(
            period_type="daily", period_label="2026-02-16",
            content="Corrected version",
        ))
        summaries = state.get_summaries("daily")
        assert len(summaries) == 1
        assert summaries[0].content == "Corrected version"

    def test_get_summaries_newest_first(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        for day in range(10, 17):
            state.add_summary(Summary(
                period_type="daily", period_label=f"2026-02-{day}",
                content=f"Day {day}",
            ))
        summaries = state.get_summaries("daily", limit=3)
        assert len(summaries) == 3
        assert summaries[0].period_label == "2026-02-16"
        assert summaries[2].period_label == "2026-02-14"

    def test_get_summaries_since_label(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        for day in range(10, 17):
            state.add_summary(Summary(
                period_type="daily", period_label=f"2026-02-{day}",
                content=f"Day {day}",
            ))
        summaries = state.get_summaries("daily", since_label="2026-02-14")
        assert len(summaries) == 3  # 14, 15, 16

    def test_get_summary_for_period(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        state.add_summary(Summary(
            period_type="weekly", period_label="2026-W07",
            content="Week 7 summary",
        ))
        s = state.get_summary_for_period("weekly", "2026-W07")
        assert s is not None
        assert s.content == "Week 7 summary"

        missing = state.get_summary_for_period("weekly", "2026-W99")
        assert missing is None

    def test_summaries_in_serialization(self):
        from alter.consciousness.state import Summary, ConsciousnessState
        state = self._make_state()
        state.add_summary(Summary(
            period_type="daily", period_label="2026-02-16",
            content="Test summary",
            key_insights=["insight1"],
        ))
        data = state.to_dict()
        restored = ConsciousnessState.from_dict(data)
        assert len(restored.summaries.get("daily", [])) == 1
        assert restored.summaries["daily"][0].content == "Test summary"


class TestContextForTick:
    """Tests for get_context_for_tick — hierarchical memory reads."""

    def _make_state(self):
        from alter.consciousness.state import ConsciousnessState
        return ConsciousnessState(user_id="test_user")

    def test_daily_tick_gets_raw_observations(self):
        from alter.consciousness.state import Observation
        state = self._make_state()
        now = datetime.now().isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep",
            prediction_error=0.6, severity="elevated", timestamp=now,
        ))
        context = state.get_context_for_tick("daily_review")
        assert "observations" in context
        assert len(context["observations"]) == 1
        assert "elevated_errors" in context
        assert len(context["elevated_errors"]) == 1

    def test_weekly_tick_gets_daily_summaries(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        for day in range(10, 17):
            state.add_summary(Summary(
                period_type="daily", period_label=f"2026-02-{day}",
                content=f"Day {day} summary",
            ))
        context = state.get_context_for_tick("weekly_reflect")
        assert "daily_summaries" in context
        assert len(context["daily_summaries"]) == 7
        # Should NOT have raw observations key
        assert "observations" not in context

    def test_monthly_tick_gets_weekly_summaries(self):
        from alter.consciousness.state import Summary
        state = self._make_state()
        for week in range(5, 9):
            state.add_summary(Summary(
                period_type="weekly", period_label=f"2026-W0{week}",
                content=f"Week {week} summary",
            ))
        context = state.get_context_for_tick("monthly_deep")
        assert "weekly_summaries" in context
        assert len(context["weekly_summaries"]) == 4
        # Also gets recent daily summaries for detail
        assert "daily_summaries" in context

    def test_urgent_tick_gets_focused_context(self):
        from alter.consciousness.state import Observation
        state = self._make_state()
        now = datetime.now().isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep",
            severity="critical", timestamp=now,
        ))
        state.update_narrative("User under work stress")
        context = state.get_context_for_tick("urgent")
        assert "observations" in context
        assert context["narrative"] == "User under work stress"
        # Should NOT have summaries (urgent is focused)
        assert "daily_summaries" not in context


class TestCompaction:
    """Tests for the compact() method — pruning old data."""

    def _make_state(self):
        from alter.consciousness.state import ConsciousnessState
        return ConsciousnessState(user_id="test_user")

    def test_compact_old_observations(self):
        from alter.consciousness.state import Observation
        state = self._make_state()

        # Add old observation (3 days ago)
        old_time = (datetime.now() - timedelta(hours=72)).isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep", timestamp=old_time,
        ))
        # Add recent observation (1 hour ago)
        recent_time = (datetime.now() - timedelta(hours=1)).isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep", timestamp=recent_time,
        ))

        pruned = state.compact()
        assert pruned["observations"] == 1  # Old one removed
        assert len(state.observations) == 1  # Recent one kept

    def test_compact_delivered_notifications(self):
        state = self._make_state()
        # Add old delivered notification
        state.pending_notifications.append({
            "id": "old",
            "message": "test",
            "delivered": True,
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
        })
        # Add recent undelivered notification
        state.add_notification("Recent message")

        pruned = state.compact()
        assert pruned["notifications"] == 1
        assert len(state.pending_notifications) == 1

    def test_compact_resolved_questions(self):
        from alter.consciousness.state import DormantQuestion
        state = self._make_state()

        # Old resolved question
        q = DormantQuestion(question="Old question", resolved=True,
                           resolved_at=(datetime.now() - timedelta(days=60)).isoformat())
        state.dormant_questions.append(q)

        # Recent unresolved question
        state.add_dormant_question(DormantQuestion(question="Active question"))

        pruned = state.compact()
        assert pruned["dormant_questions"] == 1
        assert len(state.dormant_questions) == 1
        assert state.dormant_questions[0].question == "Active question"

    def test_compact_returns_counts(self):
        state = self._make_state()
        pruned = state.compact()
        assert "observations" in pruned
        assert "notifications" in pruned
        assert "dormant_questions" in pruned


# ─── Observe Tests ───


class TestComputePredictionError:
    """Tests for the prediction error math."""

    def test_exact_match(self):
        from alter.consciousness.observe import compute_prediction_error
        error = compute_prediction_error(expected=7.0, actual=7.0, confidence=1.0)
        assert error == 0.0

    def test_within_range_no_error(self):
        from alter.consciousness.observe import compute_prediction_error
        error = compute_prediction_error(
            expected=7.5, actual=7.2, confidence=1.0,
            numeric_range=(7.0, 8.0),
        )
        assert error == 0.0

    def test_outside_range_has_error(self):
        from alter.consciousness.observe import compute_prediction_error
        error = compute_prediction_error(
            expected=7.5, actual=5.0, confidence=1.0,
            numeric_range=(7.0, 8.0),
        )
        assert error > 0.0

    def test_confidence_scales_error(self):
        from alter.consciousness.observe import compute_prediction_error
        high_conf = compute_prediction_error(expected=7.0, actual=5.0, confidence=1.0)
        low_conf = compute_prediction_error(expected=7.0, actual=5.0, confidence=0.3)
        assert low_conf < high_conf
        assert low_conf == pytest.approx(high_conf * 0.3, abs=0.01)

    def test_zero_expected(self):
        from alter.consciousness.observe import compute_prediction_error
        error = compute_prediction_error(expected=0.0, actual=5.0, confidence=1.0)
        assert error > 0.0

    def test_clamped_to_one(self):
        from alter.consciousness.observe import compute_prediction_error
        error = compute_prediction_error(expected=1.0, actual=100.0, confidence=1.0)
        assert error <= 1.0

    def test_clamped_to_zero(self):
        from alter.consciousness.observe import compute_prediction_error
        error = compute_prediction_error(expected=7.0, actual=7.0, confidence=0.0)
        assert error == 0.0


class TestObserveDailyData:
    """Tests for observing daily data against world model."""

    def _make_world_model(self):
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        wm.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5,
            numeric_range=(7.0, 8.0),
            data_field="sleep_hours",
            confidence=0.8,
            data_points=14,
        ))
        wm.set_expectation(Expectation(
            domain="emotions", aspect="mood",
            description="Generally positive mood",
            numeric_value=7.0,
            numeric_range=(6.0, 8.0),
            data_field="mood",
            confidence=0.7,
            data_points=10,
        ))
        return wm

    def test_no_data_no_observations(self):
        from alter.consciousness.observe import observe_daily_data
        wm = self._make_world_model()
        observations = observe_daily_data(wm, {})
        assert len(observations) == 0

    def test_within_range_produces_zero_error(self):
        from alter.consciousness.observe import observe_daily_data
        wm = self._make_world_model()
        observations = observe_daily_data(wm, {
            "health": {"sleep_hours": 7.5},
        })
        assert len(observations) == 1
        assert observations[0].prediction_error == 0.0
        assert observations[0].severity == "normal"

    def test_below_range_produces_error(self):
        from alter.consciousness.observe import observe_daily_data
        wm = self._make_world_model()
        observations = observe_daily_data(wm, {
            "health": {"sleep_hours": 4.0},
        })
        assert len(observations) == 1
        assert observations[0].prediction_error > 0.0
        assert observations[0].domain == "health"
        assert observations[0].aspect == "sleep"

    def test_critical_error_detected(self):
        from alter.consciousness.observe import observe_daily_data
        wm = self._make_world_model()
        # Sleep 0 hours — extreme deviation
        observations = observe_daily_data(wm, {
            "health": {"sleep_hours": 0.0},
        })
        assert len(observations) == 1
        assert observations[0].severity == "critical"

    def test_multiple_domains(self):
        from alter.consciousness.observe import observe_daily_data
        wm = self._make_world_model()
        observations = observe_daily_data(wm, {
            "health": {"sleep_hours": 5.0},
            "emotions": {"mood": 3.0},
        })
        assert len(observations) == 2
        domains = {o.domain for o in observations}
        assert "health" in domains
        assert "emotions" in domains

    def test_low_confidence_skipped(self):
        from alter.consciousness.observe import observe_daily_data
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        wm.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="test", numeric_value=7.0,
            data_field="sleep_hours",
            confidence=0.1,  # Below MIN_CONFIDENCE_FOR_ATTENTION (0.2)
        ))
        observations = observe_daily_data(wm, {"health": {"sleep_hours": 3.0}})
        assert len(observations) == 0

    def test_observation_has_raw_data(self):
        from alter.consciousness.observe import observe_daily_data
        wm = self._make_world_model()
        observations = observe_daily_data(wm, {
            "health": {"sleep_hours": 5.0},
        })
        assert "expected_value" in observations[0].raw_data
        assert "actual_value" in observations[0].raw_data
        assert observations[0].raw_data["actual_value"] == 5.0


class TestUpdateExpectation:
    """Tests for expectation learning from new data."""

    def test_exponential_moving_average(self):
        from alter.consciousness.state import Expectation
        from alter.consciousness.observe import update_expectation_from_data

        exp = Expectation(
            domain="health", aspect="sleep", description="test",
            numeric_value=7.0, data_points=10, confidence=0.5,
        )
        update_expectation_from_data(exp, actual_value=8.0, learning_rate=0.1)

        # Should move slightly toward 8.0
        assert exp.numeric_value > 7.0
        assert exp.numeric_value < 8.0
        assert exp.numeric_value == pytest.approx(7.1, abs=0.01)
        assert exp.data_points == 11

    def test_range_adjustment(self):
        from alter.consciousness.state import Expectation
        from alter.consciousness.observe import update_expectation_from_data

        exp = Expectation(
            domain="health", aspect="sleep", description="test",
            numeric_value=7.0, numeric_range=(6.5, 7.5),
            data_points=10,
        )
        update_expectation_from_data(exp, actual_value=9.0, learning_rate=0.1)

        # Range should expand toward the high end
        assert exp.numeric_range[1] > 7.5

    def test_first_value_sets_directly(self):
        from alter.consciousness.state import Expectation
        from alter.consciousness.observe import update_expectation_from_data

        exp = Expectation(
            domain="health", aspect="sleep", description="test",
        )
        update_expectation_from_data(exp, actual_value=7.0)
        assert exp.numeric_value == 7.0
        assert exp.data_points == 1

    def test_confidence_increases_with_data(self):
        from alter.consciousness.state import Expectation
        from alter.consciousness.observe import update_expectation_from_data

        exp = Expectation(
            domain="health", aspect="sleep", description="test",
            numeric_value=7.0, data_points=6, confidence=0.2,
        )
        update_expectation_from_data(exp, actual_value=7.5)
        # 7 data points → confidence should be at least 0.5
        assert exp.confidence >= 0.5


# ─── Context Assembly Tests (Phase C2) ───


class TestTokenEstimation:
    """Tests for the fast token estimation."""

    def test_estimate_tokens(self):
        from alter.consciousness.context import estimate_tokens
        # ~4 chars per token
        assert estimate_tokens("a" * 100) == 25
        assert estimate_tokens("a" * 4) == 1
        assert estimate_tokens("") == 1  # minimum 1

    def test_estimate_tokens_realistic_text(self):
        from alter.consciousness.context import estimate_tokens
        text = "The user has been sleeping poorly for three nights in a row."
        tokens = estimate_tokens(text)
        assert 10 < tokens < 20  # Rough estimate


class TestSectionFormatters:
    """Tests for individual section formatting functions."""

    def test_format_narrative_empty(self):
        from alter.consciousness.context import format_narrative
        result = format_narrative("")
        assert "No narrative established" in result

    def test_format_narrative_present(self):
        from alter.consciousness.context import format_narrative
        result = format_narrative("User is thriving")
        assert result == "User is thriving"

    def test_format_world_model_empty(self):
        from alter.consciousness.context import format_world_model
        from alter.consciousness.state import WorldModel
        wm = WorldModel()
        result = format_world_model(wm)
        assert "No expectations" in result

    def test_format_world_model_with_expectations(self):
        from alter.consciousness.context import format_world_model
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        wm.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            confidence=0.8,
        ))
        result = format_world_model(wm)
        assert "Health" in result
        assert "Sleeps 7-8 hours" in result
        assert "80%" in result

    def test_format_world_model_domain_filter(self):
        from alter.consciousness.context import format_world_model
        from alter.consciousness.state import WorldModel, Expectation
        wm = WorldModel()
        wm.set_expectation(Expectation(domain="health", aspect="sleep", description="test sleep"))
        wm.set_expectation(Expectation(domain="career", aspect="hours", description="test career"))
        result = format_world_model(wm, domains=["health"])
        assert "sleep" in result.lower()
        assert "career" not in result.lower()

    def test_format_observations_empty(self):
        from alter.consciousness.context import format_observations
        result = format_observations([])
        assert "No observations" in result

    def test_format_observations_with_severity_markers(self):
        from alter.consciousness.context import format_observations
        from alter.consciousness.state import Observation
        obs = [
            Observation(domain="health", aspect="sleep",
                       summary="sleep low", severity="elevated",
                       timestamp="2026-02-16T10:00:00"),
            Observation(domain="health", aspect="heart",
                       summary="heart rate high", severity="critical",
                       timestamp="2026-02-16T11:00:00"),
        ]
        result = format_observations(obs)
        assert "[ELEVATED]" in result
        assert "[CRITICAL]" in result

    def test_format_dormant_questions_empty(self):
        from alter.consciousness.context import format_dormant_questions
        result = format_dormant_questions([])
        assert "No unresolved" in result

    def test_format_dormant_questions_with_signals(self):
        from alter.consciousness.context import format_dormant_questions
        from alter.consciousness.state import DormantQuestion
        questions = [
            DormantQuestion(
                question="Why is sleep declining?",
                domain="health", readiness=0.5,
                resolution_signals=["sleep data", "stress levels"],
            )
        ]
        result = format_dormant_questions(questions)
        assert "Why is sleep declining?" in result
        assert "50%" in result
        assert "sleep data" in result

    def test_format_goals_active_only(self):
        from alter.consciousness.context import format_goals
        goals = [
            {"description": "Run marathon", "domain": "health",
             "time_horizon": "1_year", "status": "active"},
            {"description": "Get promoted", "domain": "career",
             "time_horizon": "1_year", "status": "completed"},
        ]
        result = format_goals(goals, active_only=True)
        assert "Run marathon" in result
        assert "Get promoted" not in result

    def test_format_goals_all(self):
        from alter.consciousness.context import format_goals
        goals = [
            {"description": "Run marathon", "domain": "health",
             "time_horizon": "1_year", "status": "active"},
            {"description": "Get promoted", "domain": "career",
             "time_horizon": "1_year", "status": "completed"},
        ]
        result = format_goals(goals, active_only=False)
        assert "Run marathon" in result
        assert "Get promoted" in result

    def test_format_summaries(self):
        from alter.consciousness.context import format_summaries
        from alter.consciousness.state import Summary
        summaries = [
            Summary(
                period_type="daily", period_label="2026-02-16",
                content="Rough day. Sleep was poor, mood dropped.",
                key_insights=["Sleep-mood correlation"],
                prediction_errors_summary="1 elevated in health",
            ),
        ]
        result = format_summaries(summaries)
        assert "2026-02-16" in result
        assert "Rough day" in result
        assert "Sleep-mood correlation" in result

    def test_format_principles_summary(self):
        from alter.consciousness.context import format_principles
        principles = [
            {"id": "autonomy", "name": "User Autonomy",
             "description": "Respect user choices", "rules": ["Always ask first"], "weight": 10},
        ]
        result = format_principles(principles, summary_only=True)
        assert "User Autonomy" in result
        assert "Always ask first" not in result  # summary_only skips rules

    def test_format_principles_full(self):
        from alter.consciousness.context import format_principles
        principles = [
            {"id": "autonomy", "name": "User Autonomy",
             "description": "Respect user choices", "rules": ["Always ask first"], "weight": 10},
        ]
        result = format_principles(principles, summary_only=False)
        assert "User Autonomy" in result
        assert "Always ask first" in result
        assert "weight: 10" in result


class TestContextAssembler:
    """Tests for the ContextAssembler."""

    def _make_populated_state(self):
        """Create a state with realistic test data."""
        from alter.consciousness.state import (
            ConsciousnessState, Observation, DormantQuestion,
            Expectation, Summary,
        )
        state = ConsciousnessState(user_id="test_user")

        # World model
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8,
        ))
        state.world_model.set_expectation(Expectation(
            domain="emotions", aspect="mood",
            description="Generally positive",
            numeric_value=7.0, data_field="mood", confidence=0.6,
        ))

        # Observations (recent)
        now = datetime.now().isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep",
            summary="Sleep 5h, below expected",
            prediction_error=0.65, severity="elevated",
            timestamp=now,
        ))

        # Narrative
        state.update_narrative("User is pushing hard at work this week.")

        # Dormant questions
        state.add_dormant_question(DormantQuestion(
            question="Is the sleep decline stress-related?",
            domain="health", readiness=0.4,
            resolution_signals=["stress data", "sleep recovery"],
        ))

        # Daily summaries
        for day in range(10, 17):
            state.add_summary(Summary(
                period_type="daily", period_label=f"2026-02-{day}",
                content=f"Day {day}: mostly normal, some sleep issues.",
                key_insights=[f"Insight from day {day}"],
            ))

        # Weekly summaries
        for week in [5, 6, 7]:
            state.add_summary(Summary(
                period_type="weekly", period_label=f"2026-W0{week}",
                content=f"Week {week}: overall stable, health trending down.",
            ))

        return state

    def _make_user_model(self):
        """Create a minimal user model for testing."""
        from alter.core.user_model import UserModel, Goal
        user = UserModel(user_id="test_user")
        user.set_purpose("Live a balanced, healthy, and meaningful life")
        user.add_goal(Goal(
            id="g1", domain="health",
            description="Sleep 7+ hours consistently",
            time_horizon="quarter",
        ))
        user.add_goal(Goal(
            id="g2", domain="career",
            description="Get promoted to senior engineer",
            time_horizon="1_year",
        ))
        user.set_personality_traits({"openness": 8, "conscientiousness": 7})
        user.set_preference("communication_style", "direct")
        return user

    def test_daily_context_has_required_sections(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        user = self._make_user_model()

        assembler = ContextAssembler(state, user_model=user)
        ctx = assembler.assemble("daily_review")

        assert "narrative" in ctx.section_names
        assert "world_model" in ctx.section_names
        assert "goals" in ctx.section_names
        assert ctx.token_estimate > 0
        assert ctx.token_estimate <= ctx.token_budget

    def test_daily_context_includes_observations(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        assembler = ContextAssembler(state)
        ctx = assembler.assemble("daily_review")

        assert "observations" in ctx.section_names or "elevated_errors" in ctx.section_names

    def test_weekly_context_has_daily_summaries(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        assembler = ContextAssembler(state)
        ctx = assembler.assemble("weekly_reflect")

        assert "daily_summaries" in ctx.section_names
        assert "constitution" in ctx.section_names

    def test_monthly_context_has_weekly_summaries(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        user = self._make_user_model()
        assembler = ContextAssembler(state, user_model=user)
        ctx = assembler.assemble("monthly_deep")

        assert "weekly_summaries" in ctx.section_names
        assert "purpose" in ctx.section_names
        assert "personality" in ctx.section_names

    def test_urgent_context_is_focused(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        assembler = ContextAssembler(state)
        ctx = assembler.assemble("urgent", trigger_domain="health")

        assert "narrative" in ctx.section_names
        assert "world_model" in ctx.section_names
        assert "observations" in ctx.section_names
        # Urgent should NOT have summaries, goals, etc.
        assert "daily_summaries" not in ctx.section_names
        assert "goals" not in ctx.section_names

    def test_budget_enforcement_drops_low_priority(self):
        from alter.consciousness.context import ContextAssembler
        from alter.consciousness.config import TOKEN_BUDGETS
        state = self._make_populated_state()
        user = self._make_user_model()
        assembler = ContextAssembler(state, user_model=user)
        ctx = assembler.assemble("daily_review")

        # Token estimate should not exceed budget
        assert ctx.token_estimate <= TOKEN_BUDGETS["daily_review"]

    def test_full_text_combines_sections(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        assembler = ContextAssembler(state)
        ctx = assembler.assemble("daily_review")

        text = ctx.full_text
        assert "## Current Narrative" in text
        assert "## Current Understanding" in text

    def test_to_dict_for_logging(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        assembler = ContextAssembler(state)
        ctx = assembler.assemble("daily_review")

        d = ctx.to_dict()
        assert "tick_type" in d
        assert "sections" in d
        assert "token_budget" in d
        assert d["tick_type"] == "daily_review"

    def test_empty_state_still_assembles(self):
        from alter.consciousness.state import ConsciousnessState
        from alter.consciousness.context import ContextAssembler
        state = ConsciousnessState(user_id="empty")
        assembler = ContextAssembler(state)
        ctx = assembler.assemble("daily_review")

        # Should still produce sections (with "no data" messages)
        assert len(ctx.sections) > 0
        assert "narrative" in ctx.section_names

    def test_no_user_model_still_assembles(self):
        from alter.consciousness.context import ContextAssembler
        state = self._make_populated_state()
        assembler = ContextAssembler(state)  # No user_model
        ctx = assembler.assemble("daily_review")

        assert "narrative" in ctx.section_names
        # Goals should show "no goals set" since no user_model
        goals_section = ctx.get_section("goals")
        assert goals_section is not None


# ─── Prompt Tests (Phase C2) ───


class TestPromptBuilder:
    """Tests for prompt building."""

    def _make_context(self, tick_type="daily_review"):
        from alter.consciousness.state import ConsciousnessState, Observation, Expectation
        from alter.consciousness.context import ContextAssembler

        state = ConsciousnessState(user_id="test_user")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours", confidence=0.8,
        ))
        state.update_narrative("User is working hard this week.")
        now = datetime.now().isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep",
            summary="Sleep 5h", severity="elevated", timestamp=now,
        ))

        assembler = ContextAssembler(state)
        return assembler.assemble(tick_type)

    def test_daily_prompt_has_all_sections(self):
        from alter.consciousness.prompts import build_prompt
        ctx = self._make_context("daily_review")
        prompt = build_prompt("daily_review", ctx, user_name="Alex")

        assert "ALTER" in prompt
        assert "Alex" in prompt
        assert "daily review" in prompt
        assert "OBSERVE" in prompt
        assert "ASSESS" in prompt
        assert "THINK" in prompt
        assert "DECIDE" in prompt
        assert "NARRATE" in prompt
        assert "SUMMARIZE" in prompt
        assert "json" in prompt.lower()

    def test_weekly_prompt_has_synthesis_steps(self):
        from alter.consciousness.prompts import build_prompt
        ctx = self._make_context("weekly_reflect")
        prompt = build_prompt("weekly_reflect", ctx)

        assert "weekly reflection" in prompt
        assert "SYNTHESIZE" in prompt
        assert "cross-domain" in prompt.lower() or "Cross-domain" in prompt

    def test_monthly_prompt_has_identity_steps(self):
        from alter.consciousness.prompts import build_prompt
        ctx = self._make_context("monthly_deep")
        prompt = build_prompt("monthly_deep", ctx)

        assert "monthly deep review" in prompt
        assert "REFLECT" in prompt
        assert "purpose" in prompt.lower()

    def test_urgent_prompt_is_focused(self):
        from alter.consciousness.prompts import build_prompt
        ctx = self._make_context("urgent")
        prompt = build_prompt("urgent", ctx)

        assert "urgent" in prompt.lower() or "immediate attention" in prompt
        assert "brief" in prompt.lower() or "focused" in prompt.lower()

    def test_prompt_includes_output_schema(self):
        from alter.consciousness.prompts import build_prompt
        ctx = self._make_context("daily_review")
        prompt = build_prompt("daily_review", ctx)

        assert "observations" in prompt
        assert "insights" in prompt
        assert "decisions" in prompt
        assert "narrative" in prompt
        assert "notifications" in prompt
        assert "summary" in prompt

    def test_available_tick_types(self):
        from alter.consciousness.prompts import get_available_tick_types
        types = get_available_tick_types()
        assert "daily_review" in types
        assert "weekly_reflect" in types
        assert "monthly_deep" in types
        assert "urgent" in types


# ─── Parse Tests (Phase C2) ───


class TestTickResultModel:
    """Tests for the TickResult Pydantic model."""

    def test_empty_tick_result(self):
        from alter.consciousness.parse import TickResult
        result = TickResult()
        assert len(result.observations) == 0
        assert len(result.decisions) == 0
        assert result.narrative == ""
        assert result.summary is None

    def test_full_tick_result(self):
        from alter.consciousness.parse import (
            TickResult, TickObservation, TickInsight, TickDecision,
            WorldModelUpdate, TickNotification, TickSummary,
            DormantQuestionChanges, NewDormantQuestion, ResolvedQuestion,
        )
        result = TickResult(
            observations=[TickObservation(
                domain="health", aspect="sleep",
                observation="Sleep was 5h", significance="signal",
            )],
            insights=[TickInsight(
                description="Sleep-stress pattern emerging",
                domains=["health", "career"], confidence=0.7,
            )],
            decisions=[TickDecision(
                action="notify_user",
                target="sleep pattern",
                detail="Alert about declining sleep",
            )],
            world_model_updates=[WorldModelUpdate(
                domain="health", aspect="sleep",
                new_description="Sleep trending toward 5-6h",
                new_numeric_value=5.5,
                reasoning="Three nights of poor sleep",
            )],
            narrative="User is pushing through a deadline, sleep is suffering.",
            notifications=[TickNotification(
                message="I've noticed your sleep has been off this week.",
                urgency="medium",
            )],
            dormant_questions=DormantQuestionChanges(
                new=[NewDormantQuestion(
                    question="Is this temporary or a pattern shift?",
                    domain="health",
                    resolution_signals=["sleep recovery after deadline"],
                )],
                resolved=[ResolvedQuestion(
                    question_id="q1",
                    resolution="Confirmed: work stress causing sleep issues",
                )],
            ),
            summary=TickSummary(
                content="Poor sleep, work stress dominant.",
                key_insights=["Sleep-stress correlation"],
                key_facts={"avg_sleep": 5.2},
                prediction_errors_summary="1 elevated in health",
            ),
        )
        assert len(result.observations) == 1
        assert result.observations[0].significance == "signal"
        assert len(result.dormant_questions.new) == 1
        assert result.summary.key_facts["avg_sleep"] == 5.2


class TestParseTickResult:
    """Tests for parsing LLM output into TickResult."""

    def _sample_result_json(self):
        return json.dumps({
            "observations": [
                {"domain": "health", "aspect": "sleep",
                 "observation": "Sleep was 5h", "significance": "signal"}
            ],
            "insights": [],
            "decisions": [
                {"action": "notify_user", "target": "sleep",
                 "detail": "Alert user about sleep"}
            ],
            "narrative": "User is tired.",
            "notifications": [
                {"message": "Your sleep has been off.", "urgency": "medium"}
            ],
            "summary": {
                "content": "Rough day, sleep issues.",
                "key_insights": ["Sleep declining"],
                "key_facts": {"sleep_hours": 5.0},
            },
        })

    def test_parse_clean_json(self):
        from alter.consciousness.parse import parse_tick_result
        raw = self._sample_result_json()
        result = parse_tick_result(raw)
        assert len(result.observations) == 1
        assert result.narrative == "User is tired."
        assert result.summary is not None

    def test_parse_json_in_markdown_block(self):
        from alter.consciousness.parse import parse_tick_result
        raw = f"Here's my analysis:\n\n```json\n{self._sample_result_json()}\n```\n\nDone."
        result = parse_tick_result(raw)
        assert len(result.observations) == 1
        assert result.narrative == "User is tired."

    def test_parse_json_in_plain_markdown_block(self):
        from alter.consciousness.parse import parse_tick_result
        raw = f"Analysis:\n\n```\n{self._sample_result_json()}\n```"
        result = parse_tick_result(raw)
        assert len(result.observations) == 1

    def test_parse_json_with_surrounding_text(self):
        from alter.consciousness.parse import parse_tick_result
        raw = f"Let me think about this...\n\n{self._sample_result_json()}\n\nThat's my analysis."
        result = parse_tick_result(raw)
        assert len(result.observations) == 1

    def test_parse_minimal_json(self):
        from alter.consciousness.parse import parse_tick_result
        raw = '{"narrative": "All is well.", "observations": []}'
        result = parse_tick_result(raw)
        assert result.narrative == "All is well."
        assert len(result.observations) == 0

    def test_parse_empty_json_object(self):
        from alter.consciousness.parse import parse_tick_result
        raw = '{}'
        result = parse_tick_result(raw)
        assert result.narrative == ""
        assert len(result.observations) == 0

    def test_parse_failure_raises(self):
        from alter.consciousness.parse import parse_tick_result, ParseError
        with pytest.raises(ParseError):
            parse_tick_result("This is not JSON at all, no braces here")

    def test_parse_invalid_json_raises(self):
        from alter.consciousness.parse import parse_tick_result, ParseError
        with pytest.raises(ParseError):
            parse_tick_result("{invalid json content with no valid structure")

    def test_parse_with_extra_fields_is_tolerant(self):
        from alter.consciousness.parse import parse_tick_result
        raw = json.dumps({
            "narrative": "Extra fields should be ignored.",
            "extra_field": "should not crash",
            "another_extra": 42,
        })
        result = parse_tick_result(raw)
        assert result.narrative == "Extra fields should be ignored."

    def test_parse_preserves_dormant_question_changes(self):
        from alter.consciousness.parse import parse_tick_result
        raw = json.dumps({
            "narrative": "test",
            "dormant_questions": {
                "new": [{"question": "Why so tired?", "domain": "health",
                         "resolution_signals": ["sleep data"]}],
                "resolved": [{"question_id": "q42", "resolution": "Answered!"}],
            },
        })
        result = parse_tick_result(raw)
        assert len(result.dormant_questions.new) == 1
        assert result.dormant_questions.new[0].question == "Why so tired?"
        assert len(result.dormant_questions.resolved) == 1
        assert result.dormant_questions.resolved[0].question_id == "q42"


class TestJsonExtraction:
    """Tests for JSON extraction helpers."""

    def test_extract_from_markdown(self):
        from alter.consciousness.parse import _extract_json_from_markdown
        text = "Text\n```json\n{\"key\": \"value\"}\n```\nMore text"
        result = _extract_json_from_markdown(text)
        assert result is not None
        assert '"key"' in result

    def test_extract_from_plain_markdown(self):
        from alter.consciousness.parse import _extract_json_from_markdown
        text = "Text\n```\n{\"key\": \"value\"}\n```\nMore text"
        result = _extract_json_from_markdown(text)
        assert result is not None

    def test_extract_from_markdown_no_json(self):
        from alter.consciousness.parse import _extract_json_from_markdown
        text = "No code blocks here"
        result = _extract_json_from_markdown(text)
        assert result is None

    def test_extract_from_markdown_non_json_block(self):
        from alter.consciousness.parse import _extract_json_from_markdown
        text = "```python\nprint('hello')\n```"
        result = _extract_json_from_markdown(text)
        assert result is None  # content doesn't start with {

    def test_extract_braces(self):
        from alter.consciousness.parse import _extract_json_braces
        text = "prefix {\"key\": \"value\"} suffix"
        result = _extract_json_braces(text)
        assert result == '{"key": "value"}'

    def test_extract_braces_nested(self):
        from alter.consciousness.parse import _extract_json_braces
        text = 'prefix {"a": {"b": 1}} suffix'
        result = _extract_json_braces(text)
        assert result == '{"a": {"b": 1}}'

    def test_extract_braces_no_json(self):
        from alter.consciousness.parse import _extract_json_braces
        text = "no braces here at all"
        result = _extract_json_braces(text)
        assert result is None


# ─── LLM Abstraction Tests (Phase C3) ───


class TestLLMAbstraction:
    """Tests for the thin LLM wrapper."""

    def test_create_mock_think_fn(self):
        from alter.consciousness.llm import create_mock_think_fn
        think = create_mock_think_fn('{"narrative": "test"}')
        result = think("any prompt")
        assert result == '{"narrative": "test"}'

    def test_mock_think_fn_ignores_prompt(self):
        from alter.consciousness.llm import create_mock_think_fn
        think = create_mock_think_fn("fixed response")
        assert think("prompt 1") == "fixed response"
        assert think("completely different prompt") == "fixed response"

    def test_create_recording_think_fn(self):
        from alter.consciousness.llm import create_recording_think_fn
        think, recorded = create_recording_think_fn('{"narrative": "ok"}')
        think("first prompt")
        think("second prompt")
        assert len(recorded) == 2
        assert recorded[0] == "first prompt"
        assert recorded[1] == "second prompt"

    def test_create_think_fn_mock_provider(self):
        from alter.consciousness.llm import create_think_fn
        think = create_think_fn(provider="mock", response='{"narrative": "via factory"}')
        assert think("prompt") == '{"narrative": "via factory"}'

    def test_create_think_fn_unknown_provider(self):
        from alter.consciousness.llm import create_think_fn
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_think_fn(provider="nonexistent")


# ─── Engine Tests (Phase C3) ───


# Canned LLM response for engine tests
CANNED_TICK_RESULT = json.dumps({
    "observations": [
        {"domain": "health", "aspect": "sleep",
         "observation": "Sleep was 5h", "significance": "signal"}
    ],
    "insights": [
        {"description": "Sleep declining due to work stress",
         "domains": ["health", "career"], "confidence": 0.7}
    ],
    "decisions": [
        {"action": "notify_user", "target": "sleep",
         "detail": "Alert about declining sleep"},
        {"action": "store_question", "target": "sleep recovery",
         "detail": "Will sleep recover post-deadline?"},
        {"action": "update_expectation", "target": "health/sleep",
         "detail": "Adjust sleep expectation down temporarily"},
    ],
    "world_model_updates": [
        {"domain": "health", "aspect": "sleep",
         "new_description": "Currently sleeping 5-6h (normally 7-8h)",
         "new_numeric_value": 5.5,
         "reasoning": "Three nights of poor sleep"}
    ],
    "narrative": "User is pushing through a deadline. Sleep and mood declining.",
    "notifications": [
        {"message": "Your sleep has been off this week. Take care of yourself.",
         "urgency": "medium"}
    ],
    "dormant_questions": {
        "new": [
            {"question": "Will sleep recover after the deadline?",
             "domain": "health",
             "resolution_signals": ["sleep returns to 7h+"],
             "context": "Sleep dropped during work crunch"}
        ],
        "resolved": []
    },
    "summary": {
        "content": "Day of poor sleep and high work hours. Burnout risk emerging.",
        "key_insights": ["Sleep-work correlation"],
        "key_facts": {"sleep_hours": 5.0, "work_hours": 11},
        "prediction_errors_summary": "Elevated in health/sleep"
    }
})


class TestEngine:
    """Tests for ConsciousnessEngine — the orchestrator."""

    def _make_engine(self, canned_response=CANNED_TICK_RESULT, auto_save=False):
        """Create an engine with mock think_fn and populated state."""
        from alter.consciousness.state import ConsciousnessState, Expectation, Observation
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.llm import create_mock_think_fn
        from alter.core.user_model import UserModel, Goal

        state = ConsciousnessState(user_id="test_user")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))
        state.update_narrative("User is working hard this week.")

        # Add a recent observation
        now = datetime.now().isoformat()
        state.add_observation(Observation(
            domain="health", aspect="sleep",
            summary="Sleep 5h", severity="elevated",
            prediction_error=0.65, timestamp=now,
        ))

        user = UserModel(user_id="test_user")
        user.set_purpose("Live a balanced life")
        user.add_goal(Goal(
            id="g1", domain="health",
            description="Sleep 7+ hours", time_horizon="quarter",
        ))
        user.record_daily_data({
            "date": datetime.now().date().isoformat(),
            "health": {"sleep_hours": 5.0},
        })

        think_fn = create_mock_think_fn(canned_response)
        engine = ConsciousnessEngine(
            consciousness_state=state,
            user_model=user,
            think_fn=think_fn,
            auto_save=auto_save,
        )
        return engine

    def test_tick_daily_review(self):
        engine = self._make_engine()
        result = engine.tick_sync("daily_review")

        assert result is not None
        assert len(result.observations) == 1
        assert result.narrative != ""
        assert result.summary is not None

    def test_tick_applies_narrative_update(self):
        engine = self._make_engine()
        engine.tick_sync("daily_review")

        assert engine.state.narrative == "User is pushing through a deadline. Sleep and mood declining."

    def test_tick_applies_world_model_updates(self):
        engine = self._make_engine()
        engine.tick_sync("daily_review")

        exp = engine.state.world_model.get_expectation("health", "sleep")
        assert exp is not None
        assert exp.numeric_value == 5.5
        assert "5-6h" in exp.description

    def test_tick_queues_notifications(self):
        engine = self._make_engine()
        engine.tick_sync("daily_review")

        pending = engine.state.get_pending_notifications()
        assert len(pending) == 1
        assert "sleep" in pending[0]["message"].lower()
        assert pending[0]["context"]["urgency"] == "medium"

    def test_tick_creates_dormant_questions(self):
        engine = self._make_engine()
        engine.tick_sync("daily_review")

        questions = engine.state.get_unresolved_questions()
        assert len(questions) >= 1
        q = questions[0]
        assert "sleep" in q.question.lower() or "deadline" in q.question.lower()
        assert q.created_by_tick == "daily_review"

    def test_tick_resolves_dormant_questions(self):
        from alter.consciousness.state import DormantQuestion

        engine = self._make_engine()
        # Add a question to resolve
        q = DormantQuestion(id="q_resolve", question="test?", domain="health")
        engine.state.add_dormant_question(q)

        # Canned response that resolves it
        resolve_response = json.dumps({
            "narrative": "Resolved.",
            "dormant_questions": {
                "new": [],
                "resolved": [{"question_id": "q_resolve", "resolution": "Answered!"}]
            }
        })
        from alter.consciousness.llm import create_mock_think_fn
        engine.think_fn = create_mock_think_fn(resolve_response)
        engine.tick_sync("daily_review")

        assert q.resolved is True
        assert q.resolution == "Answered!"

    def test_tick_stores_summary(self):
        engine = self._make_engine()
        engine.tick_sync("daily_review")

        today = datetime.now().date().isoformat()
        summary = engine.state.get_summary_for_period("daily", today)
        assert summary is not None
        assert "Burnout" in summary.content or "poor sleep" in summary.content.lower()
        assert summary.created_by_tick == "daily_review"

    def test_tick_records_token_usage(self):
        engine = self._make_engine()
        engine.tick_sync("daily_review")

        usage = engine.state.get_daily_token_usage()
        assert usage > 0

    def test_tick_saves_state(self, tmp_path):
        from alter.consciousness.state import ConsciousnessState, Expectation
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.llm import create_mock_think_fn

        state = ConsciousnessState(user_id="save_test")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep", description="test",
        ))
        state.update_narrative("Before tick.")

        save_path = tmp_path / "consciousness_state.json"
        # Monkey-patch save to use tmp_path
        state.save = lambda path=save_path: ConsciousnessState.save(state, path)

        engine = ConsciousnessEngine(
            consciousness_state=state,
            think_fn=create_mock_think_fn(CANNED_TICK_RESULT),
            auto_save=True,
        )
        engine.tick_sync("daily_review")

        # Verify file was written
        assert save_path.exists()
        loaded = ConsciousnessState.load("save_test", save_path)
        assert loaded.narrative != "Before tick."

    def test_tick_parse_failure_skips_gracefully(self):
        engine = self._make_engine(canned_response="not valid json at all")
        result = engine.tick_sync("daily_review")

        # Should return None, state unchanged
        assert result is None
        assert engine.state.narrative == "User is working hard this week."

    def test_tick_no_think_fn_raises(self):
        from alter.consciousness.state import ConsciousnessState
        from alter.consciousness.engine import ConsciousnessEngine
        state = ConsciousnessState(user_id="test")
        engine = ConsciousnessEngine(consciousness_state=state)

        with pytest.raises(RuntimeError, match="No think_fn"):
            engine.tick_sync("daily_review")

    def test_tick_weekly_reflect(self):
        engine = self._make_engine()
        result = engine.tick_sync("weekly_reflect")
        assert result is not None

    def test_tick_monthly_deep(self):
        engine = self._make_engine()
        result = engine.tick_sync("monthly_deep")
        assert result is not None

    def test_tick_urgent(self):
        engine = self._make_engine()
        result = engine.tick_sync("urgent", trigger_domain="health")
        assert result is not None

    def test_apply_creates_new_expectation(self):
        """When LLM suggests an expectation for an aspect that doesn't exist yet."""
        engine = self._make_engine()

        new_aspect_response = json.dumps({
            "narrative": "test",
            "world_model_updates": [
                {"domain": "career", "aspect": "work_hours",
                 "new_description": "Works 10h+ days",
                 "new_numeric_value": 10.5,
                 "reasoning": "Observed pattern"}
            ]
        })
        from alter.consciousness.llm import create_mock_think_fn
        engine.think_fn = create_mock_think_fn(new_aspect_response)
        engine.tick_sync("daily_review")

        exp = engine.state.world_model.get_expectation("career", "work_hours")
        assert exp is not None
        assert exp.numeric_value == 10.5
        assert exp.confidence == 0.3  # LLM-suggested, not observed


class TestHourlyObserve:
    """Tests for the hourly_observe pre-attentive loop."""

    def _make_engine_for_observe(self, sleep_value=5.0, think_response=CANNED_TICK_RESULT):
        from alter.consciousness.state import ConsciousnessState, Expectation
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.llm import create_mock_think_fn
        from alter.core.user_model import UserModel

        state = ConsciousnessState(user_id="test_user")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8h",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))

        user = UserModel(user_id="test_user")
        user.record_daily_data({
            "date": datetime.now().date().isoformat(),
            "health": {"sleep_hours": sleep_value},
        })

        engine = ConsciousnessEngine(
            consciousness_state=state,
            user_model=user,
            think_fn=create_mock_think_fn(think_response),
            auto_save=False,
        )
        return engine

    def test_hourly_observe_stores_observations(self):
        engine = self._make_engine_for_observe(sleep_value=5.0)
        obs = engine.hourly_observe()

        assert len(obs) == 1
        assert obs[0].domain == "health"
        assert obs[0].aspect == "sleep"
        assert len(engine.state.observations) >= 1

    def test_hourly_observe_no_data_returns_empty(self):
        from alter.consciousness.state import ConsciousnessState
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.core.user_model import UserModel

        state = ConsciousnessState(user_id="test")
        user = UserModel(user_id="test")  # No daily data
        engine = ConsciousnessEngine(
            consciousness_state=state, user_model=user, auto_save=False,
        )
        obs = engine.hourly_observe()
        assert len(obs) == 0

    def test_hourly_observe_no_user_model_returns_empty(self):
        from alter.consciousness.state import ConsciousnessState
        from alter.consciousness.engine import ConsciousnessEngine

        state = ConsciousnessState(user_id="test")
        engine = ConsciousnessEngine(consciousness_state=state, auto_save=False)
        obs = engine.hourly_observe()
        assert len(obs) == 0

    def test_hourly_observe_critical_triggers_urgent(self):
        """When sleep=0 → critical error → should fire urgent tick automatically."""
        from alter.consciousness.llm import create_recording_think_fn

        engine = self._make_engine_for_observe(sleep_value=0.0)
        think_fn, recorded = create_recording_think_fn(CANNED_TICK_RESULT)
        engine.think_fn = think_fn

        obs = engine.hourly_observe()

        # Should have detected critical
        critical = [o for o in obs if o.severity == "critical"]
        assert len(critical) >= 1

        # Should have fired urgent tick (think_fn was called)
        assert len(recorded) == 1
        assert "immediate attention" in recorded[0] or "urgent" in recorded[0].lower()

        # Watch event should be recorded
        assert len(engine.state.watch_events) == 1

    def test_hourly_observe_normal_no_urgent(self):
        """When values are within range, no urgent tick should fire."""
        from alter.consciousness.llm import create_recording_think_fn

        engine = self._make_engine_for_observe(sleep_value=7.5)
        think_fn, recorded = create_recording_think_fn(CANNED_TICK_RESULT)
        engine.think_fn = think_fn

        obs = engine.hourly_observe()

        # No critical → no urgent tick → think_fn not called
        assert len(recorded) == 0


# ─── C3: Async Hourly Observe Tests ───


class TestHourlyObserveAsync:
    """Tests for the async version of hourly_observe."""

    def _make_engine_for_observe(self, sleep_value=5.0, think_response=CANNED_TICK_RESULT):
        """Create an engine with daily data for observe testing."""
        from alter.consciousness.state import ConsciousnessState, Expectation
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.llm import create_mock_think_fn
        from alter.core.user_model import UserModel

        state = ConsciousnessState(user_id="test_user")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))

        user = UserModel(user_id="test_user")
        user.record_daily_data({
            "date": datetime.now().date().isoformat(),
            "health": {"sleep_hours": sleep_value},
        })

        engine = ConsciousnessEngine(
            consciousness_state=state,
            user_model=user,
            think_fn=create_mock_think_fn(think_response),
            auto_save=False,
        )
        return engine

    @pytest.mark.asyncio
    async def test_async_observe_produces_observations(self):
        """hourly_observe_async() should detect prediction errors."""
        engine = self._make_engine_for_observe(sleep_value=5.0)
        obs = await engine.hourly_observe_async()
        assert len(obs) >= 1
        assert obs[0].domain == "health"

    @pytest.mark.asyncio
    async def test_async_observe_no_data_returns_empty(self):
        """Without daily data, async observe returns empty list."""
        from alter.consciousness.state import ConsciousnessState
        from alter.consciousness.engine import ConsciousnessEngine

        state = ConsciousnessState(user_id="test")
        engine = ConsciousnessEngine(consciousness_state=state, auto_save=False)
        obs = await engine.hourly_observe_async()
        assert obs == []

    @pytest.mark.asyncio
    async def test_async_observe_critical_fires_urgent(self):
        """Critical signals should fire urgent tick via async tick()."""
        from alter.consciousness.llm import create_recording_think_fn

        engine = self._make_engine_for_observe(sleep_value=0.0)
        think_fn, recorded = create_recording_think_fn(CANNED_TICK_RESULT)
        engine.think_fn = think_fn

        obs = await engine.hourly_observe_async()

        critical = [o for o in obs if o.severity == "critical"]
        assert len(critical) >= 1
        # Urgent tick should have been fired (async path)
        assert len(recorded) == 1

    @pytest.mark.asyncio
    async def test_async_observe_normal_no_urgent(self):
        """Normal values should not fire urgent tick."""
        from alter.consciousness.llm import create_recording_think_fn

        engine = self._make_engine_for_observe(sleep_value=7.5)
        think_fn, recorded = create_recording_think_fn(CANNED_TICK_RESULT)
        engine.think_fn = think_fn

        obs = await engine.hourly_observe_async()
        assert len(recorded) == 0


# ─── C4: Standalone Adapter Tests ───


class TestStandaloneAdapter:
    """Tests for the StandaloneAdapter — APScheduler + ConsciousnessEngine wiring."""

    def _make_adapter(self, tmp_path, sleep_value=5.0):
        """Create a StandaloneAdapter with mock think_fn and temp data."""
        from alter.consciousness.state import ConsciousnessState, Expectation
        from alter.consciousness.llm import create_mock_think_fn
        from alter.core.user_model import UserModel
        from alter.adapters.standalone import StandaloneAdapter

        # Set up user data on disk
        user_dir = tmp_path / "data" / "user_data" / "test_adapter"
        user_dir.mkdir(parents=True)

        user = UserModel(user_id="test_adapter")
        user.set_purpose("Test purpose")
        user.record_daily_data({
            "date": datetime.now().date().isoformat(),
            "health": {"sleep_hours": sleep_value},
        })
        user.save(user_dir / "user_model.json")

        state = ConsciousnessState(user_id="test_adapter")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))
        state.save(user_dir / "consciousness_state.json")

        # Create adapter with mock think_fn (bypass default LLM creation)
        mock_fn = create_mock_think_fn(CANNED_TICK_RESULT)
        adapter = StandaloneAdapter(
            user_id="test_adapter",
            provider="mock",
            think_fn=mock_fn,
        )
        # Override loaded state/user with our test data
        adapter.user_model = user
        adapter.consciousness_state = state
        adapter.engine.state = state
        adapter.engine.user_model = user
        adapter.engine.auto_save = False

        return adapter

    def test_adapter_creation(self, tmp_path):
        """Adapter should create engine with all components."""
        adapter = self._make_adapter(tmp_path)
        assert adapter.engine is not None
        assert adapter.user_id == "test_adapter"
        assert adapter.provider == "mock"
        assert not adapter.is_running

    def test_adapter_get_status(self, tmp_path):
        """get_status() should return engine status dict."""
        adapter = self._make_adapter(tmp_path)
        status = adapter.get_status()
        assert status["user_id"] == "test_adapter"
        assert status["running"] is False
        assert "narrative" in status
        assert "world_model_domains" in status
        assert "pending_notifications" in status

    def test_adapter_activity_log(self, tmp_path):
        """Activity log should record entries."""
        adapter = self._make_adapter(tmp_path)
        assert len(adapter.get_activity()) == 0

        adapter._log_activity("test_event", {"data": "value"})
        activity = adapter.get_activity()
        assert len(activity) == 1
        assert activity[0]["event_type"] == "test_event"
        assert activity[0]["data"] == "value"
        assert "timestamp" in activity[0]

    def test_adapter_activity_log_ordering(self, tmp_path):
        """Activity should be returned newest first."""
        adapter = self._make_adapter(tmp_path)
        adapter._log_activity("first", {})
        adapter._log_activity("second", {})
        adapter._log_activity("third", {})

        activity = adapter.get_activity()
        assert activity[0]["event_type"] == "third"
        assert activity[2]["event_type"] == "first"

    def test_adapter_activity_log_limit(self, tmp_path):
        """Activity log should respect the limit parameter."""
        adapter = self._make_adapter(tmp_path)
        for i in range(10):
            adapter._log_activity(f"event_{i}", {})

        assert len(adapter.get_activity(limit=3)) == 3
        assert len(adapter.get_activity(limit=50)) == 10

    def test_adapter_activity_log_max_entries(self, tmp_path):
        """Activity log should cap at MAX_ACTIVITY_LOG entries."""
        from alter.adapters.standalone import MAX_ACTIVITY_LOG

        adapter = self._make_adapter(tmp_path)
        for i in range(MAX_ACTIVITY_LOG + 50):
            adapter._log_activity(f"event_{i}", {})

        assert len(adapter._activity_log) == MAX_ACTIVITY_LOG

    @pytest.mark.asyncio
    async def test_adapter_trigger_tick(self, tmp_path):
        """trigger_tick() should run a full tick and log activity."""
        adapter = self._make_adapter(tmp_path)
        result = await adapter.trigger_tick("daily_review")

        assert result is not None
        assert len(result.observations) >= 1
        assert len(result.notifications) >= 1

        # Should be logged
        activity = adapter.get_activity()
        assert len(activity) == 1
        assert "manual_daily_review" in activity[0]["event_type"]

    @pytest.mark.asyncio
    async def test_adapter_trigger_observe(self, tmp_path):
        """trigger_observe() should run hourly observe and log activity."""
        adapter = self._make_adapter(tmp_path)
        observations = await adapter.trigger_observe()

        assert len(observations) >= 1

        # Should be logged
        activity = adapter.get_activity()
        assert len(activity) == 1
        assert activity[0]["event_type"] == "manual_observe"

    @pytest.mark.asyncio
    async def test_adapter_start_stop(self, tmp_path):
        """Adapter should start and stop the scheduler."""
        adapter = self._make_adapter(tmp_path)

        adapter.start()
        assert adapter.is_running
        # Start should log activity
        activity = adapter.get_activity()
        assert any(a["event_type"] == "engine_started" for a in activity)

        adapter.stop()
        assert not adapter.is_running
        activity = adapter.get_activity()
        assert any(a["event_type"] == "engine_stopped" for a in activity)

    @pytest.mark.asyncio
    async def test_adapter_double_start(self, tmp_path):
        """Starting an already-running adapter should not crash."""
        adapter = self._make_adapter(tmp_path)
        adapter.start()
        adapter.start()  # Should not crash
        assert adapter.is_running
        adapter.stop()


# ─── C4: Consciousness API Router Tests ───


class TestConsciousnessRouter:
    """Tests for the consciousness API endpoints."""

    def test_status_without_consciousness(self):
        """GET /status should return 503 when consciousness is off."""
        from fastapi.testclient import TestClient
        from alter.api.app import create_app

        app = create_app()
        app.state.consciousness = None
        client = TestClient(app)

        response = client.get("/api/v1/consciousness/status")
        assert response.status_code == 503

    def test_activity_without_consciousness(self):
        """GET /activity should return 503 when consciousness is off."""
        from fastapi.testclient import TestClient
        from alter.api.app import create_app

        app = create_app()
        app.state.consciousness = None
        client = TestClient(app)

        response = client.get("/api/v1/consciousness/activity")
        assert response.status_code == 503


# ─── C5: Dormant Question Readiness Tests ───


class TestDormantReadiness:
    """Tests for dormant question readiness tracking."""

    def _make_state_with_questions(self):
        """Create state with dormant questions and expectations."""
        from alter.consciousness.state import ConsciousnessState, DormantQuestion, Expectation

        state = ConsciousnessState(user_id="test")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))

        state.add_dormant_question(DormantQuestion(
            id="q1",
            question="Will sleep recover after the deadline?",
            domain="health",
            resolution_signals=["sleep returns to 7h+", "sleep recovers"],
            context="Sleep dropped during work crunch",
            readiness=0.0,
        ))

        state.add_dormant_question(DormantQuestion(
            id="q2",
            question="Is the new exercise routine sustainable?",
            domain="health",
            resolution_signals=["exercise maintained for 2 weeks"],
            context="Started new routine last week",
            readiness=0.3,
        ))

        state.add_dormant_question(DormantQuestion(
            id="q3",
            question="Will career satisfaction improve?",
            domain="career",
            resolution_signals=["satisfaction improves after promotion"],
            context="User expecting promotion",
            readiness=0.0,
        ))

        return state

    def test_readiness_bump_domain_match(self):
        """Observations in same domain should bump readiness."""
        from alter.consciousness.state import Observation

        state = self._make_state_with_questions()
        obs = [Observation(
            domain="health", aspect="sleep",
            summary="Sleep was 6h today",
            severity="normal", prediction_error=0.2,
        )]

        newly_ready = state.update_dormant_readiness(obs)

        # q1 and q2 are health domain — should have been bumped
        q1 = next(q for q in state.dormant_questions if q.id == "q1")
        q2 = next(q for q in state.dormant_questions if q.id == "q2")
        q3 = next(q for q in state.dormant_questions if q.id == "q3")

        assert q1.readiness > 0.0
        assert q2.readiness > 0.3
        assert q3.readiness == 0.0  # career domain, no match
        assert len(newly_ready) == 0  # not ready yet

    def test_readiness_bump_elevated_severity(self):
        """Elevated severity in same domain should bump more."""
        from alter.consciousness.state import Observation
        from alter.consciousness.config import READINESS_BUMP_DOMAIN_MATCH, READINESS_BUMP_ELEVATED

        state = self._make_state_with_questions()
        obs = [Observation(
            domain="health", aspect="sleep",
            summary="Sleep was 4h today",
            severity="elevated", prediction_error=0.6,
        )]

        state.update_dormant_readiness(obs)
        q1 = next(q for q in state.dormant_questions if q.id == "q1")

        # Should get elevated bump, not just domain match bump
        assert q1.readiness >= READINESS_BUMP_ELEVATED
        assert q1.readiness > READINESS_BUMP_DOMAIN_MATCH

    def test_readiness_bump_signal_keyword_match(self):
        """Resolution signal keyword match should give significant bump."""
        from alter.consciousness.state import Observation
        from alter.consciousness.config import READINESS_BUMP_SIGNAL_MATCH

        state = self._make_state_with_questions()
        # This observation contains "sleep" and "recovers" matching q1's signal
        obs = [Observation(
            domain="health", aspect="sleep",
            summary="Sleep recovers to normal levels at 7.5 hours",
            severity="normal", prediction_error=0.1,
        )]

        state.update_dormant_readiness(obs)
        q1 = next(q for q in state.dormant_questions if q.id == "q1")

        assert q1.readiness >= READINESS_BUMP_SIGNAL_MATCH

    def test_readiness_crosses_threshold(self):
        """When readiness crosses threshold, question becomes ready."""
        from alter.consciousness.state import Observation, DormantQuestion

        state = self._make_state_with_questions()
        # Set q2 close to threshold (0.7)
        q2 = next(q for q in state.dormant_questions if q.id == "q2")
        q2.readiness = 0.65

        # An observation with signal match should push it over
        obs = [Observation(
            domain="health", aspect="exercise",
            summary="Exercise maintained for 2 weeks consistently",
            severity="normal", prediction_error=0.1,
        )]

        newly_ready = state.update_dormant_readiness(obs)

        assert len(newly_ready) == 1
        assert newly_ready[0].id == "q2"
        assert q2.is_ready()

    def test_readiness_accumulates_over_multiple_observations(self):
        """Multiple observations should accumulate readiness."""
        from alter.consciousness.state import Observation

        state = self._make_state_with_questions()
        q1 = next(q for q in state.dormant_questions if q.id == "q1")
        initial_readiness = q1.readiness

        # Multiple health observations
        obs = [
            Observation(domain="health", aspect="sleep",
                       summary="Sleep 6h", severity="normal", prediction_error=0.2),
            Observation(domain="health", aspect="exercise",
                       summary="Exercise 30min", severity="normal", prediction_error=0.1),
        ]

        state.update_dormant_readiness(obs)

        # Should have accumulated bumps from both observations
        assert q1.readiness > initial_readiness

    def test_readiness_capped_at_one(self):
        """Readiness should never exceed 1.0."""
        from alter.consciousness.state import Observation

        state = self._make_state_with_questions()
        q1 = next(q for q in state.dormant_questions if q.id == "q1")
        q1.readiness = 0.95

        obs = [Observation(
            domain="health", aspect="sleep",
            summary="Sleep recovers to 8 hours",
            severity="elevated", prediction_error=0.6,
        )]

        state.update_dormant_readiness(obs)
        assert q1.readiness <= 1.0

    def test_readiness_skips_resolved_questions(self):
        """Resolved questions should not have readiness updated."""
        from alter.consciousness.state import Observation

        state = self._make_state_with_questions()
        state.resolve_question("q1", "Sleep recovered after deadline")

        q1 = next(q for q in state.dormant_questions if q.id == "q1")
        initial_readiness = q1.readiness

        obs = [Observation(
            domain="health", aspect="sleep",
            summary="Sleep recovers perfectly",
            severity="normal", prediction_error=0.1,
        )]

        state.update_dormant_readiness(obs)
        assert q1.readiness == initial_readiness  # Unchanged

    def test_readiness_no_match_no_bump(self):
        """Observations with no domain or signal match should not bump readiness."""
        from alter.consciousness.state import Observation

        state = self._make_state_with_questions()
        obs = [Observation(
            domain="relationships", aspect="social",
            summary="Had dinner with friends",
            severity="normal", prediction_error=0.1,
        )]

        state.update_dormant_readiness(obs)

        for q in state.dormant_questions:
            if q.id in ("q1", "q2"):
                # health questions — no match with relationships domain
                assert q.readiness == 0.0 or q.readiness == 0.3  # unchanged

    def test_get_ready_questions(self):
        """get_ready_questions() should return questions above threshold."""
        from alter.consciousness.state import DormantQuestion

        state = self._make_state_with_questions()
        assert len(state.get_ready_questions()) == 0

        # Push q1 above threshold
        q1 = next(q for q in state.dormant_questions if q.id == "q1")
        q1.readiness = 0.8

        ready = state.get_ready_questions()
        assert len(ready) == 1
        assert ready[0].id == "q1"


# ─── C5: Narrative History Tests ───


class TestNarrativeHistory:
    """Tests for narrative history tracking."""

    def test_update_narrative_tracks_history(self):
        """update_narrative() should push previous narrative to history."""
        from alter.consciousness.state import ConsciousnessState

        state = ConsciousnessState(user_id="test")
        state.update_narrative("First narrative")
        assert state.narrative == "First narrative"
        assert len(state.narrative_history) == 0  # First set, nothing to archive

        state.update_narrative("Second narrative")
        assert state.narrative == "Second narrative"
        assert len(state.narrative_history) == 1
        assert state.narrative_history[0]["narrative"] == "First narrative"

    def test_narrative_history_has_timestamps(self):
        """Each history entry should have a timestamp."""
        from alter.consciousness.state import ConsciousnessState

        state = ConsciousnessState(user_id="test")
        state.update_narrative("v1")
        state.update_narrative("v2")

        assert "timestamp" in state.narrative_history[0]

    def test_narrative_history_max_entries(self):
        """History should cap at MAX_NARRATIVE_HISTORY entries."""
        from alter.consciousness.state import ConsciousnessState
        from alter.consciousness.config import MAX_NARRATIVE_HISTORY

        state = ConsciousnessState(user_id="test")
        for i in range(MAX_NARRATIVE_HISTORY + 5):
            state.update_narrative(f"Narrative version {i}")

        assert len(state.narrative_history) == MAX_NARRATIVE_HISTORY
        # Most recent history entry should be second-to-last narrative
        assert f"version {MAX_NARRATIVE_HISTORY + 3}" in state.narrative_history[-1]["narrative"]

    def test_narrative_same_value_no_history(self):
        """Setting the same narrative shouldn't create a history entry."""
        from alter.consciousness.state import ConsciousnessState

        state = ConsciousnessState(user_id="test")
        state.update_narrative("Same narrative")
        state.update_narrative("Same narrative")

        assert len(state.narrative_history) == 0

    def test_narrative_history_persistence(self):
        """Narrative history should survive to_dict/from_dict round-trip."""
        from alter.consciousness.state import ConsciousnessState

        state = ConsciousnessState(user_id="test")
        state.update_narrative("v1")
        state.update_narrative("v2")

        data = state.to_dict()
        restored = ConsciousnessState.from_dict(data)

        assert restored.narrative == "v2"
        assert len(restored.narrative_history) == 1
        assert restored.narrative_history[0]["narrative"] == "v1"


# ─── C5: Ready Questions in Context Assembly ───


class TestReadyQuestionsContext:
    """Tests for ready questions appearing in context assembly."""

    def _make_state_with_ready_question(self):
        """Create state with one ready and one not-ready question."""
        from alter.consciousness.state import ConsciousnessState, DormantQuestion, Expectation

        state = ConsciousnessState(user_id="test")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8,
        ))
        state.update_narrative("Testing narrative")

        # Ready question (above threshold)
        state.add_dormant_question(DormantQuestion(
            id="ready1",
            question="Has sleep recovered?",
            domain="health",
            resolution_signals=["sleep at 7h+"],
            readiness=0.8,  # Above 0.7 threshold
        ))

        # Not-ready question
        state.add_dormant_question(DormantQuestion(
            id="notready1",
            question="Is the diet working?",
            domain="health",
            resolution_signals=["weight stable"],
            readiness=0.2,
        ))

        return state

    def test_format_ready_questions(self):
        """format_ready_questions() should format ready questions."""
        from alter.consciousness.context import format_ready_questions
        from alter.consciousness.state import DormantQuestion

        questions = [DormantQuestion(
            id="q1",
            question="Test question?",
            context="Test context",
            domain="health",
            resolution_signals=["signal1"],
            readiness=0.8,
        )]

        result = format_ready_questions(questions)
        assert "Test question?" in result
        assert "Test context" in result
        assert "signal1" in result
        assert "80%" in result

    def test_format_ready_questions_empty(self):
        """format_ready_questions() returns empty string when no questions."""
        from alter.consciousness.context import format_ready_questions
        assert format_ready_questions([]) == ""

    def test_daily_context_includes_ready_questions(self):
        """Daily context should have a ready_questions section when available."""
        from alter.consciousness.context import ContextAssembler

        state = self._make_state_with_ready_question()
        assembler = ContextAssembler(state)
        context = assembler.assemble("daily_review")

        assert "ready_questions" in context.section_names
        assert "Has sleep recovered?" in context.full_text
        # The ready question should NOT appear in dormant_questions section
        dormant_section = next(
            (s for s in context.sections if s.name == "dormant_questions"), None
        )
        if dormant_section:
            assert "Has sleep recovered?" not in dormant_section.content

    def test_weekly_context_includes_ready_questions(self):
        """Weekly context should have ready questions when available."""
        from alter.consciousness.context import ContextAssembler

        state = self._make_state_with_ready_question()
        assembler = ContextAssembler(state)
        context = assembler.assemble("weekly_reflect")

        assert "ready_questions" in context.section_names

    def test_monthly_context_includes_ready_questions(self):
        """Monthly context should have ready questions when available."""
        from alter.consciousness.context import ContextAssembler

        state = self._make_state_with_ready_question()
        assembler = ContextAssembler(state)
        context = assembler.assemble("monthly_deep")

        assert "ready_questions" in context.section_names

    def test_no_ready_questions_no_section(self):
        """When no questions are ready, ready_questions section should be absent."""
        from alter.consciousness.context import ContextAssembler
        from alter.consciousness.state import ConsciousnessState, DormantQuestion

        state = ConsciousnessState(user_id="test")
        state.add_dormant_question(DormantQuestion(
            id="low1", question="Low readiness",
            domain="health", resolution_signals=[], readiness=0.1,
        ))
        assembler = ContextAssembler(state)
        context = assembler.assemble("daily_review")

        assert "ready_questions" not in context.section_names


# ─── C5: Engine Readiness Integration Tests ───


class TestEngineReadinessIntegration:
    """Tests for readiness tracking integrated into engine hourly observe."""

    def _make_engine_with_questions(self, sleep_value=5.0):
        """Create engine with dormant questions for testing readiness updates."""
        from alter.consciousness.state import ConsciousnessState, Expectation, DormantQuestion
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.llm import create_mock_think_fn
        from alter.core.user_model import UserModel

        state = ConsciousnessState(user_id="test_user")
        state.world_model.set_expectation(Expectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            numeric_value=7.5, numeric_range=(7.0, 8.0),
            data_field="sleep_hours", confidence=0.8, data_points=14,
        ))

        state.add_dormant_question(DormantQuestion(
            id="dq1",
            question="Will sleep improve?",
            domain="health",
            resolution_signals=["sleep returns to normal"],
            readiness=0.0,
        ))

        user = UserModel(user_id="test_user")
        user.record_daily_data({
            "date": datetime.now().date().isoformat(),
            "health": {"sleep_hours": sleep_value},
        })

        engine = ConsciousnessEngine(
            consciousness_state=state,
            user_model=user,
            think_fn=create_mock_think_fn(CANNED_TICK_RESULT),
            auto_save=False,
        )
        return engine

    def test_hourly_observe_updates_readiness(self):
        """hourly_observe should update dormant question readiness."""
        engine = self._make_engine_with_questions(sleep_value=5.0)
        dq = next(q for q in engine.state.dormant_questions if q.id == "dq1")
        assert dq.readiness == 0.0

        engine.hourly_observe()

        # Health observation should have bumped health-domain question
        assert dq.readiness > 0.0

    @pytest.mark.asyncio
    async def test_hourly_observe_async_updates_readiness(self):
        """hourly_observe_async should also update readiness."""
        engine = self._make_engine_with_questions(sleep_value=5.0)
        dq = next(q for q in engine.state.dormant_questions if q.id == "dq1")
        assert dq.readiness == 0.0

        await engine.hourly_observe_async()

        assert dq.readiness > 0.0


# ─── C5: Prompt Enhancement Tests ───


class TestPromptNarrativeContinuity:
    """Tests for enhanced prompt language around narrative and ready questions."""

    def test_daily_prompt_mentions_ready_questions(self):
        """Daily reasoning should mention resolving ready questions."""
        from alter.consciousness.prompts import DAILY_REASONING
        assert "Ready for Resolution" in DAILY_REASONING

    def test_daily_prompt_has_narrative_continuity(self):
        """Daily reasoning should encourage narrative continuity."""
        from alter.consciousness.prompts import DAILY_REASONING
        assert "continuous thread" in DAILY_REASONING or "Build on" in DAILY_REASONING

    def test_weekly_prompt_mentions_ready_questions(self):
        """Weekly reasoning should mention resolving ready questions."""
        from alter.consciousness.prompts import WEEKLY_REASONING
        assert "Ready for Resolution" in WEEKLY_REASONING

    def test_weekly_prompt_has_narrative_continuity(self):
        """Weekly reasoning should encourage narrative evolution."""
        from alter.consciousness.prompts import WEEKLY_REASONING
        assert "living story" in WEEKLY_REASONING or "Evolve" in WEEKLY_REASONING

    def test_monthly_prompt_mentions_ready_questions(self):
        """Monthly reasoning should mention resolving ready questions."""
        from alter.consciousness.prompts import MONTHLY_REASONING
        assert "Ready for Resolution" in MONTHLY_REASONING


# ─── OpenClaw Adapter Tests (C6) ───


class MockOpenClawSession:
    """Mock OpenClaw session for testing."""

    def __init__(self, user_id: str = "test_user", chat_response: str = "{}"):
        self._user_id = user_id
        self._chat_response = chat_response
        self.sent_messages: list = []
        self.chat_prompts: list = []

    @property
    def user_id(self) -> str:
        return self._user_id

    def chat(self, prompt: str) -> str:
        self.chat_prompts.append(prompt)
        return self._chat_response

    def send_message(self, message: str) -> None:
        self.sent_messages.append(message)


class TestOpenClawSession:
    """Tests for the OpenClaw session protocol."""

    def test_mock_session_satisfies_protocol(self):
        """MockOpenClawSession should satisfy the OpenClawSession protocol."""
        from alter.adapters.openclaw.adapter import OpenClawSession
        session = MockOpenClawSession()
        assert isinstance(session, OpenClawSession)

    def test_session_chat_returns_response(self):
        """session.chat() should return the configured response."""
        session = MockOpenClawSession(chat_response="hello")
        assert session.chat("prompt") == "hello"

    def test_session_send_message_records(self):
        """session.send_message() should record sent messages."""
        session = MockOpenClawSession()
        session.send_message("test notification")
        assert session.sent_messages == ["test notification"]


class TestOpenClawAdapter:
    """Tests for OpenClawAdapter."""

    def _make_adapter(self, chat_response: str = "{}", user_id: str = "oc_test"):
        from alter.adapters.openclaw.adapter import OpenClawAdapter
        session = MockOpenClawSession(user_id=user_id, chat_response=chat_response)
        adapter = OpenClawAdapter(session, user_id=user_id, auto_save=False)
        return adapter, session

    def test_adapter_creates_engine(self):
        """Adapter should create a ConsciousnessEngine."""
        adapter, _ = self._make_adapter()
        assert adapter.engine is not None
        assert adapter.engine.think_fn is not None

    def test_adapter_uses_session_user_id(self):
        """Adapter should use session.user_id by default."""
        from alter.adapters.openclaw.adapter import OpenClawAdapter
        session = MockOpenClawSession(user_id="from_session")
        adapter = OpenClawAdapter(session, auto_save=False)
        assert adapter.user_id == "from_session"

    def test_adapter_user_id_override(self):
        """Explicit user_id should override session.user_id."""
        adapter, _ = self._make_adapter(user_id="override_id")
        assert adapter.user_id == "override_id"

    def test_think_fn_delegates_to_session_chat(self):
        """The think_fn should call session.chat()."""
        adapter, session = self._make_adapter(chat_response="LLM output")
        result = adapter._think_fn("test prompt")
        assert result == "LLM output"
        assert session.chat_prompts == ["test prompt"]

    def test_get_status_returns_dict(self):
        """get_status() should return a status dict."""
        adapter, _ = self._make_adapter()
        status = adapter.get_status()
        assert "user_id" in status
        assert "narrative" in status
        assert "pending_notifications" in status
        assert "dormant_questions" in status
        assert status["user_id"] == "oc_test"

    @pytest.mark.asyncio
    async def test_trigger_tick_with_valid_response(self):
        """trigger_tick should run the engine and return a result."""
        canned = json.dumps({
            "observations": [{"domain": "health", "aspect": "sleep", "observation": "Slept 7h", "significance": "noise"}],
            "insights": [{"description": "Sleeping well", "confidence": 0.8, "domains": ["health"]}],
            "decisions": [],
            "notifications": [],
            "dormant_questions": {"new": [], "resolved": []},
            "world_model_updates": [],
            "narrative": "Test narrative from OpenClaw",
            "summary": {"content": "Test summary", "key_insights": [], "key_facts": {}, "prediction_errors_summary": "none"},
        })
        adapter, _ = self._make_adapter(chat_response=canned)
        result = await adapter.trigger_tick("daily_review")
        assert result is not None
        assert result.narrative == "Test narrative from OpenClaw"

    @pytest.mark.asyncio
    async def test_trigger_tick_delivers_notifications(self):
        """Notifications from a tick should be sent via session.send_message()."""
        canned = json.dumps({
            "observations": [],
            "insights": [],
            "decisions": [],
            "notifications": [{"message": "Hey, you should sleep more!", "urgency": "gentle"}],
            "dormant_questions": {"new": [], "resolved": []},
            "world_model_updates": [],
            "narrative": "",
            "summary": None,
        })
        adapter, session = self._make_adapter(chat_response=canned)
        result = await adapter.trigger_tick("daily_review")
        assert result is not None
        assert "Hey, you should sleep more!" in session.sent_messages

    @pytest.mark.asyncio
    async def test_trigger_observe(self):
        """trigger_observe should return a list of observations."""
        adapter, _ = self._make_adapter()
        observations = await adapter.trigger_observe()
        # With no user_model, engine returns empty list
        assert isinstance(observations, list)

    def test_notification_delivery_failure_logged(self):
        """Failed notification delivery should not raise."""
        from alter.adapters.openclaw.adapter import OpenClawAdapter

        class FailingSession(MockOpenClawSession):
            def send_message(self, message: str) -> None:
                raise ConnectionError("Channel unavailable")

        session = FailingSession(user_id="fail_test")
        adapter = OpenClawAdapter(session, auto_save=False)

        # Simulate a result with notifications
        from alter.consciousness.parse import TickResult, TickNotification, DormantQuestionChanges

        mock_result = TickResult(
            observations=[],
            insights=[],
            decisions=[],
            notifications=[TickNotification(message="Test", urgency="low")],
            world_model_updates=[],
            dormant_questions=DormantQuestionChanges(new=[], resolved=[]),
            narrative="",
            summary=None,
        )
        # Should not raise
        adapter._deliver_notifications(mock_result)


class TestOpenClawTools:
    """Tests for OpenClaw tool functions."""

    def _make_adapter(self):
        from alter.adapters.openclaw.adapter import OpenClawAdapter
        session = MockOpenClawSession(user_id="tools_test")
        return OpenClawAdapter(session, auto_save=False)

    def test_alter_status_tool(self):
        """alter_status should return status dict."""
        from alter.adapters.openclaw.tools import alter_status
        adapter = self._make_adapter()
        result = alter_status(adapter)
        assert "user_id" in result
        assert result["user_id"] == "tools_test"

    @pytest.mark.asyncio
    async def test_alter_reflect_invalid_tick_type(self):
        """alter_reflect with invalid tick_type should return error."""
        from alter.adapters.openclaw.tools import alter_reflect
        adapter = self._make_adapter()
        result = await alter_reflect(adapter, tick_type="invalid")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_alter_observe_tool(self):
        """alter_observe should return observation count."""
        from alter.adapters.openclaw.tools import alter_observe
        adapter = self._make_adapter()
        result = await alter_observe(adapter)
        assert "observation_count" in result

    def test_alter_narrative_tool(self):
        """alter_narrative should return narrative and history count."""
        from alter.adapters.openclaw.tools import alter_narrative
        adapter = self._make_adapter()
        result = alter_narrative(adapter)
        assert "narrative" in result
        assert "history_count" in result

    def test_alter_questions_tool(self):
        """alter_questions should return question data."""
        from alter.adapters.openclaw.tools import alter_questions
        adapter = self._make_adapter()
        result = alter_questions(adapter)
        assert "total_unresolved" in result
        assert "ready_count" in result
        assert "questions" in result

    def test_alter_notify_tool(self):
        """alter_notify should return notifications and mark delivered."""
        from alter.adapters.openclaw.tools import alter_notify
        adapter = self._make_adapter()
        # Add a notification first
        adapter.consciousness_state.add_notification(
            message="Test notification",
            context={"urgency": "gentle"},
        )
        result = alter_notify(adapter)
        assert result["notification_count"] == 1
        assert result["notifications"][0]["message"] == "Test notification"
        # Should be marked delivered now
        assert len(adapter.consciousness_state.get_pending_notifications()) == 0

    def test_tools_registry(self):
        """TOOLS registry should have all 6 tools."""
        from alter.adapters.openclaw.tools import TOOLS
        expected = {"alter_status", "alter_reflect", "alter_observe",
                    "alter_narrative", "alter_questions", "alter_notify"}
        assert set(TOOLS.keys()) == expected

    def test_tools_registry_async_flags(self):
        """Async flags should match function types."""
        from alter.adapters.openclaw.tools import TOOLS
        assert TOOLS["alter_status"]["async"] is False
        assert TOOLS["alter_reflect"]["async"] is True
        assert TOOLS["alter_observe"]["async"] is True
        assert TOOLS["alter_narrative"]["async"] is False
