"""
High-level tests for Constitution system.

Test philosophy: These tests define the expected behavior of the constitution system.
Write tests first, implement later (TDD approach).
"""

import pytest
from pathlib import Path


class TestConstitutionLoader:
    """Tests for loading and validating constitutions."""

    def test_load_default_constitution(self):
        """Should load default constitution when no custom one exists."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        assert constitution is not None
        assert constitution.version == "1.0.0"
        assert len(constitution.core_principles) >= 3  # At least required principles

    def test_load_custom_constitution(self, tmp_path):
        """Should load custom constitution if it exists."""
        from alter.core.constitution import Constitution

        # Create custom constitution
        custom_path = tmp_path / "my_constitution.yaml"
        custom_path.write_text("""
version: "1.0.0"
constitution_type: "custom"
core_principles:
  - id: "autonomy"
    name: "My Autonomy"
    rules: ["Rule 1"]
    weight: 10
  - id: "ethics"
    name: "My Ethics"
    rules: ["Rule 1"]
    weight: 10
  - id: "transparency"
    name: "My Transparency"
    rules: ["Rule 1"]
    weight: 10
        """)

        constitution = Constitution.load(custom_path)

        assert constitution.constitution_type == "custom"
        assert constitution.core_principles[0].name == "My Autonomy"

    def test_validate_required_principles(self):
        """Should fail validation if required principles are missing."""
        from alter.core.constitution import Constitution, ConstitutionValidationError

        invalid_yaml = """
version: "1.0.0"
core_principles:
  - id: "autonomy"
    name: "Autonomy"
    rules: ["Rule 1"]
    weight: 10
  # Missing ethics and transparency
        """

        with pytest.raises(ConstitutionValidationError) as exc_info:
            Constitution.from_yaml(invalid_yaml)

        assert "required principles" in str(exc_info.value).lower()

    def test_principle_weights_valid_range(self):
        """Should validate that principle weights are in range 1-10."""
        from alter.core.constitution import Constitution, ConstitutionValidationError

        invalid_yaml = """
version: "1.0.0"
core_principles:
  - id: "autonomy"
    weight: 15  # Invalid: > 10
    rules: ["Rule 1"]
        """

        with pytest.raises(ConstitutionValidationError):
            Constitution.from_yaml(invalid_yaml)


class TestConstitutionDecisions:
    """Tests for constitution-based decision making."""

    def test_validate_decision_approved(self):
        """Should approve decisions that align with constitution."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        decision = {
            "action": "schedule_exercise",
            "domain": "health",
            "impact": {"health": 1, "time": -1}
        }

        result = constitution.validate_decision(decision)

        assert result.approved is True
        assert result.reasoning is not None

    def test_validate_decision_rejected(self):
        """Should reject decisions that violate constitution."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        decision = {
            "action": "skip_sleep_for_week",
            "domain": "health",
            "impact": {"health": -5, "productivity": 2}
        }

        result = constitution.validate_decision(decision)

        assert result.approved is False
        assert "health" in result.reasoning.lower()

    def test_resolve_principle_conflict(self):
        """Should resolve conflicts using principle weights."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        # Conflict: long-term health vs short-term productivity
        conflict = {
            "options": [
                {"name": "work_late", "principles": {"long_term": -1, "productivity": 1}},
                {"name": "rest", "principles": {"long_term": 1, "productivity": -1}}
            ]
        }

        result = constitution.resolve_conflict(conflict)

        # Should prioritize long-term (higher weight in default constitution)
        assert result.chosen_option == "rest"
        assert result.reasoning is not None


class TestConstitutionOverrides:
    """Tests for override system."""

    def test_temporary_override_approved(self):
        """Should approve valid temporary override."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        override_request = {
            "type": "temporary",
            "rule_id": "health/sleep_hours",
            "duration_days": 3,
            "reason": "Project deadline"
        }

        result = constitution.request_override(override_request)

        assert result.approved is True
        assert result.override_id is not None
        assert result.expires_at is not None

    def test_temporary_override_rejected_blocked_principle(self):
        """Should reject override of blocked principles."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        override_request = {
            "type": "temporary",
            "rule_id": "ethics/no_harm",
            "duration_days": 1,
            "reason": "Testing"
        }

        result = constitution.request_override(override_request)

        assert result.approved is False
        assert "blocked" in result.reason.lower() or "cannot override" in result.reason.lower()

    def test_override_rate_limits(self):
        """Should enforce rate limits on overrides."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        # Request 9 overrides (limit is 8 per month)
        for i in range(9):
            override_request = {
                "type": "temporary",
                "rule_id": f"test_rule_{i}",
                "duration_days": 1,
                "reason": "Test"
            }
            result = constitution.request_override(override_request)

            if i < 8:
                assert result.approved is True
            else:
                assert result.approved is False
                assert "rate limit" in result.reason.lower()

    def test_contextual_override_vacation_mode(self):
        """Should support contextual overrides like vacation mode."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        context_request = {
            "type": "contextual",
            "context_name": "vacation_mode",
            "duration_days": 7,
            "suspended_rules": ["productivity/*", "learning/*"]
        }

        result = constitution.activate_context(context_request)

        assert result.activated is True
        assert len(result.suspended_rules) > 0


class TestConstitutionEvolution:
    """Tests for constitution learning and evolution."""

    def test_suggest_amendments_from_override_patterns(self):
        """Should suggest amendments based on frequent overrides."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        # Simulate multiple overrides of same rule
        for _ in range(5):
            constitution.request_override({
                "type": "temporary",
                "rule_id": "health/sleep_hours",
                "duration_days": 1,
                "reason": "Work schedule"
            })

        suggestions = constitution.suggest_amendments()

        assert len(suggestions) > 0
        # Should suggest adjusting sleep_hours minimum
        assert any("sleep_hours" in s.rule_id for s in suggestions)

    def test_amendment_requires_user_approval(self):
        """Should not auto-apply amendments without user approval."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        amendment = {
            "rule_id": "health/sleep_hours",
            "change": {"old_value": 7, "new_value": 6.5},
            "reason": "User consistently needs less sleep"
        }

        # Propose amendment
        result = constitution.propose_amendment(amendment)

        assert result.status == "pending_approval"
        assert result.reflection_period_hours == 24

        # Constitution should not be changed yet
        original_value = constitution.get_rule_value("health/sleep_hours")
        assert original_value == 7


class TestLifeDomains:
    """Tests for life domain tracking and validation."""

    def test_get_life_domains(self):
        """Should return all life domains from constitution."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()
        domains = constitution.get_life_domains()

        assert len(domains) > 0
        assert "health" in [d.id for d in domains]

    def test_check_minimum_standards(self):
        """Should validate data against minimum standards."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        user_data = {
            "health": {
                "sleep_hours": 5,  # Below minimum of 7
                "exercise_days_per_week": 4  # Above minimum of 3
            }
        }

        violations = constitution.check_minimum_standards(user_data)

        assert len(violations) > 0
        assert any(v.domain == "health" and "sleep" in v.metric for v in violations)

    def test_custom_domain_in_custom_constitution(self):
        """Should support custom domains in user constitutions."""
        from alter.core.constitution import Constitution

        custom_yaml = """
version: "1.0.0"
constitution_type: "custom"
core_principles:
  - id: "autonomy"
    rules: ["Rule 1"]
    weight: 10
  - id: "ethics"
    rules: ["Rule 1"]
    weight: 10
  - id: "transparency"
    rules: ["Rule 1"]
    weight: 10
life_domains:
  - id: "adventure"
    name: "Adventure & Exploration"
    metrics:
      - "New experiences per month"
    minimum_standards:
      new_experiences_per_month: 2
        """

        constitution = Constitution.from_yaml(custom_yaml)
        domains = constitution.get_life_domains()

        assert any(d.id == "adventure" for d in domains)


class TestInterventionTriggers:
    """Tests for intervention trigger system."""

    def test_check_immediate_intervention_triggers(self):
        """Should detect conditions requiring immediate intervention."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        user_state = {
            "health": {
                "sleep_hours_last_3_days": [4, 4, 4]  # Below 5 for 3 days
            }
        }

        interventions = constitution.check_intervention_triggers(
            user_state, trigger_type="immediate"
        )

        assert len(interventions) > 0
        assert interventions[0].urgency == "immediate"
        assert "sleep" in interventions[0].message.lower()

    def test_no_intervention_when_within_standards(self):
        """Should not trigger intervention when user is within standards."""
        from alter.core.constitution import Constitution

        constitution = Constitution.load()

        user_state = {
            "health": {
                "sleep_hours_last_3_days": [7, 8, 7.5]
            }
        }

        interventions = constitution.check_intervention_triggers(
            user_state, trigger_type="immediate"
        )

        assert len(interventions) == 0
