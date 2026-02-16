"""
Consciousness State — The shared blackboard.

This is the central data store for the consciousness layer. All ticks
read from and write to this state. Cross-loop communication happens
naturally through time-ranged reads on the observation log.

Components:
- Expectation: A prediction about one aspect of the user's life
- Observation: Result of comparing reality to an expectation
- DormantQuestion: An unresolved thought waiting for new data
- WorldModel: Dict of domain → expectations (what we believe about the user)
- Narrative: The unified story of the user's life
- ConsciousnessState: The complete shared blackboard
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import uuid

from alter.consciousness.config import (
    Severity,
    SummaryPeriod,
    OBSERVATION_BUFFER_SIZE,
    MAX_DORMANT_QUESTIONS,
    CONFIDENCE_MILESTONES,
    DORMANT_READINESS_THRESHOLD,
    RAW_OBSERVATION_RETENTION_HOURS,
    SUMMARY_RETENTION,
    MAX_SUMMARIES,
    MAX_NARRATIVE_HISTORY,
    READINESS_BUMP_DOMAIN_MATCH,
    READINESS_BUMP_ELEVATED,
    READINESS_BUMP_CRITICAL,
    READINESS_BUMP_SIGNAL_MATCH,
    SIGNAL_MATCH_MIN_WORD_LEN,
    classify_severity,
)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


@dataclass
class Expectation:
    """
    A prediction about one aspect of the user's life.

    Dual representation: numeric (for Python math) + natural language (for LLM).
    """
    domain: str                             # "health", "career", ...
    aspect: str                             # "sleep", "exercise", "mood", ...
    description: str                        # NL for LLM: "Sleeps 7-8h on weeknights"
    numeric_value: Optional[float] = None   # For Python comparison: 7.5
    numeric_range: Optional[tuple] = None   # Tolerance band: (7.0, 8.0)
    data_field: Optional[str] = None        # Maps to user.daily_data key: "sleep_hours"
    confidence: float = 0.0                 # 0-1, scales prediction error
    data_points: int = 0                    # How many observations this is based on
    last_confirmed: Optional[str] = None    # ISO timestamp
    last_violated: Optional[str] = None     # ISO timestamp

    def update_confidence(self) -> None:
        """Update confidence based on number of data points."""
        for threshold, conf in sorted(CONFIDENCE_MILESTONES.items(), reverse=True):
            if self.data_points >= threshold:
                self.confidence = max(self.confidence, conf)
                break

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "aspect": self.aspect,
            "description": self.description,
            "numeric_value": self.numeric_value,
            "numeric_range": list(self.numeric_range) if self.numeric_range else None,
            "data_field": self.data_field,
            "confidence": self.confidence,
            "data_points": self.data_points,
            "last_confirmed": self.last_confirmed,
            "last_violated": self.last_violated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Expectation:
        nr = data.get("numeric_range")
        return cls(
            domain=data["domain"],
            aspect=data["aspect"],
            description=data["description"],
            numeric_value=data.get("numeric_value"),
            numeric_range=tuple(nr) if nr else None,
            data_field=data.get("data_field"),
            confidence=data.get("confidence", 0.0),
            data_points=data.get("data_points", 0),
            last_confirmed=data.get("last_confirmed"),
            last_violated=data.get("last_violated"),
        )


@dataclass
class Observation:
    """
    Result of comparing reality to an expectation.

    Produced by observe step (Python math for hourly, LLM for daily+).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tick_type: str = ""                     # "hourly_pulse", "daily_review", etc.
    domain: str = ""                        # "health"
    aspect: str = ""                        # "sleep"
    expected: str = ""                      # "7-8 hours"
    observed: str = ""                      # "5 hours"
    prediction_error: float = 0.0           # 0.0-1.0
    severity: str = Severity.NORMAL.value   # "normal" | "elevated" | "critical"
    summary: str = ""                       # Human-readable summary
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tick_type": self.tick_type,
            "domain": self.domain,
            "aspect": self.aspect,
            "expected": self.expected,
            "observed": self.observed,
            "prediction_error": self.prediction_error,
            "severity": self.severity,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "raw_data": self.raw_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Observation:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DormantQuestion:
    """
    An unresolved thought waiting for new data.

    Has resolution_signals (what data would answer it), a readiness score
    (increases as signals arrive), and a threshold. When readiness crosses
    the threshold, the question re-enters the next LLM tick.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    question: str = ""
    context: str = ""                       # Why this question arose
    domain: str = ""                        # Primary life domain
    resolution_signals: List[str] = field(default_factory=list)
    readiness: float = 0.0                  # 0-1, increases as signals arrive
    threshold: float = DORMANT_READINESS_THRESHOLD
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by_tick: str = ""               # Which tick created this
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None        # How it was resolved

    def is_ready(self) -> bool:
        """Check if readiness has crossed the threshold."""
        return self.readiness >= self.threshold and not self.resolved

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "context": self.context,
            "domain": self.domain,
            "resolution_signals": self.resolution_signals,
            "readiness": self.readiness,
            "threshold": self.threshold,
            "created_at": self.created_at,
            "created_by_tick": self.created_by_tick,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "resolution": self.resolution,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DormantQuestion:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Summary:
    """
    A compressed representation of a time period's observations and insights.

    Part of the hierarchical memory system:
        Raw observations (hourly) → daily summary → weekly summary → monthly summary

    Each higher-level tick reads summaries from the level below instead of
    raw data, achieving ~20x compression while preserving semantic meaning.

    Summaries are produced by LLM ticks as a natural output of their processing.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    period_type: str = ""                   # "daily" | "weekly" | "monthly"
    period_label: str = ""                  # "2026-02-16" | "2026-W07" | "2026-02"
    content: str = ""                       # NL summary from LLM — the core compressed text
    key_insights: List[str] = field(default_factory=list)    # Structured findings
    key_facts: Dict[str, Any] = field(default_factory=dict)  # Quantitative data (averages, counts, trends)
    domains_covered: List[str] = field(default_factory=list)
    prediction_errors_summary: str = ""     # Notable prediction errors in NL
    observation_count: int = 0              # How many raw observations were compressed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by_tick: str = ""               # Which tick produced this

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "period_type": self.period_type,
            "period_label": self.period_label,
            "content": self.content,
            "key_insights": self.key_insights,
            "key_facts": self.key_facts,
            "domains_covered": self.domains_covered,
            "prediction_errors_summary": self.prediction_errors_summary,
            "observation_count": self.observation_count,
            "created_at": self.created_at,
            "created_by_tick": self.created_by_tick,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Summary:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# World Model
# ---------------------------------------------------------------------------


class WorldModel:
    """
    The "what I believe about this person's life right now" layer.

    Dict of domain → list of expectations. Includes both predictions
    AND context (season, upcoming events, recent changes).
    """

    def __init__(
        self,
        expectations: Optional[Dict[str, List[Expectation]]] = None,
        context: Optional[Dict[str, Dict[str, str]]] = None,
        last_updated: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        self.expectations: Dict[str, List[Expectation]] = expectations or {}
        self.context: Dict[str, Dict[str, str]] = context or {}
        self.last_updated = last_updated
        self.updated_by = updated_by

    def get_expectation(self, domain: str, aspect: str) -> Optional[Expectation]:
        """Get a specific expectation by domain and aspect."""
        for exp in self.expectations.get(domain, []):
            if exp.aspect == aspect:
                return exp
        return None

    def set_expectation(self, expectation: Expectation) -> None:
        """Add or update an expectation."""
        domain_exps = self.expectations.setdefault(expectation.domain, [])
        for i, exp in enumerate(domain_exps):
            if exp.aspect == expectation.aspect:
                domain_exps[i] = expectation
                return
        domain_exps.append(expectation)

    def get_all_expectations(self) -> List[Expectation]:
        """Get all expectations across all domains."""
        result = []
        for exps in self.expectations.values():
            result.extend(exps)
        return result

    def get_numeric_expectations(self) -> List[Expectation]:
        """Get expectations that have numeric values (for Python comparison)."""
        return [
            exp for exp in self.get_all_expectations()
            if exp.numeric_value is not None and exp.data_field is not None
        ]

    def get_domains(self) -> List[str]:
        """Get all domains that have expectations."""
        return list(self.expectations.keys())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expectations": {
                domain: [exp.to_dict() for exp in exps]
                for domain, exps in self.expectations.items()
            },
            "context": self.context,
            "last_updated": self.last_updated,
            "updated_by": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorldModel:
        expectations = {}
        for domain, exps in data.get("expectations", {}).items():
            expectations[domain] = [Expectation.from_dict(e) for e in exps]

        return cls(
            expectations=expectations,
            context=data.get("context", {}),
            last_updated=data.get("last_updated"),
            updated_by=data.get("updated_by"),
        )


# ---------------------------------------------------------------------------
# Consciousness State — The Shared Blackboard
# ---------------------------------------------------------------------------


class ConsciousnessState:
    """
    The complete consciousness state. All ticks read from and write to this.

    Provides:
    - World model (expectations about the user's life)
    - Observation log (ring buffer, time-ranged reads for snapshots)
    - Narrative thread (unified story, updated per LLM tick)
    - Dormant questions (subconscious thoughts)
    - Pending notifications (messages to surface to user)
    - Watch events (critical errors that triggered immediate thinking)
    """

    def __init__(
        self,
        user_id: str,
        world_model: Optional[WorldModel] = None,
        observations: Optional[List[Observation]] = None,
        narrative: str = "",
        narrative_history: Optional[List[Dict[str, str]]] = None,
        dormant_questions: Optional[List[DormantQuestion]] = None,
        pending_notifications: Optional[List[Dict[str, Any]]] = None,
        watch_events: Optional[List[Dict[str, Any]]] = None,
        token_usage: Optional[Dict[str, int]] = None,
        summaries: Optional[Dict[str, List[Summary]]] = None,
    ):
        self.user_id = user_id
        self.world_model = world_model or WorldModel()
        self.observations: List[Observation] = observations or []
        self.narrative = narrative
        self.narrative_history: List[Dict[str, str]] = narrative_history or []
        self.dormant_questions: List[DormantQuestion] = dormant_questions or []
        self.pending_notifications: List[Dict[str, Any]] = pending_notifications or []
        self.watch_events: List[Dict[str, Any]] = watch_events or []
        self.token_usage: Dict[str, int] = token_usage or {}
        # Hierarchical summaries: {"daily": [...], "weekly": [...], "monthly": [...]}
        self.summaries: Dict[str, List[Summary]] = summaries or {}

    # --- Observations ---

    def add_observation(self, obs: Observation) -> None:
        """Add an observation to the log, maintaining ring buffer size per domain."""
        self.observations.append(obs)
        self._trim_observations(obs.domain)

    def add_observations(self, observations: List[Observation]) -> None:
        """Add multiple observations."""
        domains_touched = set()
        for obs in observations:
            self.observations.append(obs)
            domains_touched.add(obs.domain)
        for domain in domains_touched:
            self._trim_observations(domain)

    def _trim_observations(self, domain: str) -> None:
        """Trim observation buffer for a domain to max size."""
        domain_obs = [o for o in self.observations if o.domain == domain]
        if len(domain_obs) > OBSERVATION_BUFFER_SIZE:
            # Sort by timestamp, keep newest
            domain_obs.sort(key=lambda o: o.timestamp)
            keep = set(id(o) for o in domain_obs[-OBSERVATION_BUFFER_SIZE:])
            self.observations = [
                o for o in self.observations
                if o.domain != domain or id(o) in keep
            ]

    def get_observations_since(
        self,
        since: datetime,
        domain: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Observation]:
        """
        Snapshot read: get observations since a timestamp.

        This is the primary cross-loop communication mechanism.
        """
        since_iso = since.isoformat()
        results = []
        for obs in self.observations:
            if obs.timestamp < since_iso:
                continue
            if domain and obs.domain != domain:
                continue
            if severity and obs.severity != severity:
                continue
            results.append(obs)
        return sorted(results, key=lambda o: o.timestamp)

    def get_elevated_observations_since(self, since: datetime) -> List[Observation]:
        """Get elevated+ observations since a timestamp (for daily tick attention)."""
        since_iso = since.isoformat()
        return [
            o for o in self.observations
            if o.timestamp >= since_iso
            and o.severity in (Severity.ELEVATED.value, Severity.CRITICAL.value)
        ]

    # --- Dormant Questions ---

    def add_dormant_question(self, question: DormantQuestion) -> None:
        """Add a dormant question, pruning if at capacity."""
        self.dormant_questions.append(question)
        if len(self.dormant_questions) > MAX_DORMANT_QUESTIONS:
            # Prune lowest-readiness unresolved question
            unresolved = [q for q in self.dormant_questions if not q.resolved]
            if unresolved:
                lowest = min(unresolved, key=lambda q: q.readiness)
                self.dormant_questions.remove(lowest)

    def get_ready_questions(self) -> List[DormantQuestion]:
        """Get dormant questions that have crossed their readiness threshold."""
        return [q for q in self.dormant_questions if q.is_ready()]

    def get_unresolved_questions(self, limit: Optional[int] = None) -> List[DormantQuestion]:
        """Get unresolved dormant questions, sorted by readiness (highest first)."""
        unresolved = sorted(
            [q for q in self.dormant_questions if not q.resolved],
            key=lambda q: q.readiness,
            reverse=True,
        )
        if limit:
            return unresolved[:limit]
        return unresolved

    def resolve_question(self, question_id: str, resolution: str) -> None:
        """Mark a dormant question as resolved."""
        for q in self.dormant_questions:
            if q.id == question_id:
                q.resolved = True
                q.resolved_at = datetime.now().isoformat()
                q.resolution = resolution
                break

    # --- Notifications ---

    def add_notification(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Queue a notification to surface to the user."""
        self.pending_notifications.append({
            "id": str(uuid.uuid4())[:8],
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "delivered": False,
        })

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get undelivered notifications."""
        return [n for n in self.pending_notifications if not n.get("delivered")]

    def mark_notification_delivered(self, notification_id: str) -> None:
        """Mark a notification as delivered."""
        for n in self.pending_notifications:
            if n["id"] == notification_id:
                n["delivered"] = True
                break

    # --- Watch Events ---

    def add_watch_event(self, critical_observations: List[Observation], tick_result: Optional[Dict[str, Any]] = None) -> None:
        """Record a watch event (critical prediction error → immediate thinking)."""
        self.watch_events.append({
            "id": str(uuid.uuid4())[:8],
            "observations": [o.to_dict() for o in critical_observations],
            "tick_result": tick_result,
            "timestamp": datetime.now().isoformat(),
        })

    # --- Narrative ---

    def update_narrative(self, narrative: str) -> None:
        """Update the narrative thread, pushing the previous version to history."""
        if self.narrative and self.narrative != narrative:
            self.narrative_history.append({
                "narrative": self.narrative,
                "timestamp": datetime.now().isoformat(),
            })
            # Keep only the most recent entries
            if len(self.narrative_history) > MAX_NARRATIVE_HISTORY:
                self.narrative_history = self.narrative_history[-MAX_NARRATIVE_HISTORY:]
        self.narrative = narrative

    # --- Dormant Question Readiness ---

    def update_dormant_readiness(
        self, observations: List[Observation]
    ) -> List[DormantQuestion]:
        """
        Update dormant question readiness based on new observations.

        For each unresolved question, checks if observations correlate with
        its domain and resolution signals. Bumps readiness accordingly.

        Returns: questions that crossed the readiness threshold (newly ready).
        """
        newly_ready = []
        unresolved = self.get_unresolved_questions()

        for question in unresolved:
            was_ready = question.is_ready()

            for obs in observations:
                bump = 0.0

                # Domain correlation — same domain gets a base bump
                if question.domain and obs.domain == question.domain:
                    bump = READINESS_BUMP_DOMAIN_MATCH
                    # Higher bump for elevated/critical severity
                    if obs.severity == "elevated":
                        bump = READINESS_BUMP_ELEVATED
                    elif obs.severity == "critical":
                        bump = READINESS_BUMP_CRITICAL

                # Resolution signal keyword match
                if question.resolution_signals and obs.summary:
                    obs_lower = obs.summary.lower()
                    for signal in question.resolution_signals:
                        signal_terms = [
                            w for w in signal.lower().split()
                            if len(w) >= SIGNAL_MATCH_MIN_WORD_LEN
                        ]
                        if signal_terms:
                            matches = sum(
                                1 for term in signal_terms if term in obs_lower
                            )
                            if matches >= max(1, len(signal_terms) // 3):
                                bump = max(bump, READINESS_BUMP_SIGNAL_MATCH)
                                break

                if bump > 0:
                    question.readiness = min(1.0, question.readiness + bump)

            # Track questions that just crossed the threshold
            if question.is_ready() and not was_ready:
                newly_ready.append(question)

        return newly_ready

    # --- Summaries / Hierarchical Memory ---

    def add_summary(self, summary: Summary) -> None:
        """
        Add a summary, replacing any existing one for the same period.

        Summaries are produced by LLM ticks:
        - daily_review → daily summary
        - weekly_reflect → weekly summary
        - monthly_deep → monthly summary
        """
        period_list = self.summaries.setdefault(summary.period_type, [])

        # Replace existing summary for same period label (idempotent)
        period_list[:] = [s for s in period_list if s.period_label != summary.period_label]
        period_list.append(summary)

        # Sort by period_label (chronological) and trim to max
        period_list.sort(key=lambda s: s.period_label)
        period_type = SummaryPeriod(summary.period_type)
        max_count = MAX_SUMMARIES.get(period_type, 100)
        if len(period_list) > max_count:
            self.summaries[summary.period_type] = period_list[-max_count:]

    def get_summaries(
        self,
        period_type: str,
        limit: Optional[int] = None,
        since_label: Optional[str] = None,
    ) -> List[Summary]:
        """
        Get summaries for a period type, newest first.

        This is how higher-level ticks read compressed context:
        - Weekly tick reads daily summaries (last 7)
        - Monthly tick reads weekly summaries (last 4)

        Args:
            period_type: "daily", "weekly", or "monthly"
            limit: Max number to return
            since_label: Only return summaries with period_label >= this
        """
        all_summaries = self.summaries.get(period_type, [])
        if since_label:
            all_summaries = [s for s in all_summaries if s.period_label >= since_label]
        # Return newest first
        result = sorted(all_summaries, key=lambda s: s.period_label, reverse=True)
        if limit:
            return result[:limit]
        return result

    def get_summary_for_period(self, period_type: str, period_label: str) -> Optional[Summary]:
        """Get a specific summary by type and label."""
        for s in self.summaries.get(period_type, []):
            if s.period_label == period_label:
                return s
        return None

    def get_context_for_tick(
        self,
        tick_type: str,
    ) -> Dict[str, Any]:
        """
        Get the right level of context for a tick type.

        This is the key method for hierarchical memory:
        - daily_review: raw observations (last 24h) — small enough for raw data
        - weekly_reflect: daily summaries (last 7) — NOT raw hourly observations
        - monthly_deep: weekly summaries (last 4) — NOT raw daily data
        - urgent: raw observations for the triggering domain only

        Returns a dict of context sections that context.py (Phase C2) will
        assemble into the prompt.
        """
        now = datetime.now()

        if tick_type == "daily_review":
            return {
                "observations": [o.to_dict() for o in self.get_observations_since(now - timedelta(hours=24))],
                "elevated_errors": [o.to_dict() for o in self.get_elevated_observations_since(now - timedelta(hours=24))],
                "narrative": self.narrative,
                "dormant_questions": [q.to_dict() for q in self.get_unresolved_questions(limit=5)],
            }

        elif tick_type == "weekly_reflect":
            # Use daily summaries instead of raw observations — ~7x compression
            return {
                "daily_summaries": [s.to_dict() for s in self.get_summaries("daily", limit=7)],
                "elevated_errors": [o.to_dict() for o in self.get_elevated_observations_since(now - timedelta(days=7))],
                "narrative": self.narrative,
                "dormant_questions": [q.to_dict() for q in self.get_unresolved_questions()],
            }

        elif tick_type == "monthly_deep":
            # Use weekly summaries instead of raw data — ~30x compression
            return {
                "weekly_summaries": [s.to_dict() for s in self.get_summaries("weekly", limit=4)],
                "daily_summaries": [s.to_dict() for s in self.get_summaries("daily", limit=7)],  # recent detail
                "narrative": self.narrative,
                "dormant_questions": [q.to_dict() for q in self.get_unresolved_questions()],
            }

        elif tick_type == "urgent":
            # Focused: only recent observations, no summaries needed
            return {
                "observations": [o.to_dict() for o in self.get_observations_since(now - timedelta(hours=6))],
                "narrative": self.narrative,
            }

        # Fallback
        return {"narrative": self.narrative}

    def compact(self) -> Dict[str, int]:
        """
        Compact old raw data that has been summarized.

        Called periodically (e.g., after each daily tick) to prune raw
        observations and old summaries that are no longer needed.

        Retention policy:
        - Raw observations: keep last RAW_OBSERVATION_RETENTION_HOURS
        - Daily summaries: keep last SUMMARY_RETENTION[daily] days
        - Weekly summaries: keep last SUMMARY_RETENTION[weekly] days
        - Monthly summaries: keep forever

        Returns dict of what was pruned: {"observations": N, "daily_summaries": N, ...}
        """
        now = datetime.now()
        pruned = {}

        # 1. Prune raw observations older than retention window
        cutoff = (now - timedelta(hours=RAW_OBSERVATION_RETENTION_HOURS)).isoformat()
        before = len(self.observations)
        self.observations = [o for o in self.observations if o.timestamp >= cutoff]
        pruned["observations"] = before - len(self.observations)

        # 2. Prune old summaries per retention policy
        for period_type_enum, retention_days in SUMMARY_RETENTION.items():
            period_type = period_type_enum.value
            if retention_days is None:
                continue  # Keep forever (monthly)

            period_list = self.summaries.get(period_type, [])
            cutoff_date = (now - timedelta(days=retention_days)).isoformat()
            before = len(period_list)
            self.summaries[period_type] = [
                s for s in period_list if s.created_at >= cutoff_date
            ]
            pruned[f"{period_type}_summaries"] = before - len(self.summaries.get(period_type, []))

        # 3. Prune delivered notifications older than 7 days
        notif_cutoff = (now - timedelta(days=7)).isoformat()
        before = len(self.pending_notifications)
        self.pending_notifications = [
            n for n in self.pending_notifications
            if not n.get("delivered") or n.get("timestamp", "") >= notif_cutoff
        ]
        pruned["notifications"] = before - len(self.pending_notifications)

        # 4. Prune resolved dormant questions older than 30 days
        q_cutoff = (now - timedelta(days=30)).isoformat()
        before = len(self.dormant_questions)
        self.dormant_questions = [
            q for q in self.dormant_questions
            if not q.resolved or (q.resolved_at or "") >= q_cutoff
        ]
        pruned["dormant_questions"] = before - len(self.dormant_questions)

        return pruned

    # --- Token Tracking ---

    def record_token_usage(self, tick_type: str, tokens: int) -> None:
        """Record tokens used by a tick type."""
        today = datetime.now().date().isoformat()
        key = f"{today}:{tick_type}"
        self.token_usage[key] = self.token_usage.get(key, 0) + tokens

    def get_daily_token_usage(self, date_str: Optional[str] = None) -> int:
        """Get total tokens used on a given day."""
        date_str = date_str or datetime.now().date().isoformat()
        return sum(
            v for k, v in self.token_usage.items()
            if k.startswith(date_str)
        )

    # --- Persistence ---

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "world_model": self.world_model.to_dict(),
            "observations": [o.to_dict() for o in self.observations],
            "narrative": self.narrative,
            "narrative_history": self.narrative_history,
            "dormant_questions": [q.to_dict() for q in self.dormant_questions],
            "pending_notifications": self.pending_notifications,
            "watch_events": self.watch_events,
            "token_usage": self.token_usage,
            "summaries": {
                period_type: [s.to_dict() for s in summaries]
                for period_type, summaries in self.summaries.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsciousnessState:
        summaries = {}
        for period_type, summary_list in data.get("summaries", {}).items():
            summaries[period_type] = [Summary.from_dict(s) for s in summary_list]

        return cls(
            user_id=data["user_id"],
            world_model=WorldModel.from_dict(data.get("world_model", {})),
            observations=[Observation.from_dict(o) for o in data.get("observations", [])],
            narrative=data.get("narrative", ""),
            narrative_history=data.get("narrative_history", []),
            dormant_questions=[DormantQuestion.from_dict(q) for q in data.get("dormant_questions", [])],
            pending_notifications=data.get("pending_notifications", []),
            watch_events=data.get("watch_events", []),
            token_usage=data.get("token_usage", {}),
            summaries=summaries,
        )

    def save(self, path: Optional[Path] = None) -> None:
        """Save consciousness state to disk."""
        if path is None:
            path = Path(f"data/user_data/{self.user_id}/consciousness_state.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, user_id: str, path: Optional[Path] = None) -> ConsciousnessState:
        """Load consciousness state from disk."""
        if path is None:
            path = Path(f"data/user_data/{user_id}/consciousness_state.json")
        if not path.exists():
            return cls(user_id=user_id)
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
