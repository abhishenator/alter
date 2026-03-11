# LifeOS Implementation Plan — Consciousness Layer

*Living document. Updated as thinking evolves.*

---

## Project Status (as of Phase 1 + Web UI completion)

### What's Built (Layer 1: Identity & Values)

| Module | File | Lines | Status |
|--------|------|-------|--------|
| Constitution | `src/alter/core/constitution.py` | 591 | Complete — ethics framework, validation, overrides, amendments, interventions |
| UserModel | `src/alter/core/user_model.py` | 396 | Complete — goals, purpose, daily data, personality, basic pattern detection |
| SystemState | `src/alter/core/state.py` | 371 | Complete — decision log, agent states, missions, persistence |
| MetaLoop | `src/alter/core/meta_loop.py` | 738 | Complete — 5-phase cycle (rule-based, no LLM) |
| CLI | `src/alter/cli.py` | 599 | Complete — init, status, cycle, goals, purpose, constitution, serve |
| REST API | `src/alter/api/` | ~500 | Complete — all CRUD endpoints, service layer, Pydantic models |
| Web UI | `src/alter/web/` | ~800 | Complete — dashboard, goals, constitution, daily plan, settings, setup wizard |
| Tests | `tests/unit/` | 56 passing | Constitution (18), UserModel+State (20), MetaLoop (18) |

### What's Stubbed (Empty `__init__.py` Only)

`agents/`, `orchestration/`, `skills/`, `integrations/`, `data/` — all empty.

### What's Missing

- **No LLM calls** — despite langchain/langgraph in deps, all reasoning is hardcoded strings
- **No background processing** — despite Celery/Redis in deps, everything is synchronous
- **No world model** — system stores history but has no expectations/predictions
- **No autonomous thought** — system only acts when human triggers it

---

## The Core Insight

**The consciousness layer is not a complex multi-component system. It is a state machine with one operation:**

```
Read state → Assemble context → Call LLM → Parse output → Update state
```

The components from CONSCIOUSNESS.md (World Model, Observers, Attention Gate, Inquiry Process, Narrative Thread, Dormant Questions) are not separate Python classes that need to communicate. They are **sections of a shared state** that get assembled into **sections of an LLM prompt**. The cognitive work happens inside the LLM, not in Python code.

```
WHAT CONSCIOUSNESS.MD DESCRIBES              WHAT THE CODE ACTUALLY IS
─────────────────────────────────             ──────────────────────────

6 Observer classes with interfaces    →       Different tick frequencies + context depths
Attention Gate scoring system         →       Python threshold (hourly) + prompt section (LLM ticks)
Inquiry Process pipeline              →       Reasoning chain structured in the prompt
Event Bus with queues                 →       Shared state: snapshot reads + watch events
Narrative Thread maintenance          →       A field in state, updated per LLM tick
Token Budget with carryover           →       Context specs per tick type + daily counter
```

**The intelligence lives in state design, context assembly, and prompt engineering — not in software architecture.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  LAYER 3: RUNTIME ADAPTERS (how it runs)                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │  Standalone       │  │  OpenClaw Plugin  │  │  Future: Mobile │   │
│  │  (alter serve)    │  │  (SKILL.md)       │  │  (API client)   │   │
│  │  APScheduler      │  │  OpenClaw Cron    │  │  Push notifs    │   │
│  │  Own LLM (LC)     │  │  OpenClaw LLM     │  │  App LLM       │   │
│  │  FastAPI + WebUI  │  │  WhatsApp/Discord │  │  Native UI      │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
│                                                                      │
│  ════════════════════════════════════════════════════════════════    │
│                                                                      │
│  LAYER 2: CONSCIOUSNESS ENGINE (how it thinks)    ← BUILD NEXT     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │  ConsciousnessState (shared blackboard — JSON on disk)        │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ world_model    │ observations    │ narrative              │ │  │
│  │  │ (expectations) │ (ring buffer)   │ (unified story)        │ │  │
│  │  │                │                 │                        │ │  │
│  │  │ dormant_questions               │ pending_notifications  │ │  │
│  │  │ (subconscious)                  │ (to surface to user)   │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                          │                                     │  │
│  │  ConsciousnessEngine     │                                     │  │
│  │  ┌───────────────────────▼──────────────────────────────────┐ │  │
│  │  │ tick(type) = observe → worth_thinking? → think → update  │ │  │
│  │  │                                                          │ │  │
│  │  │ SNAPSHOT path: scheduled ticks read accumulated state    │ │  │
│  │  │ WATCH path: critical errors trigger immediate thinking   │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ════════════════════════════════════════════════════════════════    │
│                                                                      │
│  LAYER 1: IDENTITY & VALUES (who it serves)       ← EXISTS TODAY   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Constitution     UserModel        SystemState                 │  │
│  │  (values/ethics)  (goals/purpose)  (decisions/history)         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Building Blocks — Definitions

These are the primitives of the consciousness layer.

### Expectation
A prediction about one aspect of the user's life. Has **dual representation**: numeric value (for Python math in hourly ticks) and natural language description (for LLM reasoning).

```python
Expectation:
    domain: str             # "health", "career", "relationships", ...
    aspect: str             # "sleep", "exercise", "mood", ...
    description: str        # "Sleeps 7-8 hours on weeknights" — for LLM
    numeric_value: float    # 7.5 — for Python comparison
    numeric_range: tuple    # (7.0, 8.0) — tolerance band
    data_field: str         # "sleep_hours" — maps to user.daily_data key
    confidence: float       # 0.0-1.0 — scales prediction error
    data_points: int        # Number of observations this is based on
    last_confirmed: str     # ISO timestamp
    last_violated: str      # ISO timestamp
```

### Observation
Result of comparing reality to an expectation. Produced by the observe step (Python math for hourly ticks, LLM reasoning for daily/weekly ticks).

```python
Observation:
    tick_type: str          # "hourly_pulse", "daily_review", etc.
    domain: str             # "health"
    aspect: str             # "sleep"
    expected: str           # "7-8 hours"
    observed: str           # "5 hours"
    prediction_error: float # 0.0-1.0
    severity: str           # "normal" | "elevated" | "critical"
    summary: str            # Human-readable summary
    timestamp: str          # ISO timestamp
    raw_data: dict          # Supporting evidence
```

### Prediction Error
Numeric measure: `|expected - actual| / expected`, scaled by confidence. Range 0-1.

```
Severity thresholds:
    normal:   error < 0.5   → written to observation log, processed on next snapshot
    elevated: 0.5 ≤ error < 0.8 → flagged for daily tick's attention
    critical: error ≥ 0.8   → triggers immediate watch event + LLM thinking
```

### World Model
Dict of domain → expectations. The "what I believe about this person's life right now" layer. Updated after every LLM tick. Includes both predictions AND context (season, upcoming events, recent changes).

### Narrative
The unified story. Current focus, active storylines, unresolved tensions. Updated after every LLM tick. Included in every prompt. This is what makes the system feel like **one mind** instead of a collection of alerts.

### Dormant Question
An unresolved thought. Has `resolution_signals` (what data would answer it), a `readiness` score (increases as signals arrive), and a threshold. When readiness crosses threshold, the question re-enters the next LLM tick as high-priority context.

### Tick
One invocation of the consciousness cycle. Type determines frequency, context depth, and whether LLM is used.

### TickResult
Structured LLM output. Contains: observations, insights, decisions, world model updates, narrative update, dormant question changes, user notifications. Parsed via Pydantic with graceful fallback.

### Watch Event
Urgent trigger from critical prediction error. Bypasses schedule, triggers immediate LLM thinking. Registered watchers (adapters) can react — e.g., send WhatsApp notification.

---

## Cross-Loop Communication: Snapshot + Watch Hybrid

**Resolved: not a pure event bus, not pure shared state. A hybrid.**

### Normal Flow (99% of ticks) — SNAPSHOT

Each scheduled tick reads accumulated shared state as a time-ranged snapshot.

```
Daily tick reads "last 24h of observations" → sees outputs from all hourly ticks.
Weekly tick reads "last 7d of observations" → sees outputs from all hourly + daily ticks.
Monthly tick reads "last 30d" → sees everything.
```

Cross-loop context happens naturally. The weekly tick doesn't need an event from the daily tick — it reads the daily tick's observations from the shared state, sorted by time. The LLM synthesizes cross-domain patterns ("sleep declining + mood dropping + exercise skipped → burnout risk") because it sees all the evidence in one context window.

**No event bus. No queues. No consolidation step. Just time-ranged reads on a shared observation log.**

### Urgent Flow (rare) — WATCH EVENTS

The hourly Python tick detects a critical prediction error (severity > 0.8). Instead of waiting for the next daily tick, it emits a watch event that triggers immediate LLM thinking.

```python
def tick(self, tick_type):
    raw_errors = self.observe(tick_type)
    self.state.add_observations(raw_errors)

    # SNAPSHOT path: scheduled ticks
    if tick_type in ("daily_review", "weekly_reflect", "monthly_deep"):
        context = self.assemble_context(tick_type)  # snapshot read
        result = self.think(self.get_prompt(tick_type), context)
        self.state.apply(result)

    # WATCH path: critical errors → immediate thinking
    critical = [e for e in raw_errors if e.severity == "critical"]
    if critical:
        self.emit_watch_event(critical)

def emit_watch_event(self, critical_errors):
    context = self.assemble_context("urgent", extra=critical_errors)
    result = self.think(self.get_prompt("urgent"), context)
    self.state.apply(result)
    for watcher in self.watchers:
        watcher(critical_errors, result)
```

Watchers are how adapters plug in:
- Standalone: watcher pushes WebSocket notification to web UI
- OpenClaw: watcher sends message to user's WhatsApp/Discord via session

### Why This Works Better Than a Full Event Bus

- **No infrastructure**: No queues, no ordering guarantees, no dead letters
- **No token cost for consolidation**: The LLM consolidates naturally when it sees a week's observations
- **No cascade risk**: Event bus can trigger chain reactions (event → triggers loop → produces more events → triggers more loops). Snapshot reads can't cascade — each tick runs once at its scheduled time.
- **Concurrency is simple**: Last-write-wins with timestamps. Two ticks rarely write the same domain. If they do, next tick self-corrects.
- **Maps to LLM paradigm**: LLMs process context, not events. Snapshot reads produce context directly.

---

## Tick Types — The Multi-Speed Mind

```
TYPE            FREQUENCY     LLM?    CONTEXT         TOKEN EST    PURPOSE
────            ─────────     ────    ───────         ─────────    ───────

hourly_pulse    every hour    No*     Python only     detect       Pre-attentive signal detection.
                                                                    Queue errors. *Escalates to LLM
                                                                    via watch event if critical.

daily_review    9pm daily     Yes     Medium          ~5K          Full review: what happened vs
                                      (24h window)                  expectations. Update narrative.
                                                                    Process dormant questions.

weekly_reflect  Sunday 9pm   Yes     Wide            ~9K          Step back. Cross-domain synthesis.
                                      (7d window)                   Connect dots. Deep narrative update.

monthly_deep    1st of month  Yes     Full            ~12K         Existential. Purpose check.
                                      (30d window)                  Identity evolution. Constitution
                                                                    alignment review.

urgent          On-demand     Yes     Focused         ~3K          Triggered by watch event.
                              (watch)  (error only)                 Fast response to critical error.
```

The hourly tick uses Python math for fast signal detection — like the brain's pre-attentive filters. LLM reasoning is invoked for scheduled review ticks and for urgent watch events. Any tick can escalate to LLM thinking when the situation warrants it.

---

## Context Assembly — The Real Engineering Challenge

Each tick type needs different context depth. Too little → shallow thinking. Too much → token waste + noise.

### Context Specs Per Tick Type

```python
CONTEXT_SPECS = {
    "hourly_pulse": {
        # No LLM context — Python comparison only
        "compare": "user.daily_data vs world_model.expectations"
    },
    "daily_review": {
        "world_model": "all_domains",           # ~600 tokens
        "new_data": "today",                     # ~300 tokens
        "queued_errors": "elevated_from_hourly", # ~200 tokens
        "narrative": "full",                     # ~300 tokens
        "dormant_questions": 5,                  # ~300 tokens (top 5 by readiness)
        "goals": "active",                       # ~300 tokens
        "recent_observations": "last_24h",       # ~500 tokens
        # Total context: ~2500 tokens
    },
    "weekly_reflect": {
        "world_model": "all_domains",            # ~600 tokens
        "observations": "last_7d",               # ~1500 tokens ← cross-loop context!
        "narrative": "full",                     # ~300 tokens
        "dormant_questions": "all",              # ~500 tokens
        "goals": "all",                          # ~500 tokens
        "constitution": "principles_summary",    # ~300 tokens
        "weekly_data_summary": "aggregated",     # ~500 tokens
        # Total context: ~4200 tokens
    },
    "monthly_deep": {
        "world_model": "full_with_history",      # ~1000 tokens
        "observations": "last_30d_summarized",   # ~2000 tokens
        "narrative": "full",                     # ~300 tokens
        "dormant_questions": "all",              # ~500 tokens
        "goals": "all_with_history",             # ~800 tokens
        "constitution": "full",                  # ~500 tokens
        "purpose_history": "full",               # ~300 tokens
        "personality": "full",                   # ~300 tokens
        # Total context: ~5700 tokens
    },
    "urgent": {
        "triggering_error": "the critical observation",  # ~200 tokens
        "relevant_domain": "world_model[error.domain]",  # ~200 tokens
        "narrative": "current_focus",                     # ~100 tokens
        "related_observations": "same_domain_last_3",    # ~300 tokens
        # Total context: ~800 tokens (fast and focused)
    }
}
```

### Key Design Decision: Observers That Fire Often Get LESS Context

```
Hourly:  Pre-attentive (Python signal detection, escalates via watch events when needed)
Daily:   ~5K tokens   (own domain + narrative + goals)
Weekly:  ~9K tokens   (everything from the week — cross-domain synthesis)
Monthly: ~12K tokens  (full life review)
Urgent:  ~3K tokens   (focused on the triggering error)
```

This mirrors the brain: fast reflexes use little information, slow deliberation integrates broadly.

### Cross-Domain Synthesis Via Context Assembly

The "burnout detection" example from CONSCIOUSNESS.md:

```
Weekly tick fires (Sunday 9pm):
  1. Context assembly reads observations from last 7 days:
     - Mon behavioral: "exercise skipped, morning meetings"
     - Tue behavioral: "sleep 5h, lower than expected"
     - Wed emotional: "mood dropped, energy rated 3/10"
     - Thu behavioral: "exercise skipped again"
     - Fri progress: "career goal milestone hit but at extended hours"

  2. ONE LLM call with all 5 observations in context:
     Prompt: "What patterns emerge across these observations?"

  3. LLM naturally synthesizes: "Career progress is happening but at the cost
     of health and emotional well-being. Classic burnout pattern emerging."

  4. No event bus needed. The weekly tick SAW the daily observations
     because they were in the shared state's observation log.
```

---

## World Model — Dual Representation

The world model needs to be **machine-readable** (for Python prediction error math in hourly ticks) AND **natural-language** (for LLM reasoning in daily/weekly ticks).

```python
world_model:
  health:
    expectations:
      sleep:
        description: "Sleeps 7-8 hours on weeknights, 8-9 on weekends"
        numeric_value: 7.5
        numeric_range: [7.0, 8.0]
        data_field: "sleep_hours"          # maps to user.daily_data["sleep_hours"]
        confidence: 0.8
        data_points: 14
      exercise:
        description: "Exercises Mon/Wed/Fri mornings, ~45 min each"
        numeric_value: 3.0                 # times per week
        data_field: "exercise_minutes"
        confidence: 0.7
        data_points: 10
      energy_pattern:
        description: "High energy mornings, dip at 2pm, moderate evenings"
        numeric_value: null                # qualitative — LLM only
        confidence: 0.6
        data_points: 8
    last_prediction_error: 0.3
    last_updated: "2025-03-15T21:00"
    updated_by: "daily_review"

  career:
    expectations:
      goal_pace:
        description: "On track for promotion — 3/5 milestones completed"
        confidence: 0.7
      work_hours:
        description: "Usually 8-9h days, occasional 10h during deadlines"
        numeric_value: 8.5
        numeric_range: [8.0, 9.0]
        data_field: "work_hours"
        confidence: 0.6
    context:
      current_note: "Performance review in 2 weeks — expect elevated focus"

  relationships:
    expectations: { ... }

  emotional:
    expectations: { ... }
    context:
      baseline: "Generally positive, slight stress from deadline"
```

### Cold Start / Bootstrap

New user, zero data. How the world model forms:

```
PHASE 1 — LEARNING (days 0-7):
  World model is empty. No expectations → no prediction errors → no thinking.
  System is transparent: "I'm learning your patterns. Log daily data to help me understand you."

  Each daily data entry BUILDS expectations (not compared to them):
    Day 1: sleep=7   → expectation forming: sleep ≈ 7 (confidence: 0.1, data_points: 1)
    Day 3: sleep=7.5 → expectation adjusting: sleep ≈ 7.2 (confidence: 0.2, data_points: 3)
    Day 7: sleep=[7,7.5,6.5,8,7,7.5,7] → expectation: 7.2 ± 0.5 (confidence: 0.5, data_points: 7)

  Optional bootstrap: ask user 3 questions on init:
    "When do you usually wake up?"
    "What does your exercise routine look like?"
    "What are your top 3 priorities right now?"
  → Seeds world model with stated expectations (confidence: 0.3 — stated, not observed)

PHASE 2 — CALIBRATING (days 7-14):
  Basic expectations exist (confidence: 0.3-0.5).
  Attention threshold is HIGH → only dramatic prediction errors get through.
  System notices big stuff: "You slept 3 hours — very unusual."
  Small deviations ignored (low confidence × small error = below threshold).

PHASE 3 — ACTIVE (day 14+):
  Expectations solidify (confidence: 0.7+).
  Attention threshold normalizes.
  Full consciousness active.

The confidence field naturally handles cold start:
  effective_prediction_error = raw_error × confidence
  → Low confidence dampens errors → attention gate rarely triggers → few tokens spent
```

---

## Prompt Engineering — Where Intelligence Lives

Each tick type has a prompt template that structures the LLM's reasoning. The cognitive architecture from CONSCIOUSNESS.md (Observe → Filter → Hypothesize → Conclude → Decide) becomes **sections of the prompt**.

### Daily Review Prompt (example)

```
You are LifeOS's consciousness, doing your daily review for {user_name}.

## Current Understanding (World Model)
{world_model_all_domains}

## What Happened Today
{today_daily_data}

## Prediction Errors Detected Today (from hourly checks)
{queued_hourly_errors}

## Recent Observations (last 24h)
{recent_observations}

## Current Narrative
{narrative}

## Unresolved Questions
{dormant_questions_top_5}

## Active Goals
{active_goals}

---

Walk through these steps:

1. OBSERVE — What happened today vs what you expected? Note significant matches
   and mismatches. Ignore normal variance.

2. ASSESS — For each mismatch:
   - Is this noise (within expected range) or signal (meaningful deviation)?
   - How does it connect to the user's goals and current narrative?

3. THINK — For significant signals:
   - What might explain this? Generate 1-2 hypotheses.
   - Does this change what you should expect going forward?
   - Does this help resolve any dormant questions?

4. DECIDE — For each insight, choose exactly one:
   - update_expectation: adjust what you expect going forward
   - notify_user: surface this to the user (write a warm, contextual message —
     NOT a robotic alert. Speak like someone who knows them.)
   - store_question: needs more data to resolve (specify resolution signals)
   - resolve_question: this answers a dormant question (reference by ID)
   - no_action: noted but no response needed

5. NARRATE — Update the narrative. What is the current story of this person's
   life? What's the main theme right now? What changed today?

Respond in this JSON structure:
{tick_result_json_schema}
```

### Why Prompt Sections > Python Classes

The "Attention Gate" from CONSCIOUSNESS.md is step 2 of the prompt: "Is this noise or signal?" The LLM filters naturally.

The "Inquiry Process" is step 3: "What might explain this? Generate hypotheses."

The "Narrative Thread" is step 5: "Update the narrative."

No Python classes needed. The cognitive architecture is real — it just lives in prompt structure, not in code.

### Preventing Repetition

The prompt includes `recent_observations`. The LLM sees its own recent history and naturally escalates rather than repeats:

```
Day 1: "Sleep was shorter than usual (5h vs 7-8h expected)"
Day 2: (sees day 1 in observations) "Second night of poor sleep."
Day 3: (sees day 1+2) "Third night. Storing question: temporary stress or routine shift?"
Day 5: (sees pattern + dormant question) "Sleep consistently poor this week. Connected
        to the work deadline narrative. Suggesting to user: 'I've noticed your sleep
        has been off all week — want to talk about what's keeping you up?'"
```

The observation log IS the dedup mechanism. No dedup logic in Python.

---

## Hard Problems — Solved

### 1. Cross-Loop Communication
**Resolved: Snapshot + Watch hybrid.** Normal ticks read accumulated state (snapshot). Critical errors emit watch events for immediate processing. No event bus infrastructure.

### 2. Context Engineering
**Resolved: Tiered context specs.** Each tick type has a defined context budget. Fast ticks get less context (cheaper). Slow ticks get more (deeper). Cross-domain synthesis happens naturally when weekly tick reads the week's observations.

### 3. World Model Bootstrap (Cold Start)
**Resolved: Confidence-gated activation.** New expectations start at low confidence. Prediction errors are scaled by confidence. Low confidence = dampened errors = fewer triggers = minimal token cost for new users. System gradually "wakes up" as data accumulates.

### 4. Concurrency
**Resolved: Not a real problem.** Ticks run at different frequencies (hourly vs daily vs weekly), so simultaneous firing is rare. They write to different state domains. Last-write-wins with timestamps. Python GIL serializes in-process. If needed later, SQLite WAL mode gives read-write concurrency.

### 5. Testing
**Resolved: Layered strategy.**
- State transitions: unit test with mock think_fn (no LLM)
- Context assembly: unit test — assert right data selected per tick type (no LLM)
- Prediction error math: unit test — pure Python arithmetic (no LLM)
- Full tick cycle: integration test with canned LLM responses (mock think_fn)
- Prompt quality: manual review during development
- End-to-end: real LLM against synthetic data, assert structural properties (not exact content)

90% of the system is testable without an LLM.

### 6. Structured Output Reliability
**Resolved: Parse with fallback.** Pydantic validation on LLM JSON output. If parsing fails, extract JSON from markdown code blocks. If that fails, skip this tick (no state modified, next tick will retry). A failed parse is cheap — the system runs continuously.

### 7. Repetition Prevention
**Resolved: Context-based dedup.** The prompt includes recent observations. The LLM sees its own history and naturally escalates ("third day in a row...") instead of repeating. No dedup logic in Python.

---

## Final File Structure

```
src/alter/consciousness/
├── state.py              # ConsciousnessState — the shared blackboard
│                          #   WorldModel, Observation, Narrative, DormantQuestion
│                          #   Ring buffer for observations, JSON persistence
│                          #   ~200 lines
│
├── engine.py             # ConsciousnessEngine — the one operation
│                          #   tick() → observe → worth_thinking? → think → apply
│                          #   Watch event emission + watcher registration
│                          #   ~150 lines
│
├── observe.py            # Python-only observation (hourly tick)
│                          #   Compare user.daily_data fields to world_model expectations
│                          #   Compute numeric prediction errors
│                          #   Classify severity: normal / elevated / critical
│                          #   ~100 lines
│
├── context.py            # Context assembly per tick type
│                          #   CONTEXT_SPECS dict — what state to include per tick
│                          #   Snapshot reads with time-range filtering
│                          #   Token budget awareness
│                          #   ~150 lines
│
├── prompts.py            # Prompt templates — where intelligence lives
│                          #   daily_review, weekly_reflect, monthly_deep, urgent
│                          #   The cognitive architecture (Observe→Assess→Think→Decide→Narrate)
│                          #   ~200 lines
│
├── parse.py              # Output parsing
│                          #   TickResult Pydantic model
│                          #   JSON parsing with fallback
│                          #   Graceful failure handling
│                          #   ~100 lines
│
└── config.py             # Configuration
│                          #   Tick types, frequencies, thresholds, severity levels
│                          #   Loadable from YAML for user customization
│                          #   ~50 lines
│
│  Total: ~950 lines for the entire consciousness layer

src/alter/adapters/
├── standalone.py          # APScheduler + langchain think_fn + WebSocket delivery
│                          #   ~100 lines
└── openclaw/
    ├── SKILL.md           # OpenClaw skill manifest + cron definitions
    ├── adapter.py         # OpenClaw session → think_fn, watcher → channel delivery
    │                      #   ~80 lines
    └── tools.py           # Tool definitions (alter_reflect, alter_plan, etc.)
                           #   ~100 lines
```

---

## Build Phases

### Phase C1: State + World Model + Observe
- `consciousness/state.py` — ConsciousnessState, WorldModel, Observation, Narrative, DormantQuestion
- `consciousness/observe.py` — Python-only prediction error math
- `consciousness/config.py` — tick types, thresholds, severity levels
- Extend `core/state.py` if needed for persistence integration
- **Result: system can have expectations and detect prediction errors (no LLM yet)**

### Phase C2: Context Assembly + Prompts + Parse
- `consciousness/context.py` — CONTEXT_SPECS, snapshot reads, time-range filtering
- `consciousness/prompts.py` — daily_review, weekly_reflect, monthly_deep, urgent templates
- `consciousness/parse.py` — TickResult Pydantic model, JSON parsing
- **Result: context → prompt → structured output pipeline ready (no LLM call yet)**

### Phase C3: Engine + LLM Integration
- `consciousness/engine.py` — ConsciousnessEngine with tick(), watch events, watcher registration
- LLM abstraction: thin wrapper producing `think_fn: Callable[[str, dict], str]`
- Wire to langchain for standalone mode
- **Result: system thinks autonomously for the first time**

### Phase C4: Standalone Adapter
- `adapters/standalone.py` — APScheduler fires ticks, langchain provides think_fn
- Wire into `alter serve` and web UI
- Add thought stream page to web UI
- **Result: `alter serve` runs a conscious system**

### Phase C5: Dormant Questions + Narrative
- Enhance state with dormant question readiness tracking
- Enhance prompts to include dormant question resolution
- Narrative thread carried across ticks
- **Result: system has memory and identity**

### Phase C6: OpenClaw Adapter
- `adapters/openclaw/SKILL.md` — skill manifest with tools + cron
- `adapters/openclaw/adapter.py` — maps OpenClaw session → think_fn
- `adapters/openclaw/tools.py` — tool definitions
- **Result: LifeOS is an installable OpenClaw plugin**

### Phase C7: Skills Expansion
- Each skill = new sense organ
- Calendar → health → journal → web research → finance → ...
- Each skill adds data fields that world model can form expectations about
- **Result: system becomes aware of more life domains**

---

## Design Principles

1. **Approximating the architecture of cognition** — LLMs are the cognitive substrate. LifeOS is the meta-architecture: attention, prediction, memory, narrative, values. Together they approximate how a mind works.
2. **A parallel you** — LifeOS creates an autonomous version of the user that thinks on their behalf, handles mundane tasks, and helps them evolve. The user configures it, commands it, overrides it. Always their agent.
3. **Prediction error as primary trigger, but extensible** — the system thinks because something surprised it, not because a timer fired. But the trigger mechanism is extensible: user commands, dormant question readiness, goal deadlines, external events, and cascading thought can all invoke the meta-loop with different goals and prompts.
4. **Hierarchical memory** — raw observations → daily summaries → weekly summaries → monthly summaries. Higher ticks read compressed context. ~20x compression. See CONTEXT_ENGINEERING.md.
5. **Snapshot + Watch** — normal cross-loop context via time-ranged state reads; urgent interrupts via watch events
6. **LLM does the cognitive work** — observers, attention gate, inquiry, narrative are prompt sections, not Python classes
7. **Framework-agnostic core** — engine takes a `think_fn` callable, doesn't import any framework
8. **Confidence gates activation** — new expectations start low confidence, system gradually "wakes up" as data accumulates
9. **Fast loops detect, slow loops think** — Hourly ticks are pre-attentive signal detection (Python math). Daily/weekly/monthly ticks are conscious reasoning (LLM). But any loop can escalate to LLM thinking via watch events when a signal is significant enough.
10. **Constitution governs all actions** — every autonomous action validated against user's values before execution
11. **Narrative prevents roboticism** — the system speaks like someone who knows you, not a dashboard
12. **User input is first-class** — direct commands, context injection, goal setting, and overrides are always honored. The system is autonomous but obedient.
