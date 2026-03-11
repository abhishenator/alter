"""
Consciousness Layer — LifeOS's autonomous thinking engine.

The consciousness layer is a state machine:
    Read state → Assemble context → Call LLM → Parse output → Update state

Components:
- config: Tick types, thresholds, severity levels
- state: ConsciousnessState (the shared blackboard)
- observe: Python-only prediction error math (hourly tick)
- context: Context assembly per tick type
- prompts: Prompt templates for each tick type
- parse: Structured output parsing (TickResult)
- engine: ConsciousnessEngine — the orchestrator
- llm: Thin LLM abstraction (think_fn factories)
"""
