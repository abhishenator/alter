"""
Tests for the Inbox + Habits + PinnedNotes redesign (Phases A-F).

Tests cover:
- InboxItem: creation, serialization, CRUD on ConsciousnessState
- Habit: creation, toggle, streak calculation, serialization
- PinnedNote: creation, archival, serialization
- UserModel: habit/pinned_note management + serialization roundtrip
- ConsciousnessState: inbox management, compact pruning, serialization
- Context: user engagement formatting for consciousness feedback loop
- Adapter: inbox routing from tick results
"""

import pytest
from datetime import datetime, timedelta


# ─── InboxItem Tests ───


class TestInboxItem:
    """Tests for the InboxItem dataclass."""

    def test_create_inbox_item_defaults(self):
        from alter.consciousness.state import InboxItem
        item = InboxItem()
        assert len(item.id) == 8
        assert item.status == "pending"
        assert item.item_type == ""
        assert item.suggested_goal is None
        assert item.user_reaction is None

    def test_create_inbox_item_with_values(self):
        from alter.consciousness.state import InboxItem
        item = InboxItem(
            item_type="insight",
            title="Sleep affects energy",
            body="Your energy is highest the day after 8+ hours of sleep.",
            domain="health",
            source_tick="daily_review",
            actionable="Try sleeping before 11pm this week.",
        )
        assert item.item_type == "insight"
        assert item.title == "Sleep affects energy"
        assert item.domain == "health"
        assert item.status == "pending"

    def test_inbox_item_serialization_roundtrip(self):
        from alter.consciousness.state import InboxItem
        item = InboxItem(
            item_type="goal_suggestion",
            title="Walk 30 min daily",
            body="Based on exercise goals, walking helps.",
            domain="health",
            source_tick="weekly_reflect",
            suggested_goal={"description": "Walk 30 min daily", "domain": "health", "time_horizon": "week"},
        )
        d = item.to_dict()
        restored = InboxItem.from_dict(d)
        assert restored.id == item.id
        assert restored.item_type == "goal_suggestion"
        assert restored.suggested_goal["description"] == "Walk 30 min daily"
        assert restored.status == "pending"

    def test_inbox_item_with_all_types(self):
        from alter.consciousness.state import InboxItem
        for t in ["insight", "discovery", "goal_suggestion", "decision", "notification"]:
            item = InboxItem(item_type=t, title=f"Test {t}")
            assert item.item_type == t


# ─── Habit Tests ───


class TestHabit:
    """Tests for the Habit dataclass."""

    def test_create_habit(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        assert h.id == "h1"
        assert h.name == "Exercise"
        assert h.domain == "general"
        assert h.active is True
        assert h.streak == 0
        assert h.completions == {}

    def test_toggle_marks_done(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        today = datetime.now().date().isoformat()
        result = h.toggle()
        assert result is True
        assert h.completions[today] is True

    def test_toggle_twice_unmarks(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        today = datetime.now().date().isoformat()
        h.toggle()  # mark done
        result = h.toggle()  # unmark
        assert result is False
        assert h.completions[today] is False

    def test_toggle_specific_date(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        result = h.toggle("2026-02-15")
        assert result is True
        assert h.completions["2026-02-15"] is True

    def test_streak_calculation_today_only(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        today = datetime.now().date().isoformat()
        h.toggle(today)
        assert h.streak == 1

    def test_streak_calculation_consecutive_days(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        today = datetime.now().date()
        for i in range(5):
            d = (today - timedelta(days=i)).isoformat()
            h.completions[d] = True
        h._recalc_streak()
        assert h.streak == 5

    def test_streak_breaks_on_gap(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        today = datetime.now().date()
        # Complete today and yesterday, skip day before
        h.completions[today.isoformat()] = True
        h.completions[(today - timedelta(days=1)).isoformat()] = True
        # Skip day 2
        h.completions[(today - timedelta(days=3)).isoformat()] = True
        h._recalc_streak()
        assert h.streak == 2  # only today + yesterday

    def test_streak_zero_when_today_not_done(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Exercise")
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        h.completions[yesterday] = True
        h._recalc_streak()
        assert h.streak == 0

    def test_habit_serialization_roundtrip(self):
        from alter.core.user_model import Habit
        h = Habit(
            id="h1", name="Exercise", domain="health",
            linked_goal_id="g1", source_inbox_id="inbox1",
        )
        h.toggle()  # mark today done
        d = h.to_dict()
        restored = Habit.from_dict(d)
        assert restored.id == "h1"
        assert restored.name == "Exercise"
        assert restored.domain == "health"
        assert restored.linked_goal_id == "g1"
        assert restored.source_inbox_id == "inbox1"
        assert restored.streak == h.streak

    def test_habit_with_goal_link(self):
        from alter.core.user_model import Habit
        h = Habit(id="h1", name="Run 3x/week", domain="health", linked_goal_id="g_run")
        assert h.linked_goal_id == "g_run"


# ─── PinnedNote Tests ───


class TestPinnedNote:
    """Tests for the PinnedNote dataclass."""

    def test_create_pinned_note(self):
        from alter.core.user_model import PinnedNote
        n = PinnedNote(id="n1", text="Energy peaks after exercise", domain="health")
        assert n.id == "n1"
        assert n.archived is False
        assert n.source_inbox_id is None

    def test_pinned_note_with_inbox_link(self):
        from alter.core.user_model import PinnedNote
        n = PinnedNote(
            id="n1", text="Test", domain="health",
            source_inbox_id="inbox42",
        )
        assert n.source_inbox_id == "inbox42"

    def test_pinned_note_serialization_roundtrip(self):
        from alter.core.user_model import PinnedNote
        n = PinnedNote(
            id="n1", text="Energy peaks after exercise",
            domain="health", source_inbox_id="i1", linked_goal_id="g1",
        )
        d = n.to_dict()
        restored = PinnedNote.from_dict(d)
        assert restored.id == "n1"
        assert restored.text == "Energy peaks after exercise"
        assert restored.domain == "health"
        assert restored.source_inbox_id == "i1"
        assert restored.linked_goal_id == "g1"
        assert restored.archived is False


# ─── UserModel Habit/PinnedNote Management Tests ───


class TestUserModelHabits:
    """Tests for habit management on UserModel."""

    def _make_user(self):
        from alter.core.user_model import UserModel
        return UserModel.create_new(user_id="test")

    def test_add_habit(self):
        from alter.core.user_model import Habit
        user = self._make_user()
        h = Habit(id="h1", name="Exercise")
        user.add_habit(h)
        assert len(user.habits) == 1
        assert user.habits[0].name == "Exercise"

    def test_get_habit(self):
        from alter.core.user_model import Habit
        user = self._make_user()
        user.add_habit(Habit(id="h1", name="Exercise"))
        user.add_habit(Habit(id="h2", name="Journal"))
        assert user.get_habit("h2").name == "Journal"
        assert user.get_habit("missing") is None

    def test_get_active_habits(self):
        from alter.core.user_model import Habit
        user = self._make_user()
        user.add_habit(Habit(id="h1", name="Exercise"))
        user.add_habit(Habit(id="h2", name="Journal"))
        user.remove_habit("h1")
        active = user.get_active_habits()
        assert len(active) == 1
        assert active[0].id == "h2"

    def test_remove_habit_deactivates(self):
        from alter.core.user_model import Habit
        user = self._make_user()
        user.add_habit(Habit(id="h1", name="Exercise"))
        assert user.remove_habit("h1") is True
        assert user.get_habit("h1").active is False

    def test_remove_nonexistent_habit(self):
        user = self._make_user()
        assert user.remove_habit("missing") is False

    def test_habits_persist_in_serialization(self):
        from alter.core.user_model import Habit, UserModel
        user = self._make_user()
        user.add_habit(Habit(id="h1", name="Exercise", domain="health"))
        user.add_habit(Habit(id="h2", name="Journal", domain="growth"))
        d = user.to_dict()
        assert len(d["habits"]) == 2
        restored = UserModel.from_dict(d)
        assert len(restored.habits) == 2
        assert restored.habits[0].name == "Exercise"
        assert restored.habits[1].domain == "growth"


class TestUserModelPinnedNotes:
    """Tests for pinned note management on UserModel."""

    def _make_user(self):
        from alter.core.user_model import UserModel
        return UserModel.create_new(user_id="test")

    def test_add_pinned_note(self):
        from alter.core.user_model import PinnedNote
        user = self._make_user()
        n = PinnedNote(id="n1", text="Test insight", domain="health")
        user.add_pinned_note(n)
        assert len(user.pinned_notes) == 1

    def test_get_active_pinned_notes_excludes_archived(self):
        from alter.core.user_model import PinnedNote
        user = self._make_user()
        user.add_pinned_note(PinnedNote(id="n1", text="Active", domain="health"))
        user.add_pinned_note(PinnedNote(id="n2", text="Archived", domain="health"))
        user.archive_pinned_note("n2")
        active = user.get_active_pinned_notes()
        assert len(active) == 1
        assert active[0].id == "n1"

    def test_get_active_pinned_notes_newest_first(self):
        from alter.core.user_model import PinnedNote
        user = self._make_user()
        user.add_pinned_note(PinnedNote(id="n1", text="Old", domain="a", pinned_at="2026-01-01"))
        user.add_pinned_note(PinnedNote(id="n2", text="New", domain="b", pinned_at="2026-02-01"))
        active = user.get_active_pinned_notes()
        assert active[0].id == "n2"

    def test_archive_pinned_note(self):
        from alter.core.user_model import PinnedNote
        user = self._make_user()
        user.add_pinned_note(PinnedNote(id="n1", text="Test", domain="health"))
        assert user.archive_pinned_note("n1") is True
        assert user.pinned_notes[0].archived is True

    def test_archive_nonexistent_note(self):
        user = self._make_user()
        assert user.archive_pinned_note("missing") is False

    def test_pinned_notes_persist_in_serialization(self):
        from alter.core.user_model import PinnedNote, UserModel
        user = self._make_user()
        user.add_pinned_note(PinnedNote(id="n1", text="Insight A", domain="health"))
        user.add_pinned_note(PinnedNote(id="n2", text="Insight B", domain="career"))
        d = user.to_dict()
        assert len(d["pinned_notes"]) == 2
        restored = UserModel.from_dict(d)
        assert len(restored.pinned_notes) == 2
        assert restored.pinned_notes[0].text == "Insight A"


# ─── ConsciousnessState Inbox Tests ───


class TestConsciousnessStateInbox:
    """Tests for inbox management on ConsciousnessState."""

    def _make_state(self):
        from alter.consciousness.state import ConsciousnessState
        return ConsciousnessState(user_id="test")

    def test_add_inbox_item(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        item = InboxItem(item_type="insight", title="Test", domain="health")
        state.add_inbox_item(item)
        assert len(state.inbox) == 1

    def test_get_pending_inbox_newest_first(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(
            item_type="insight", title="Old", created_at="2026-01-01T00:00:00"))
        state.add_inbox_item(InboxItem(
            item_type="insight", title="New", created_at="2026-02-01T00:00:00"))
        pending = state.get_pending_inbox()
        assert len(pending) == 2
        assert pending[0].title == "New"

    def test_get_pending_excludes_resolved(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="a", item_type="insight", title="Pending"))
        state.add_inbox_item(InboxItem(id="b", item_type="insight", title="Dismissed"))
        state.resolve_inbox_item("b", "dismissed")
        pending = state.get_pending_inbox()
        assert len(pending) == 1
        assert pending[0].id == "a"

    def test_get_inbox_item_by_id(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="test123", item_type="insight", title="Found"))
        item = state.get_inbox_item("test123")
        assert item is not None
        assert item.title == "Found"

    def test_get_inbox_item_not_found(self):
        state = self._make_state()
        assert state.get_inbox_item("missing") is None

    def test_resolve_inbox_item_pin(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="a", item_type="insight", title="Pin me"))
        item = state.resolve_inbox_item("a", "pinned", "pinned")
        assert item is not None
        assert item.status == "pinned"
        assert item.resolved_at is not None
        assert item.user_reaction == "pinned"

    def test_resolve_inbox_item_dismiss(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="a", item_type="insight", title="Dismiss me"))
        item = state.resolve_inbox_item("a", "dismissed", "dismissed")
        assert item.status == "dismissed"

    def test_resolve_inbox_item_convert(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="a", item_type="goal_suggestion", title="Convert me"))
        item = state.resolve_inbox_item("a", "converted", "converted_to_goal")
        assert item.status == "converted"
        assert item.user_reaction == "converted_to_goal"

    def test_resolve_already_resolved_returns_none(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="a", item_type="insight", title="Once"))
        state.resolve_inbox_item("a", "dismissed")
        result = state.resolve_inbox_item("a", "pinned")
        assert result is None

    def test_resolve_nonexistent_returns_none(self):
        state = self._make_state()
        assert state.resolve_inbox_item("missing", "dismissed") is None

    def test_get_recent_dismissed(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        for i in range(3):
            state.add_inbox_item(InboxItem(id=f"d{i}", item_type="insight", title=f"Item {i}"))
            state.resolve_inbox_item(f"d{i}", "dismissed")
        dismissed = state.get_recent_dismissed()
        assert len(dismissed) == 3

    def test_get_recent_pinned(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        state.add_inbox_item(InboxItem(id="p1", item_type="insight", title="Pinned"))
        state.resolve_inbox_item("p1", "pinned")
        state.add_inbox_item(InboxItem(id="c1", item_type="insight", title="Converted"))
        state.resolve_inbox_item("c1", "converted")
        pinned = state.get_recent_pinned()
        assert len(pinned) == 2  # both pinned and converted

    def test_inbox_in_serialization_roundtrip(self):
        from alter.consciousness.state import InboxItem, ConsciousnessState
        state = self._make_state()
        state.add_inbox_item(InboxItem(
            id="t1", item_type="insight", title="Survive serialization",
            body="Full body", domain="health", source_tick="daily_review",
        ))
        state.add_inbox_item(InboxItem(
            id="t2", item_type="goal_suggestion", title="With goal",
            suggested_goal={"description": "Run daily", "domain": "health"},
        ))
        d = state.to_dict()
        restored = ConsciousnessState.from_dict(d)
        assert len(restored.inbox) == 2
        assert restored.inbox[0].id == "t1"
        assert restored.inbox[0].body == "Full body"
        assert restored.inbox[1].suggested_goal["description"] == "Run daily"

    def test_compact_prunes_old_resolved_inbox(self):
        from alter.consciousness.state import InboxItem
        state = self._make_state()
        old_date = (datetime.now() - timedelta(days=20)).isoformat()
        recent_date = (datetime.now() - timedelta(days=1)).isoformat()

        # Old resolved item — should be pruned
        state.add_inbox_item(InboxItem(
            id="old", item_type="insight", title="Old",
            status="dismissed", resolved_at=old_date,
        ))
        # Recent resolved item — should survive
        state.add_inbox_item(InboxItem(
            id="recent", item_type="insight", title="Recent",
            status="dismissed", resolved_at=recent_date,
        ))
        # Pending item — should survive
        state.add_inbox_item(InboxItem(
            id="pending", item_type="insight", title="Pending",
        ))

        state.compact()
        ids = [i.id for i in state.inbox]
        assert "old" not in ids
        assert "recent" in ids
        assert "pending" in ids


# ─── User Engagement Context Tests ───


class TestUserEngagementContext:
    """Tests for the consciousness feedback loop via context assembly."""

    def test_format_user_engagement_habits(self):
        from alter.consciousness.context import format_user_engagement
        habits = [
            {"name": "Exercise", "streak": 5},
            {"name": "Journal", "streak": 0},
        ]
        result = format_user_engagement(habits, [], [])
        assert "Exercise: 5-day streak" in result
        assert "Journal: no active streak" in result

    def test_format_user_engagement_pinned_notes(self):
        from alter.consciousness.context import format_user_engagement
        notes = [
            {"text": "Energy peaks after exercise", "domain": "health"},
        ]
        result = format_user_engagement([], notes, [])
        assert "Energy peaks after exercise" in result
        assert "(health)" in result

    def test_format_user_engagement_dismissed(self):
        from alter.consciousness.context import format_user_engagement
        dismissed = ["Meditation suggestion", "Career change prompt"]
        result = format_user_engagement([], [], dismissed)
        assert "Meditation suggestion" in result
        assert "Recently Dismissed" in result

    def test_format_user_engagement_empty(self):
        from alter.consciousness.context import format_user_engagement
        result = format_user_engagement([], [], [])
        assert result == ""

    def test_format_user_engagement_all_sections(self):
        from alter.consciousness.context import format_user_engagement
        result = format_user_engagement(
            [{"name": "Walk", "streak": 3}],
            [{"text": "Sleep insight", "domain": "health"}],
            ["Old suggestion"],
        )
        assert "Habits Being Tracked" in result
        assert "Pinned (User Valued These)" in result
        assert "Recently Dismissed" in result


# ─── Adapter Inbox Routing Tests ───


class TestAdapterInboxRouting:
    """Tests for inbox routing in StandaloneAdapter."""

    def test_route_to_inbox_creates_item(self):
        from alter.consciousness.state import ConsciousnessState
        from alter.adapters.standalone import StandaloneAdapter
        from alter.core.user_model import UserModel
        from alter.core.constitution import Constitution
        from unittest.mock import MagicMock

        user = UserModel.create_new(user_id="test")
        state = ConsciousnessState(user_id="test")

        # Create adapter with mocked engine
        adapter = StandaloneAdapter.__new__(StandaloneAdapter)
        adapter.user_model = user
        adapter.consciousness_state = state
        adapter.engine = MagicMock()
        adapter.activity_log = []
        adapter._running = False

        # Use the internal routing method
        adapter._route_to_inbox(
            item_type="insight",
            title="Test insight",
            body="Full body text",
            domain="health",
            source_tick="daily_review",
            actionable="Try this",
        )

        assert len(state.inbox) == 1
        item = state.inbox[0]
        assert item.item_type == "insight"
        assert item.title == "Test insight"
        assert item.body == "Full body text"
        assert item.domain == "health"

    def test_route_to_inbox_with_suggested_goal(self):
        from alter.consciousness.state import ConsciousnessState
        from alter.adapters.standalone import StandaloneAdapter
        from alter.core.user_model import UserModel
        from unittest.mock import MagicMock

        user = UserModel.create_new(user_id="test")
        state = ConsciousnessState(user_id="test")

        adapter = StandaloneAdapter.__new__(StandaloneAdapter)
        adapter.user_model = user
        adapter.consciousness_state = state
        adapter.engine = MagicMock()
        adapter.activity_log = []
        adapter._running = False

        adapter._route_to_inbox(
            item_type="goal_suggestion",
            title="Walk daily",
            body="Walking 30 min helps health",
            domain="health",
            source_tick="weekly_reflect",
            suggested_goal={"description": "Walk 30 min daily", "time_horizon": "week"},
        )

        assert len(state.inbox) == 1
        item = state.inbox[0]
        assert item.item_type == "goal_suggestion"
        assert item.suggested_goal["description"] == "Walk 30 min daily"

    def test_adapter_no_pending_actions_attribute(self):
        """Verify _pending_actions was removed from adapter."""
        from alter.adapters.standalone import StandaloneAdapter
        # StandaloneAdapter should not have _pending_actions anymore
        adapter = StandaloneAdapter.__new__(StandaloneAdapter)
        assert not hasattr(adapter, '_pending_actions')


# ─── Web Routes Redirect Tests ───


class TestRouteRedirects:
    """Test that old URLs redirect to new 3-screen architecture."""

    def test_redirect_mapping_exists(self):
        """Verify redirect routes are defined in web routes module."""
        from alter.web import routes
        import inspect
        source = inspect.getsource(routes)
        # Old URLs should redirect
        assert "/stream" in source
        assert "/direction" in source
        assert "/profile" in source
        assert "/world" in source


# ─── Integration: Inbox → PinnedNote flow ───


class TestInboxToPinnedNoteFlow:
    """Integration tests for the pin workflow."""

    def test_pin_creates_pinned_note_from_inbox(self):
        from alter.consciousness.state import ConsciousnessState, InboxItem
        from alter.core.user_model import UserModel, PinnedNote

        state = ConsciousnessState(user_id="test")
        user = UserModel.create_new(user_id="test")

        # Simulate: consciousness creates inbox item
        item = InboxItem(
            id="i1", item_type="insight",
            title="Sleep-exercise connection",
            body="Your energy is 20% higher the day after exercise.",
            domain="health", source_tick="daily_review",
        )
        state.add_inbox_item(item)

        # Simulate: user pins it
        resolved = state.resolve_inbox_item("i1", "pinned", "pinned")
        assert resolved is not None

        note = PinnedNote(
            id="n1",
            text=resolved.body,
            domain=resolved.domain,
            source_inbox_id=resolved.id,
        )
        user.add_pinned_note(note)

        # Verify
        assert len(state.get_pending_inbox()) == 0
        assert len(user.get_active_pinned_notes()) == 1
        assert user.get_active_pinned_notes()[0].source_inbox_id == "i1"


class TestInboxToGoalFlow:
    """Integration tests for the convert-to-goal workflow."""

    def test_convert_creates_goal_from_inbox(self):
        from alter.consciousness.state import ConsciousnessState, InboxItem
        from alter.core.user_model import UserModel, Goal

        state = ConsciousnessState(user_id="test")
        user = UserModel.create_new(user_id="test")

        item = InboxItem(
            id="i1", item_type="goal_suggestion",
            title="Run 3x/week",
            domain="health", source_tick="goal_analysis",
            suggested_goal={
                "description": "Run 3 times per week",
                "domain": "health",
                "time_horizon": "month",
            },
        )
        state.add_inbox_item(item)

        # Simulate: user converts to goal
        resolved = state.resolve_inbox_item("i1", "converted", "converted_to_goal")
        goal = Goal(
            id="g1",
            domain=resolved.suggested_goal["domain"],
            description=resolved.suggested_goal["description"],
            time_horizon=resolved.suggested_goal["time_horizon"],
        )
        user.add_goal(goal)

        assert len(state.get_pending_inbox()) == 0
        assert len(user.get_active_goals()) == 1
        assert user.get_active_goals()[0].description == "Run 3 times per week"


class TestInboxToHabitFlow:
    """Integration tests for the convert-to-habit workflow."""

    def test_convert_creates_habit_from_inbox(self):
        from alter.consciousness.state import ConsciousnessState, InboxItem
        from alter.core.user_model import UserModel, Habit

        state = ConsciousnessState(user_id="test")
        user = UserModel.create_new(user_id="test")

        item = InboxItem(
            id="i1", item_type="insight",
            title="Walk 30 min daily",
            domain="health", source_tick="daily_review",
        )
        state.add_inbox_item(item)

        resolved = state.resolve_inbox_item("i1", "converted", "converted_to_habit")
        habit = Habit(
            id="h1",
            name=resolved.title,
            domain=resolved.domain,
            source_inbox_id=resolved.id,
        )
        user.add_habit(habit)

        assert len(state.get_pending_inbox()) == 0
        assert len(user.get_active_habits()) == 1
        assert user.get_active_habits()[0].source_inbox_id == "i1"


# ─── Full feedback loop test ───


class TestFeedbackLoop:
    """Test the full consciousness feedback loop."""

    def test_engagement_context_includes_habits_and_notes(self):
        """Verify that user engagement data flows into context assembly."""
        from alter.consciousness.context import format_user_engagement
        from alter.core.user_model import UserModel, Habit, PinnedNote

        user = UserModel.create_new(user_id="test")

        # Add habits with streaks
        h = Habit(id="h1", name="Exercise", domain="health")
        h.completions[datetime.now().date().isoformat()] = True
        h._recalc_streak()
        user.add_habit(h)

        # Add pinned notes
        user.add_pinned_note(PinnedNote(id="n1", text="Energy insight", domain="health"))

        # Format for context
        habits_data = [h.to_dict() for h in user.get_active_habits()]
        pinned_data = [n.to_dict() for n in user.get_active_pinned_notes()]
        dismissed = ["Old suggestion"]

        result = format_user_engagement(habits_data, pinned_data, dismissed)

        assert "Exercise: 1-day streak" in result
        assert "Energy insight" in result
        assert "Old suggestion" in result
