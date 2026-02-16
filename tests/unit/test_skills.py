"""
Tests for the Skills Layer — Phase C7.

Tests cover:
- Base: Skill interface, SkillInfo, SkillMetric, SkillExpectation
- Health: HealthSkill data collection, bootstrap expectations
- Calendar: CalendarSkill data collection, bootstrap expectations
- Journal: JournalSkill data collection, text entries, bootstrap expectations
- Registry: registration, collection, validation, expectations
- Bootstrap: world model expectation creation from skills
- Integration: skills → daily_data → observe → prediction errors
"""

import pytest
from typing import Any, Dict, List


# ─── Skill Base Tests ───


class TestSkillBase:
    """Tests for the Skill base class and data structures."""

    def test_skill_metric_creation(self):
        from alter.skills.base import SkillMetric
        m = SkillMetric(name="sleep_hours", domain="health",
                        description="Hours of sleep", unit="hours",
                        typical_range=(6.0, 9.0))
        assert m.name == "sleep_hours"
        assert m.typical_range == (6.0, 9.0)

    def test_skill_expectation_creation(self):
        from alter.skills.base import SkillExpectation
        e = SkillExpectation(
            domain="health", aspect="sleep",
            description="Sleeps 7-8 hours",
            data_field="sleep_hours",
            default_value=7.5, default_range=(7.0, 8.0),
        )
        assert e.initial_confidence == 0.1
        assert e.data_field == "sleep_hours"

    def test_skill_info_creation(self):
        from alter.skills.base import SkillInfo
        info = SkillInfo(name="test", description="Test skill",
                         domains=["test_domain"])
        assert info.name == "test"
        assert info.version == "1.0"

    def test_abstract_skill_cannot_instantiate(self):
        from alter.skills.base import Skill
        with pytest.raises(TypeError):
            Skill()


# ─── Health Skill Tests ───


class TestHealthSkill:
    """Tests for HealthSkill."""

    def _make_skill(self):
        from alter.skills.health import HealthSkill
        return HealthSkill()

    def test_info(self):
        skill = self._make_skill()
        info = skill.info()
        assert info.name == "health"
        assert info.domains == ["health"]
        assert len(info.metrics) == 5

    def test_name_property(self):
        skill = self._make_skill()
        assert skill.name == "health"

    def test_domains_property(self):
        skill = self._make_skill()
        assert skill.domains == ["health"]

    @pytest.mark.asyncio
    async def test_collect_with_kwargs(self):
        skill = self._make_skill()
        data = await skill.collect(sleep_hours=7, exercise_minutes=30)
        assert data == {"health": {"sleep_hours": 7.0, "exercise_minutes": 30.0}}

    @pytest.mark.asyncio
    async def test_collect_with_set_data(self):
        skill = self._make_skill()
        skill.set_data(sleep_hours=8, steps=10000)
        data = await skill.collect()
        assert data["health"]["sleep_hours"] == 8.0
        assert data["health"]["steps"] == 10000.0

    @pytest.mark.asyncio
    async def test_collect_kwargs_override_set_data(self):
        skill = self._make_skill()
        skill.set_data(sleep_hours=7)
        data = await skill.collect(sleep_hours=9)
        assert data["health"]["sleep_hours"] == 9.0

    @pytest.mark.asyncio
    async def test_collect_filters_unknown_fields(self):
        skill = self._make_skill()
        data = await skill.collect(sleep_hours=7, unknown_field=42)
        assert "unknown_field" not in data.get("health", {})

    @pytest.mark.asyncio
    async def test_collect_empty_returns_empty(self):
        skill = self._make_skill()
        data = await skill.collect()
        assert data == {}

    def test_bootstrap_expectations(self):
        skill = self._make_skill()
        exps = skill.bootstrap_expectations()
        assert len(exps) == 4
        domains = {e.domain for e in exps}
        assert domains == {"health"}
        fields = {e.data_field for e in exps}
        assert "sleep_hours" in fields
        assert "exercise_minutes" in fields

    @pytest.mark.asyncio
    async def test_validate_default(self):
        skill = self._make_skill()
        assert await skill.validate() is True


# ─── Calendar Skill Tests ───


class TestCalendarSkill:
    """Tests for CalendarSkill."""

    def _make_skill(self):
        from alter.skills.calendar import CalendarSkill
        return CalendarSkill()

    def test_info(self):
        skill = self._make_skill()
        info = skill.info()
        assert info.name == "calendar"
        assert info.domains == ["calendar"]
        assert len(info.metrics) == 4

    @pytest.mark.asyncio
    async def test_collect(self):
        skill = self._make_skill()
        data = await skill.collect(meetings=3, focus_hours=2.5)
        assert data == {"calendar": {"meetings": 3.0, "focus_hours": 2.5}}

    @pytest.mark.asyncio
    async def test_collect_empty(self):
        skill = self._make_skill()
        data = await skill.collect()
        assert data == {}

    def test_bootstrap_expectations(self):
        skill = self._make_skill()
        exps = skill.bootstrap_expectations()
        assert len(exps) == 3
        fields = {e.data_field for e in exps}
        assert "meetings" in fields
        assert "focus_hours" in fields


# ─── Journal Skill Tests ───


class TestJournalSkill:
    """Tests for JournalSkill."""

    def _make_skill(self):
        from alter.skills.journal import JournalSkill
        return JournalSkill()

    def test_info(self):
        skill = self._make_skill()
        info = skill.info()
        assert info.name == "journal"
        assert info.domains == ["emotions"]
        assert len(info.metrics) == 4

    @pytest.mark.asyncio
    async def test_collect_numeric(self):
        skill = self._make_skill()
        data = await skill.collect(mood=7, energy=6, stress=3)
        assert data["emotions"]["mood"] == 7.0
        assert data["emotions"]["energy"] == 6.0
        assert data["emotions"]["stress"] == 3.0

    @pytest.mark.asyncio
    async def test_collect_with_text_entry(self):
        skill = self._make_skill()
        data = await skill.collect(mood=7, entry="Feeling good today")
        assert data["emotions"]["mood"] == 7.0
        assert data["emotions"]["journal_entry"] == "Feeling good today"

    @pytest.mark.asyncio
    async def test_collect_text_only(self):
        skill = self._make_skill()
        data = await skill.collect(entry="Just a thought")
        assert data["emotions"]["journal_entry"] == "Just a thought"

    @pytest.mark.asyncio
    async def test_collect_empty(self):
        skill = self._make_skill()
        data = await skill.collect()
        assert data == {}

    def test_bootstrap_expectations(self):
        skill = self._make_skill()
        exps = skill.bootstrap_expectations()
        assert len(exps) == 3
        domains = {e.domain for e in exps}
        assert domains == {"emotions"}
        fields = {e.data_field for e in exps}
        assert "mood" in fields
        assert "stress" in fields


# ─── Registry Tests ───


class TestSkillRegistry:
    """Tests for SkillRegistry."""

    def _make_registry(self):
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        from alter.skills.calendar import CalendarSkill
        registry = SkillRegistry()
        registry.register(HealthSkill())
        registry.register(CalendarSkill())
        return registry

    def test_register(self):
        registry = self._make_registry()
        assert "health" in registry.skill_names
        assert "calendar" in registry.skill_names

    def test_list_skills(self):
        registry = self._make_registry()
        infos = registry.list_skills()
        assert len(infos) == 2
        names = {i.name for i in infos}
        assert names == {"health", "calendar"}

    def test_get_skill(self):
        registry = self._make_registry()
        skill = registry.get("health")
        assert skill is not None
        assert skill.name == "health"

    def test_get_nonexistent(self):
        registry = self._make_registry()
        assert registry.get("nonexistent") is None

    def test_unregister(self):
        registry = self._make_registry()
        removed = registry.unregister("health")
        assert removed is not None
        assert "health" not in registry.skill_names

    def test_unregister_nonexistent(self):
        registry = self._make_registry()
        removed = registry.unregister("nonexistent")
        assert removed is None

    def test_domains(self):
        registry = self._make_registry()
        domains = registry.domains
        assert "health" in domains
        assert "calendar" in domains

    def test_replace_on_register(self):
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        registry = SkillRegistry()
        s1 = HealthSkill()
        s2 = HealthSkill()
        registry.register(s1)
        registry.register(s2)
        assert len(registry.skill_names) == 1
        assert registry.get("health") is s2

    @pytest.mark.asyncio
    async def test_collect_all(self):
        from alter.skills.health import HealthSkill
        from alter.skills.calendar import CalendarSkill
        from alter.skills.registry import SkillRegistry
        registry = SkillRegistry()
        h = HealthSkill()
        h.set_data(sleep_hours=7)
        c = CalendarSkill()
        c.set_data(meetings=3)
        registry.register(h)
        registry.register(c)
        data = await registry.collect_all()
        assert data["health"]["sleep_hours"] == 7.0
        assert data["calendar"]["meetings"] == 3.0

    @pytest.mark.asyncio
    async def test_collect_all_handles_failure(self):
        """A failing skill should not prevent others from collecting."""
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        from alter.skills.base import Skill, SkillInfo

        class FailingSkill(Skill):
            def info(self):
                return SkillInfo(name="failing", description="Always fails", domains=["fail"])
            async def collect(self, **kwargs):
                raise RuntimeError("Boom")

        registry = SkillRegistry()
        h = HealthSkill()
        h.set_data(sleep_hours=7)
        registry.register(h)
        registry.register(FailingSkill())
        data = await registry.collect_all()
        assert data["health"]["sleep_hours"] == 7.0

    @pytest.mark.asyncio
    async def test_collect_skill_by_name(self):
        from alter.skills.health import HealthSkill
        from alter.skills.registry import SkillRegistry
        registry = SkillRegistry()
        h = HealthSkill()
        h.set_data(sleep_hours=8)
        registry.register(h)
        data = await registry.collect_skill("health")
        assert data["health"]["sleep_hours"] == 8.0

    @pytest.mark.asyncio
    async def test_collect_skill_not_found(self):
        from alter.skills.registry import SkillRegistry
        registry = SkillRegistry()
        with pytest.raises(KeyError):
            await registry.collect_skill("nonexistent")

    def test_get_all_expectations(self):
        registry = self._make_registry()
        exps = registry.get_all_expectations()
        assert len(exps) > 0
        domains = {e.domain for e in exps}
        assert "health" in domains
        assert "calendar" in domains

    @pytest.mark.asyncio
    async def test_validate_all(self):
        registry = self._make_registry()
        results = await registry.validate_all()
        assert results["health"] is True
        assert results["calendar"] is True


# ─── Bootstrap Tests ───


class TestBootstrap:
    """Tests for bootstrapping skill expectations into the world model."""

    def _make_world_model(self):
        from alter.consciousness.state import WorldModel
        return WorldModel()

    def _make_registry(self):
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        registry = SkillRegistry()
        registry.register(HealthSkill())
        return registry

    def test_bootstrap_creates_expectations(self):
        from alter.skills.bootstrap import bootstrap_skills
        wm = self._make_world_model()
        registry = self._make_registry()
        created = bootstrap_skills(registry, wm)
        assert len(created) == 4  # HealthSkill has 4 expectations
        # Check one was actually set
        exp = wm.get_expectation("health", "sleep")
        assert exp is not None
        assert exp.numeric_value == 7.5
        assert exp.data_field == "sleep_hours"

    def test_bootstrap_low_confidence(self):
        from alter.skills.bootstrap import bootstrap_skills
        wm = self._make_world_model()
        registry = self._make_registry()
        created = bootstrap_skills(registry, wm)
        for exp in created:
            assert exp.confidence == 0.1  # Low initial confidence

    def test_bootstrap_skips_existing(self):
        """Bootstrap should not overwrite existing expectations."""
        from alter.skills.bootstrap import bootstrap_skills
        from alter.consciousness.state import Expectation
        wm = self._make_world_model()
        # Pre-set an expectation with high confidence
        existing = Expectation(
            domain="health", aspect="sleep",
            description="Custom sleep expectation",
            numeric_value=9.0, confidence=0.9, data_points=100,
            data_field="sleep_hours",
        )
        wm.set_expectation(existing)
        registry = self._make_registry()
        created = bootstrap_skills(registry, wm)
        # sleep should have been skipped
        assert len(created) == 3
        # Existing expectation should be untouched
        exp = wm.get_expectation("health", "sleep")
        assert exp.numeric_value == 9.0
        assert exp.confidence == 0.9

    def test_bootstrap_idempotent(self):
        """Running bootstrap twice should not duplicate expectations."""
        from alter.skills.bootstrap import bootstrap_skills
        wm = self._make_world_model()
        registry = self._make_registry()
        first = bootstrap_skills(registry, wm)
        second = bootstrap_skills(registry, wm)
        assert len(first) == 4
        assert len(second) == 0  # All already exist

    def test_bootstrap_multiple_skills(self):
        from alter.skills.bootstrap import bootstrap_skills
        from alter.skills.calendar import CalendarSkill
        from alter.skills.journal import JournalSkill
        wm = self._make_world_model()
        registry = self._make_registry()
        registry.register(CalendarSkill())
        registry.register(JournalSkill())
        created = bootstrap_skills(registry, wm)
        # 4 health + 3 calendar + 3 journal = 10
        assert len(created) == 10
        domains = {e.domain for e in created}
        assert "health" in domains
        assert "calendar" in domains
        assert "emotions" in domains


# ─── Integration Tests ───


class TestSkillsIntegration:
    """Tests for the full skills → daily_data → observe → prediction error pipeline."""

    @pytest.mark.asyncio
    async def test_skill_data_produces_observations(self):
        """Skill data should flow through observe_daily_data() and produce prediction errors."""
        from alter.skills.health import HealthSkill
        from alter.skills.bootstrap import bootstrap_skills
        from alter.skills.registry import SkillRegistry
        from alter.consciousness.state import WorldModel
        from alter.consciousness.observe import observe_daily_data

        # Set up skill and world model
        registry = SkillRegistry()
        skill = HealthSkill()
        registry.register(skill)
        wm = WorldModel()
        created = bootstrap_skills(registry, wm)

        # Boost confidence so observations actually fire
        for exp in created:
            exp.confidence = 0.8
            exp.data_points = 30

        # Collect data with a significant deviation
        data = await skill.collect(sleep_hours=4, exercise_minutes=0)
        # data = {"health": {"sleep_hours": 4.0, "exercise_minutes": 0.0}}

        # Run observation
        observations = observe_daily_data(wm, data)
        assert len(observations) > 0

        # Check that sleep deviation was detected
        sleep_obs = [o for o in observations if o.aspect == "sleep"]
        assert len(sleep_obs) == 1
        assert sleep_obs[0].prediction_error > 0.3  # 4h vs 7.5h expected

    @pytest.mark.asyncio
    async def test_registry_collect_merges_domains(self):
        """collect_all() should merge data from multiple skills into one dict."""
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        from alter.skills.journal import JournalSkill

        registry = SkillRegistry()
        h = HealthSkill()
        h.set_data(sleep_hours=7)
        j = JournalSkill()
        j.set_data(mood=8)
        registry.register(h)
        registry.register(j)

        data = await registry.collect_all()
        assert "health" in data
        assert "emotions" in data
        assert data["health"]["sleep_hours"] == 7.0
        assert data["emotions"]["mood"] == 8.0

    @pytest.mark.asyncio
    async def test_engine_collect_skill_data(self):
        """Engine.collect_skill_data() should update user_model.daily_data."""
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.state import ConsciousnessState
        from alter.core.user_model import UserModel
        from datetime import datetime

        registry = SkillRegistry()
        h = HealthSkill()
        h.set_data(sleep_hours=7.5, steps=9000)
        registry.register(h)

        user = UserModel.create_new("skill_test")
        state = ConsciousnessState(user_id="skill_test")
        engine = ConsciousnessEngine(
            consciousness_state=state,
            user_model=user,
            auto_save=False,
            skill_registry=registry,
        )

        await engine.collect_skill_data()

        today = datetime.now().date().isoformat()
        daily = user.get_daily_data(today)
        assert daily["health"]["sleep_hours"] == 7.5
        assert daily["health"]["steps"] == 9000.0

    @pytest.mark.asyncio
    async def test_full_pipeline_skill_to_observation(self):
        """Full pipeline: skill → collect → daily_data → observe → observations."""
        from alter.skills.registry import SkillRegistry
        from alter.skills.health import HealthSkill
        from alter.skills.bootstrap import bootstrap_skills
        from alter.consciousness.engine import ConsciousnessEngine
        from alter.consciousness.state import ConsciousnessState
        from alter.core.user_model import UserModel
        from datetime import datetime

        # Set up
        registry = SkillRegistry()
        h = HealthSkill()
        h.set_data(sleep_hours=3)  # Very low — should trigger prediction error
        registry.register(h)

        user = UserModel.create_new("pipeline_test")
        state = ConsciousnessState(user_id="pipeline_test")

        # Bootstrap and boost confidence
        created = bootstrap_skills(registry, state.world_model)
        for exp in created:
            exp.confidence = 0.8
            exp.data_points = 30

        engine = ConsciousnessEngine(
            consciousness_state=state,
            user_model=user,
            auto_save=False,
            skill_registry=registry,
        )

        # Collect skill data → daily_data
        await engine.collect_skill_data()

        # Observe → prediction errors
        observations = engine.hourly_observe()
        sleep_obs = [o for o in observations if o.aspect == "sleep"]
        assert len(sleep_obs) == 1
        # 3h vs 7.5h expected → error = 0.6 * 0.8 = 0.48 (just below elevated threshold)
        assert sleep_obs[0].prediction_error > 0.3
        assert sleep_obs[0].severity != "critical"  # not that extreme at 0.8 confidence
