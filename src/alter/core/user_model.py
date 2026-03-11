"""
User Model - Identity, goals, personality, and life data tracking.

Manages the user's:
- Life purpose and its evolution
- Goal hierarchy (life → 5yr → 1yr → quarter → month → week → day)
- Personality traits and preferences
- Daily life data and patterns
- Strengths and growth areas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class Habit:
    """A trackable daily habit, optionally linked to a goal or inbox item."""
    id: str
    name: str
    domain: str = "general"
    linked_goal_id: Optional[str] = None
    source_inbox_id: Optional[str] = None
    completions: Dict[str, bool] = field(default_factory=dict)  # date → done
    streak: int = 0
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def toggle(self, date_str: Optional[str] = None) -> bool:
        """Toggle completion for a date. Returns new done state."""
        date_str = date_str or datetime.now().date().isoformat()
        done = not self.completions.get(date_str, False)
        self.completions[date_str] = done
        self._recalc_streak()
        return done

    def _recalc_streak(self) -> None:
        """Recalculate streak from completions."""
        today = datetime.now().date()
        streak = 0
        d = today
        while True:
            if self.completions.get(d.isoformat(), False):
                streak += 1
                d -= timedelta(days=1)
            else:
                break
        self.streak = streak

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "domain": self.domain,
            "linked_goal_id": self.linked_goal_id,
            "source_inbox_id": self.source_inbox_id,
            "completions": self.completions, "streak": self.streak,
            "active": self.active, "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Habit:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PinnedNote:
    """A pinned insight or note, optionally linked to a goal or inbox item."""
    id: str
    text: str
    domain: str = ""
    source_inbox_id: Optional[str] = None
    linked_goal_id: Optional[str] = None
    pinned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "text": self.text, "domain": self.domain,
            "source_inbox_id": self.source_inbox_id,
            "linked_goal_id": self.linked_goal_id,
            "pinned_at": self.pinned_at, "archived": self.archived,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PinnedNote:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PurposeHistory:
    """Record of purpose statement at a point in time."""
    statement: str
    set_at: datetime
    notes: str = ""


@dataclass
class Goal:
    """A goal in the user's goal hierarchy."""
    id: str
    domain: str  # health, wealth, relationships, emotions, growth
    description: str
    time_horizon: str  # life, 5_year, 1_year, quarter, month, week, day
    parent_goal_id: Optional[str] = None
    status: str = "active"  # active, completed, abandoned, paused
    outcome: Optional[str] = None  # success, partial, failure
    completion_notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    """An identified pattern in user behavior."""
    pattern_id: str
    description: str
    confidence: float  # 0-1
    evidence: List[str]
    detected_at: datetime = field(default_factory=datetime.now)


class UserModel:
    """
    Comprehensive user model tracking identity, goals, and life data.

    This is the core representation of the user that the meta-loop
    uses to understand who they are and what they're working toward.
    """

    def __init__(
        self,
        user_id: str,
        purpose_statement: Optional[str] = None,
        purpose_history: Optional[List[PurposeHistory]] = None,
        goals: Optional[List[Goal]] = None,
        habits: Optional[List[Habit]] = None,
        pinned_notes: Optional[List[PinnedNote]] = None,
        personality_traits: Optional[Dict[str, int]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        strengths: Optional[List[str]] = None,
        growth_areas: Optional[List[str]] = None,
        daily_data: Optional[Dict[str, Dict[str, Any]]] = None,
        created_at: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.purpose_statement = purpose_statement
        self.purpose_history = purpose_history or []
        self.goals = goals or []
        self.habits: List[Habit] = habits or []
        self.pinned_notes: List[PinnedNote] = pinned_notes or []
        self.personality_traits = personality_traits or {}
        self.preferences = preferences or {}
        self.strengths = strengths or []
        self.growth_areas = growth_areas or []
        self.daily_data = daily_data or {}  # date_str -> {domain -> metrics}
        self.created_at = created_at or datetime.now()

    @classmethod
    def create_new(cls, user_id: str) -> UserModel:
        """Create a new user model with default values."""
        return cls(user_id=user_id)

    # Purpose Management

    def set_purpose(self, purpose: str, notes: str = "") -> None:
        """Set or update life purpose statement."""
        # Set new purpose and add to history
        self.purpose_statement = purpose
        self.purpose_history.append(PurposeHistory(
            statement=purpose,
            set_at=datetime.now(),
            notes=notes
        ))

    # Goal Management

    def add_goal(self, goal: Goal) -> None:
        """Add a goal to the user's goal hierarchy."""
        self.goals.append(goal)

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal by ID."""
        for goal in self.goals:
            if goal.id == goal_id:
                return goal
        return None

    def get_goals_by_time_horizon(self, time_horizon: str) -> List[Goal]:
        """Get all goals for a specific time horizon."""
        return [g for g in self.goals if g.time_horizon == time_horizon]

    def get_goals_by_domain(self, domain: str) -> List[Goal]:
        """Get all goals for a specific life domain."""
        return [g for g in self.goals if g.domain == domain]

    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return [g for g in self.goals if g.status == "active"]

    def complete_goal(
        self,
        goal_id: str,
        outcome: str = "success",
        notes: str = ""
    ) -> None:
        """Mark a goal as completed with outcome."""
        goal = self.get_goal(goal_id)
        if goal:
            goal.status = "completed"
            goal.outcome = outcome
            goal.completion_notes = notes
            goal.completed_at = datetime.now()

    def update_goal(self, goal_id: str, **kwargs: Any) -> Optional[Goal]:
        """Update fields on an existing goal. Returns updated Goal or None."""
        goal = self.get_goal(goal_id)
        if not goal:
            return None
        for field in ("description", "domain", "time_horizon", "parent_goal_id", "status"):
            if field in kwargs:
                setattr(goal, field, kwargs[field])
        return goal

    def remove_goal(self, goal_id: str) -> bool:
        """Remove a goal entirely. Returns True if found and removed."""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        self.goals.remove(goal)
        return True

    def abandon_goal(self, goal_id: str, reason: str = "") -> None:
        """Mark a goal as abandoned."""
        goal = self.get_goal(goal_id)
        if goal:
            goal.status = "abandoned"
            goal.completion_notes = reason
            goal.completed_at = datetime.now()

    # Habit Management

    def add_habit(self, habit: Habit) -> None:
        """Add a habit."""
        self.habits.append(habit)

    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """Get a habit by ID."""
        for h in self.habits:
            if h.id == habit_id:
                return h
        return None

    def get_active_habits(self) -> List[Habit]:
        """Get all active habits."""
        return [h for h in self.habits if h.active]

    def remove_habit(self, habit_id: str) -> bool:
        """Deactivate a habit. Returns True if found."""
        h = self.get_habit(habit_id)
        if h:
            h.active = False
            return True
        return False

    # Pinned Notes Management

    def add_pinned_note(self, note: PinnedNote) -> None:
        """Add a pinned note."""
        self.pinned_notes.append(note)

    def get_active_pinned_notes(self) -> List[PinnedNote]:
        """Get non-archived pinned notes, newest first."""
        return sorted(
            [n for n in self.pinned_notes if not n.archived],
            key=lambda n: n.pinned_at,
            reverse=True,
        )

    def archive_pinned_note(self, note_id: str) -> bool:
        """Archive a pinned note. Returns True if found."""
        for n in self.pinned_notes:
            if n.id == note_id:
                n.archived = True
                return True
        return False

    # Personality & Preferences

    def set_personality_traits(self, traits: Dict[str, int]) -> None:
        """Set personality traits (e.g., Big Five scores)."""
        self.personality_traits.update(traits)

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        self.preferences[key] = value

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.preferences.get(key, default)

    def add_strength(self, strength: str) -> None:
        """Add an identified strength."""
        if strength not in self.strengths:
            self.strengths.append(strength)

    def add_growth_area(self, growth_area: str) -> None:
        """Add an identified growth area."""
        if growth_area not in self.growth_areas:
            self.growth_areas.append(growth_area)

    # Life Data Tracking

    def record_daily_data(self, data: Dict[str, Any]) -> None:
        """
        Record daily metrics across life domains.

        Expected format:
        {
            "date": "2026-02-10",
            "health": {"sleep_hours": 7.5, "exercise_minutes": 45, ...},
            "emotions": {"mood": 7, "stress": 4},
            ...
        }
        """
        date_str = data.get("date")
        if not date_str:
            date_str = datetime.now().date().isoformat()

        # Store all domain data for this date
        self.daily_data[date_str] = {
            k: v for k, v in data.items() if k != "date"
        }

    def get_daily_data(self, date_str: str) -> Dict[str, Any]:
        """Get all daily data for a specific date."""
        return self.daily_data.get(date_str, {})

    def get_weekly_stats(self, week_start_date: date) -> Dict[str, Dict[str, float]]:
        """
        Aggregate daily data over a week.

        Returns statistics like averages, totals, etc. for each domain.
        """
        stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(list))

        # Collect data for 7 days
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            date_str = current_date.isoformat()
            daily = self.get_daily_data(date_str)

            # Collect metrics for each domain
            for domain, metrics in daily.items():
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        if isinstance(value, (int, float)):
                            stats[domain][metric].append(value)

        # Calculate averages
        result: Dict[str, Dict[str, float]] = {}
        for domain, metrics in stats.items():
            result[domain] = {}
            for metric, values in metrics.items():
                if values:
                    result[domain][f"{metric}_avg"] = sum(values) / len(values)
                    result[domain][f"{metric}_total"] = sum(values)
                    result[domain][f"{metric}_min"] = min(values)
                    result[domain][f"{metric}_max"] = max(values)

        return result

    def detect_patterns(self) -> List[Pattern]:
        """
        Identify patterns in user behavior over time.

        This is a simple pattern detection. In a real implementation,
        this would use more sophisticated analysis.
        """
        patterns = []

        # Pattern: Low energy on specific day of week
        if self._detect_day_of_week_pattern():
            patterns.append(Pattern(
                pattern_id="low_energy_monday",
                description="Low energy levels detected on Mondays",
                confidence=0.8,
                evidence=["Consistent pattern over 4+ weeks"]
            ))

        return patterns

    def _detect_day_of_week_pattern(self) -> bool:
        """Helper to detect day-of-week energy patterns."""
        # Group energy levels by day of week
        day_energies: Dict[int, List[float]] = defaultdict(list)

        for date_str, data in self.daily_data.items():
            try:
                # Handle both date objects and ISO format strings
                if isinstance(date_str, str):
                    dt = datetime.fromisoformat(date_str).date()
                else:
                    dt = date_str

                energy = data.get("health", {}).get("energy_level")
                if energy is not None:
                    day_energies[dt.weekday()].append(energy)
            except (ValueError, AttributeError, TypeError):
                continue

        # Check if any specific day consistently has lower energy
        for check_day in range(7):  # Check all days of week
            if check_day in day_energies and len(day_energies[check_day]) >= 4:
                check_day_avg = sum(day_energies[check_day]) / len(day_energies[check_day])
                other_days_avg = []

                for day in range(7):
                    if day != check_day and day in day_energies and day_energies[day]:
                        other_days_avg.extend(day_energies[day])

                if other_days_avg:
                    other_avg = sum(other_days_avg) / len(other_days_avg)
                    if check_day_avg < other_avg - 1.5:  # Significantly lower
                        return True

        return False

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user model to dictionary."""
        return {
            "user_id": self.user_id,
            "purpose_statement": self.purpose_statement,
            "purpose_history": [
                {
                    "statement": ph.statement,
                    "set_at": ph.set_at.isoformat(),
                    "notes": ph.notes
                }
                for ph in self.purpose_history
            ],
            "goals": [
                {
                    "id": g.id,
                    "domain": g.domain,
                    "description": g.description,
                    "time_horizon": g.time_horizon,
                    "parent_goal_id": g.parent_goal_id,
                    "status": g.status,
                    "outcome": g.outcome,
                    "completion_notes": g.completion_notes,
                    "created_at": g.created_at.isoformat(),
                    "completed_at": g.completed_at.isoformat() if g.completed_at else None,
                    "metadata": g.metadata
                }
                for g in self.goals
            ],
            "habits": [h.to_dict() for h in self.habits],
            "pinned_notes": [n.to_dict() for n in self.pinned_notes],
            "personality_traits": self.personality_traits,
            "preferences": self.preferences,
            "strengths": self.strengths,
            "growth_areas": self.growth_areas,
            "daily_data": self.daily_data,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserModel:
        """Deserialize user model from dictionary."""
        # Parse purpose history
        purpose_history = [
            PurposeHistory(
                statement=ph["statement"],
                set_at=datetime.fromisoformat(ph["set_at"]),
                notes=ph.get("notes", "")
            )
            for ph in data.get("purpose_history", [])
        ]

        # Parse goals
        goals = [
            Goal(
                id=g["id"],
                domain=g["domain"],
                description=g["description"],
                time_horizon=g["time_horizon"],
                parent_goal_id=g.get("parent_goal_id"),
                status=g.get("status", "active"),
                outcome=g.get("outcome"),
                completion_notes=g.get("completion_notes", ""),
                created_at=datetime.fromisoformat(g["created_at"]),
                completed_at=datetime.fromisoformat(g["completed_at"]) if g.get("completed_at") else None,
                metadata=g.get("metadata", {})
            )
            for g in data.get("goals", [])
        ]

        # Parse habits and pinned notes
        habits = [Habit.from_dict(h) for h in data.get("habits", [])]
        pinned_notes = [PinnedNote.from_dict(n) for n in data.get("pinned_notes", [])]

        return cls(
            user_id=data["user_id"],
            purpose_statement=data.get("purpose_statement"),
            purpose_history=purpose_history,
            goals=goals,
            habits=habits,
            pinned_notes=pinned_notes,
            personality_traits=data.get("personality_traits", {}),
            preferences=data.get("preferences", {}),
            strengths=data.get("strengths", []),
            growth_areas=data.get("growth_areas", []),
            daily_data=data.get("daily_data", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Save user model to disk."""
        if path is None:
            path = Path(f"data/user_data/{self.user_id}/user_model.json")

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, user_id: str, path: Optional[Path] = None) -> UserModel:
        """Load user model from disk."""
        if path is None:
            path = Path(f"data/user_data/{user_id}/user_model.json")

        with open(path, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)
