"""
Consciousness Configuration — Tick types, thresholds, severity levels.

All tunable constants for the consciousness layer live here.
"""

from __future__ import annotations

from enum import Enum


class TickType(str, Enum):
    """Types of consciousness ticks, each with different frequency and depth."""
    HOURLY_PULSE = "hourly_pulse"      # Pre-attentive signal detection (Python), escalates via watch
    DAILY_REVIEW = "daily_review"      # LLM — daily conscious reasoning
    WEEKLY_REFLECT = "weekly_reflect"  # LLM — cross-domain synthesis
    MONTHLY_DEEP = "monthly_deep"      # LLM — existential / purpose review
    URGENT = "urgent"                  # LLM — immediate reasoning (triggered by watch event or user)


class Severity(str, Enum):
    """Prediction error severity levels."""
    NORMAL = "normal"      # error < 0.5 — logged, processed on next snapshot
    ELEVATED = "elevated"  # 0.5 <= error < 0.8 — flagged for daily tick
    CRITICAL = "critical"  # error >= 0.8 — triggers immediate watch event


# Severity thresholds
SEVERITY_THRESHOLDS = {
    Severity.NORMAL: (0.0, 0.5),
    Severity.ELEVATED: (0.5, 0.8),
    Severity.CRITICAL: (0.8, float("inf")),
}

# Observation ring buffer size per domain
OBSERVATION_BUFFER_SIZE = 100

# Max dormant questions before pruning lowest-readiness
MAX_DORMANT_QUESTIONS = 20

# Default confidence for user-stated expectations (not observed)
STATED_CONFIDENCE = 0.3

# Minimum confidence before prediction errors trigger attention
MIN_CONFIDENCE_FOR_ATTENTION = 0.2

# Number of data points for confidence milestones
CONFIDENCE_MILESTONES = {
    1: 0.1,   # 1 data point
    3: 0.2,   # 3 data points
    7: 0.5,   # 1 week
    14: 0.7,  # 2 weeks
    30: 0.9,  # 1 month
}

# Dormant question readiness threshold for resurfacing
DORMANT_READINESS_THRESHOLD = 0.7

# Readiness bump amounts when observations match dormant questions
READINESS_BUMP_DOMAIN_MATCH = 0.05     # Same domain as question
READINESS_BUMP_ELEVATED = 0.10         # Elevated severity + domain match
READINESS_BUMP_CRITICAL = 0.15         # Critical severity + domain match
READINESS_BUMP_SIGNAL_MATCH = 0.20     # Resolution signal keyword match

# Minimum word length for signal matching (skip short words)
SIGNAL_MATCH_MIN_WORD_LEN = 4

# Maximum narrative history entries to retain
MAX_NARRATIVE_HISTORY = 10

# ---------------------------------------------------------------------------
# Memory / Summarization Retention Policy
# ---------------------------------------------------------------------------
# After a tick produces a summary, raw data from that period can be compacted.
# These define how long to keep each level of detail.

class SummaryPeriod(str, Enum):
    """Period types for hierarchical summaries."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# How long to keep raw observations before compaction (hours)
RAW_OBSERVATION_RETENTION_HOURS = 48

# How long to keep each summary level
SUMMARY_RETENTION = {
    SummaryPeriod.DAILY: 90,     # keep daily summaries for 90 days
    SummaryPeriod.WEEKLY: 180,   # keep weekly summaries for 6 months
    SummaryPeriod.MONTHLY: None, # keep monthly summaries forever
}

# Max summaries per period type (safety cap)
MAX_SUMMARIES = {
    SummaryPeriod.DAILY: 90,
    SummaryPeriod.WEEKLY: 26,
    SummaryPeriod.MONTHLY: 120,  # 10 years
}


# ---------------------------------------------------------------------------
# Token Budgets Per Tick Type
# ---------------------------------------------------------------------------
# Max input tokens for context assembly. Assembly stops when the budget is
# reached, dropping lowest-priority sections first. Adjust these to trade
# off between depth of reasoning and token usage.

TOKEN_BUDGETS = {
    TickType.DAILY_REVIEW.value: 3200,
    TickType.WEEKLY_REFLECT.value: 5300,
    TickType.MONTHLY_DEEP.value: 7900,
    TickType.URGENT.value: 1300,
}


def classify_severity(prediction_error: float) -> Severity:
    """Classify a prediction error into a severity level."""
    if prediction_error >= 0.8:
        return Severity.CRITICAL
    elif prediction_error >= 0.5:
        return Severity.ELEVATED
    return Severity.NORMAL
