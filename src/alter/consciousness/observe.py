"""
Observation — Python-only prediction error math.

This module runs during hourly ticks with ZERO LLM cost. It compares
the user's actual daily data against the world model's numeric expectations
and produces Observation objects with prediction error scores.

The key formula:
    raw_error = |expected - actual| / expected
    effective_error = raw_error * confidence

Confidence scaling naturally handles cold start: new expectations with
low confidence produce dampened errors that won't trigger attention.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from alter.consciousness.config import TickType, classify_severity, MIN_CONFIDENCE_FOR_ATTENTION
from alter.consciousness.state import (
    ConsciousnessState,
    Expectation,
    Observation,
    WorldModel,
)


def compute_prediction_error(
    expected: float,
    actual: float,
    confidence: float,
    numeric_range: Optional[tuple] = None,
) -> float:
    """
    Compute prediction error between expected and actual values.

    Formula: |expected - actual| / expected * confidence
    If numeric_range is provided, values within range have zero error.

    Returns a value in [0.0, 1.0] (clamped).
    """
    # If within tolerance range, no error
    if numeric_range:
        low, high = numeric_range
        if low <= actual <= high:
            return 0.0

    # Avoid division by zero
    if expected == 0:
        raw_error = abs(actual) if actual != 0 else 0.0
    else:
        raw_error = abs(expected - actual) / abs(expected)

    # Scale by confidence
    effective_error = raw_error * confidence

    # Clamp to [0, 1]
    return min(max(effective_error, 0.0), 1.0)


def observe_daily_data(
    world_model: WorldModel,
    daily_data: Dict[str, Any],
) -> List[Observation]:
    """
    Compare today's daily data against world model expectations.

    This is the hourly tick's core operation. Pure Python, no LLM.

    Args:
        world_model: Current world model with expectations
        daily_data: Today's data from UserModel.daily_data
            Format: {"health": {"sleep_hours": 5, ...}, "emotions": {"mood": 3}, ...}

    Returns:
        List of Observations with prediction errors
    """
    observations = []
    now = datetime.now().isoformat()

    for expectation in world_model.get_numeric_expectations():
        # Skip low-confidence expectations (cold start dampening)
        if expectation.confidence < MIN_CONFIDENCE_FOR_ATTENTION:
            continue

        # Find the actual value in daily_data
        actual_value = _extract_value(daily_data, expectation)
        if actual_value is None:
            continue

        # Compute prediction error
        error = compute_prediction_error(
            expected=expectation.numeric_value,
            actual=actual_value,
            confidence=expectation.confidence,
            numeric_range=expectation.numeric_range,
        )

        severity = classify_severity(error)

        # Build observation
        obs = Observation(
            tick_type=TickType.HOURLY_PULSE.value,
            domain=expectation.domain,
            aspect=expectation.aspect,
            expected=f"{expectation.numeric_value} (range: {expectation.numeric_range})" if expectation.numeric_range else str(expectation.numeric_value),
            observed=str(actual_value),
            prediction_error=round(error, 3),
            severity=severity.value,
            summary=_build_summary(expectation, actual_value, error),
            timestamp=now,
            raw_data={
                "expected_value": expectation.numeric_value,
                "actual_value": actual_value,
                "raw_error": abs(expectation.numeric_value - actual_value) / abs(expectation.numeric_value) if expectation.numeric_value else 0,
                "confidence": expectation.confidence,
                "data_field": expectation.data_field,
            },
        )
        observations.append(obs)

    return observations


def update_expectation_from_data(
    expectation: Expectation,
    actual_value: float,
    learning_rate: float = 0.1,
) -> None:
    """
    Update an expectation's numeric value based on new data.

    Uses exponential moving average to slowly adjust expectations
    as the user's patterns change. Also updates confidence.

    Args:
        expectation: The expectation to update
        actual_value: The new observed value
        learning_rate: How fast to adjust (0.1 = slow adaptation)
    """
    if expectation.numeric_value is not None:
        # Exponential moving average
        expectation.numeric_value = (
            expectation.numeric_value * (1 - learning_rate)
            + actual_value * learning_rate
        )

        # Update range if provided
        if expectation.numeric_range:
            low, high = expectation.numeric_range
            # Slowly widen or narrow range
            new_low = low * (1 - learning_rate) + min(actual_value, low) * learning_rate
            new_high = high * (1 - learning_rate) + max(actual_value, high) * learning_rate
            expectation.numeric_range = (round(new_low, 2), round(new_high, 2))
    else:
        # First numeric value
        expectation.numeric_value = actual_value

    # Update metadata
    expectation.data_points += 1
    expectation.update_confidence()
    expectation.last_confirmed = datetime.now().isoformat()


def _extract_value(
    daily_data: Dict[str, Any],
    expectation: Expectation,
) -> Optional[float]:
    """
    Extract the actual value for an expectation from daily data.

    The data_field on the expectation maps to a key in the daily_data dict.
    Daily data is nested by domain: {"health": {"sleep_hours": 7}, ...}
    """
    if not expectation.data_field:
        return None

    # Try domain-nested lookup first: daily_data[domain][data_field]
    domain_data = daily_data.get(expectation.domain, {})
    if isinstance(domain_data, dict):
        value = domain_data.get(expectation.data_field)
        if value is not None and isinstance(value, (int, float)):
            return float(value)

    # Fallback: try flat lookup: daily_data[data_field]
    value = daily_data.get(expectation.data_field)
    if value is not None and isinstance(value, (int, float)):
        return float(value)

    return None


def _build_summary(
    expectation: Expectation,
    actual_value: float,
    error: float,
) -> str:
    """Build a human-readable summary for an observation."""
    severity = classify_severity(error)

    if error == 0:
        return f"{expectation.aspect} ({expectation.domain}): as expected ({actual_value})"

    direction = "below" if actual_value < (expectation.numeric_value or 0) else "above"

    if severity.value == "normal":
        return f"{expectation.aspect} ({expectation.domain}): slightly {direction} expected ({actual_value} vs {expectation.numeric_value})"
    elif severity.value == "elevated":
        return f"{expectation.aspect} ({expectation.domain}): notably {direction} expected ({actual_value} vs {expectation.numeric_value})"
    else:
        return f"{expectation.aspect} ({expectation.domain}): significantly {direction} expected ({actual_value} vs {expectation.numeric_value})"
