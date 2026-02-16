"""
Demo: ALTER Consciousness Pipeline (C1 + C2 + C3)

This demo shows the full pipeline in two modes:

1. MANUAL MODE (C1+C2): Step-by-step observe → assemble → prompt → parse
2. ENGINE MODE (C3): ConsciousnessEngine orchestrates everything in one call

Both use a mock think_fn (no real LLM call) to demonstrate the full flow.

Run: python -m examples.demo_consciousness_pipeline
"""

import json
from datetime import datetime

from alter.consciousness.config import TickType
from alter.consciousness.state import (
    ConsciousnessState,
    DormantQuestion,
    Expectation,
    Observation,
    Summary,
)
from alter.consciousness.observe import observe_daily_data
from alter.consciousness.context import ContextAssembler
from alter.consciousness.prompts import build_prompt
from alter.consciousness.parse import parse_tick_result
from alter.consciousness.engine import ConsciousnessEngine
from alter.consciousness.llm import create_mock_think_fn
from alter.core.user_model import UserModel, Goal


def create_demo_user() -> UserModel:
    """Create a demo user with goals and personality."""
    user = UserModel(user_id="demo_user")
    user.set_purpose("Live a balanced life while building a meaningful career in tech")
    user.add_goal(Goal(
        id="g1", domain="health",
        description="Sleep 7+ hours consistently",
        time_horizon="quarter",
    ))
    user.add_goal(Goal(
        id="g2", domain="career",
        description="Ship the v2 product launch",
        time_horizon="quarter",
    ))
    user.add_goal(Goal(
        id="g3", domain="relationships",
        description="Have dinner with family 3x/week",
        time_horizon="month",
    ))
    user.set_personality_traits({"openness": 8, "conscientiousness": 7, "agreeableness": 6})
    user.set_preference("communication_style", "direct but warm")
    user.record_daily_data({
        "date": datetime.now().date().isoformat(),
        "health": {"sleep_hours": 5.0, "exercise_minutes": 0, "energy_level": 4},
        "emotions": {"mood": 4, "stress": 8},
        "career": {"work_hours": 11, "focus_rating": 6},
    })
    return user


def create_demo_consciousness_state() -> ConsciousnessState:
    """Create a consciousness state with world model and history."""
    state = ConsciousnessState(user_id="demo_user")

    # Build world model expectations
    state.world_model.set_expectation(Expectation(
        domain="health", aspect="sleep",
        description="Sleeps 7-8 hours on weeknights",
        numeric_value=7.5, numeric_range=(7.0, 8.0),
        data_field="sleep_hours", confidence=0.8, data_points=21,
    ))
    state.world_model.set_expectation(Expectation(
        domain="health", aspect="exercise",
        description="Exercises 30+ minutes most days",
        numeric_value=30.0, numeric_range=(20.0, 60.0),
        data_field="exercise_minutes", confidence=0.6, data_points=14,
    ))
    state.world_model.set_expectation(Expectation(
        domain="emotions", aspect="mood",
        description="Generally positive mood (7/10)",
        numeric_value=7.0, numeric_range=(6.0, 8.0),
        data_field="mood", confidence=0.7, data_points=14,
    ))

    # Set narrative
    state.update_narrative(
        "User is in a high-pressure phase preparing for a product launch. "
        "Sleep has been declining over the past few days. Energy and mood "
        "are following the downward trend. Work hours are extended."
    )

    # Add a dormant question
    state.add_dormant_question(DormantQuestion(
        question="Is the sleep decline temporary (deadline push) or becoming a pattern?",
        context="Sleep dropped below 6h for two consecutive nights",
        domain="health",
        resolution_signals=["sleep recovers after launch", "sleep stays low post-deadline"],
        readiness=0.4,
    ))

    # Add some daily summaries (from previous days)
    state.add_summary(Summary(
        period_type="daily", period_label="2026-02-14",
        content="Mostly normal day. Sleep was 6.5h (slightly low). Work was productive. Mood stable.",
        key_insights=["Sleep slightly below range but not alarming"],
        key_facts={"sleep_hours": 6.5, "mood": 6, "work_hours": 9},
        domains_covered=["health", "emotions", "career"],
        observation_count=8,
    ))
    state.add_summary(Summary(
        period_type="daily", period_label="2026-02-15",
        content="Sleep dropped to 5.5h. Skipped exercise. Work hours extended to 10h. Mood declined to 5/10.",
        key_insights=["Sleep-exercise-mood all declining together", "Work hours increasing"],
        key_facts={"sleep_hours": 5.5, "mood": 5, "work_hours": 10, "exercise_minutes": 0},
        domains_covered=["health", "emotions", "career"],
        prediction_errors_summary="Elevated error in health/sleep, elevated in emotions/mood",
        observation_count=10,
    ))

    return state


def simulate_llm_response() -> str:
    """Simulate what an LLM would return for a daily review."""
    return json.dumps({
        "observations": [
            {
                "domain": "health",
                "aspect": "sleep",
                "observation": "Sleep dropped to 5h — third consecutive night below expected range",
                "significance": "signal"
            },
            {
                "domain": "health",
                "aspect": "exercise",
                "observation": "No exercise today — second day skipped",
                "significance": "signal"
            },
            {
                "domain": "emotions",
                "aspect": "mood",
                "observation": "Mood at 4/10 — notably below the 6-8 expected range",
                "significance": "signal"
            },
            {
                "domain": "career",
                "aspect": "work_hours",
                "observation": "11h work day, extending the pattern of overwork",
                "significance": "signal"
            }
        ],
        "insights": [
            {
                "description": "Classic burnout triangle emerging: overwork -> poor sleep -> low mood -> skip exercise -> worse sleep.",
                "domains": ["health", "emotions", "career"],
                "confidence": 0.8
            },
            {
                "description": "The product launch deadline is the root cause.",
                "domains": ["career", "health"],
                "confidence": 0.7
            }
        ],
        "decisions": [
            {
                "action": "notify_user",
                "target": "burnout risk",
                "detail": "Surface the cross-domain pattern warmly"
            },
            {
                "action": "store_question",
                "target": "recovery capacity",
                "detail": "Will metrics bounce back after the launch?"
            },
            {
                "action": "update_expectation",
                "target": "health/sleep",
                "detail": "Temporarily expect 5-6h during crunch"
            }
        ],
        "world_model_updates": [
            {
                "domain": "health",
                "aspect": "sleep",
                "new_description": "Currently sleeping 5-6h due to work crunch (normally 7-8h)",
                "new_numeric_value": 5.5,
                "reasoning": "Three consecutive nights of poor sleep"
            }
        ],
        "narrative": "User is deep in a product launch crunch. Sleep, exercise, and mood have all declined as work hours extended to 10-11h/day. The burnout triangle is in full effect.",
        "notifications": [
            {
                "message": "Hey — I've noticed your sleep has dropped to 5h for three nights, you've skipped exercise twice, and your mood is at 4/10. These patterns feed each other. Even 15 minutes of movement or getting to bed 30 minutes earlier could help. What do you think?",
                "urgency": "medium"
            }
        ],
        "dormant_questions": {
            "new": [
                {
                    "question": "Will health metrics recover after the product launch?",
                    "domain": "health",
                    "resolution_signals": ["sleep returns to 7h+ within 1 week of launch"],
                    "context": "Burnout triangle during crunch"
                }
            ],
            "resolved": []
        },
        "summary": {
            "content": "Day 3 of product launch crunch. All health indicators declining: sleep 5h, exercise skipped, mood 4/10. Work hours at 11h. Burnout pattern emerging.",
            "key_insights": [
                "Burnout triangle: overwork -> poor sleep -> low mood -> no exercise",
                "Product launch is root cause"
            ],
            "key_facts": {
                "sleep_hours": 5.0,
                "exercise_minutes": 0,
                "mood": 4,
                "stress": 8,
                "work_hours": 11
            },
            "prediction_errors_summary": "Elevated in health/sleep, health/exercise, emotions/mood"
        }
    }, indent=2)


def demo_manual_pipeline():
    """Demo Part 1: Manual step-by-step pipeline (C1 + C2)."""
    print("=" * 70)
    print("  PART 1: Manual Pipeline (C1 + C2)")
    print("  Step-by-step: observe -> assemble -> prompt -> parse")
    print("=" * 70)

    user = create_demo_user()
    state = create_demo_consciousness_state()
    print(f"\nUser: {user.user_id} | Purpose: {user.purpose_statement[:50]}...")
    print(f"World model: {state.world_model.get_domains()} | Goals: {len(user.get_active_goals())}")

    # Observe
    print("\n--- Hourly Observation (Python math, no LLM) ---")
    today = datetime.now().date().isoformat()
    daily_data = user.get_daily_data(today)
    observations = observe_daily_data(state.world_model, daily_data)
    state.add_observations(observations)
    for obs in observations:
        print(f"  [{obs.severity.upper():>8}] {obs.summary} (error: {obs.prediction_error})")

    # Assemble
    print("\n--- Context Assembly ---")
    assembler = ContextAssembler(state, user_model=user)
    context = assembler.assemble("daily_review")
    print(f"  Sections: {context.section_names}")
    print(f"  Tokens:   {context.token_estimate} / {context.token_budget}")

    # Prompt
    print("\n--- Prompt ---")
    prompt = build_prompt("daily_review", context, user_name="Demo User")
    print(f"  Length: {len(prompt)} chars (~{len(prompt)//4} tokens)")

    # Parse
    print("\n--- Parse (simulated LLM response) ---")
    result = parse_tick_result(simulate_llm_response())
    print(f"  Observations: {len(result.observations)} | Insights: {len(result.insights)}")
    print(f"  Decisions: {len(result.decisions)} | Notifications: {len(result.notifications)}")
    if result.summary:
        print(f"  Summary: {result.summary.content[:80]}...")


def demo_engine():
    """Demo Part 2: Engine orchestrates everything (C3)."""
    print("\n\n" + "=" * 70)
    print("  PART 2: Engine Mode (C3)")
    print("  ConsciousnessEngine runs the full loop in one call")
    print("=" * 70)

    user = create_demo_user()
    state = create_demo_consciousness_state()
    think_fn = create_mock_think_fn(simulate_llm_response())

    engine = ConsciousnessEngine(
        consciousness_state=state,
        user_model=user,
        think_fn=think_fn,
        auto_save=False,  # Don't write to disk in demo
    )

    # Step 1: Hourly observe (pre-attentive, no LLM)
    print("\n--- Hourly Observe ---")
    observations = engine.hourly_observe()
    for obs in observations:
        print(f"  [{obs.severity.upper():>8}] {obs.summary}")

    # Step 2: Daily tick (full LLM cycle)
    print("\n--- Daily Tick (engine.tick_sync) ---")
    result = engine.tick_sync("daily_review")

    if result:
        print(f"  Observations: {len(result.observations)}")
        print(f"  Insights:     {len(result.insights)}")
        print(f"  Decisions:    {len(result.decisions)}")
        print(f"  Notifications:{len(result.notifications)}")

        # Show state was mutated
        print("\n--- State After Tick ---")
        print(f"  Narrative: {state.narrative[:80]}...")
        exp = state.world_model.get_expectation("health", "sleep")
        print(f"  Sleep expectation: {exp.description} (numeric: {exp.numeric_value})")
        print(f"  Pending notifications: {len(state.get_pending_notifications())}")
        print(f"  Dormant questions: {len(state.get_unresolved_questions())}")

        today = datetime.now().date().isoformat()
        summary = state.get_summary_for_period("daily", today)
        if summary:
            print(f"  Today's summary: {summary.content[:80]}...")

        print(f"  Token usage today: ~{state.get_daily_token_usage()} tokens")

        # Show notification content
        pending = state.get_pending_notifications()
        if pending:
            print(f"\n--- Notification for User ---")
            print(f"  {pending[0]['message'][:120]}...")

    print("\n" + "=" * 70)
    print("  ALTER is thinking. Phase C4 will schedule this automatically.")
    print("=" * 70)


def main():
    demo_manual_pipeline()
    demo_engine()


if __name__ == "__main__":
    main()
