# LifeOS — System Architecture

## Vision

A meta-cognitive AI system that pays attention to someone's life. It maintains a world model of expectations, detects when reality diverges from those expectations, and thinks about what that means — all autonomously, all governed by a user-defined constitution of values and principles.

The system doesn't wait to be asked. It notices.

## Core Philosophy

- **Approximating the architecture of cognition**: LLMs provide the cognitive substrate. LifeOS provides the meta-architecture — attention, prediction, memory, narrative, values — that turns raw intelligence into a coherent mind.
- **A parallel you**: LifeOS creates an autonomous version of you. It approximates your starting point and helps you evolve. You configure it, command it, override it. It's your agency amplified.
- **Prediction error as the primary trigger**: Thought is triggered by surprise, not by schedule. But the architecture supports extensible triggers — user commands, dormant question readiness, goal deadlines, external events, cascading thought.
- **Constitution-driven**: All autonomous actions filtered through user's ethical/value framework
- **Narrative identity**: One coherent mind, not a collection of disconnected alerts
- **Skills as sense organs**: Each integration expands what the system can perceive

---

## System Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  LAYER 3: RUNTIME ADAPTERS                                          │
│  How it runs. Framework-agnostic core, thin adapters per runtime.   │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │  Standalone       │  │  OpenClaw Plugin  │  │  Future: Mobile │   │
│  │  alter serve      │  │  SKILL.md         │  │  API client     │   │
│  │  APScheduler      │  │  OpenClaw Cron    │  │  Push notifs    │   │
│  │  langchain LLM    │  │  OpenClaw LLM     │  │  App LLM       │   │
│  │  FastAPI + WebUI  │  │  WhatsApp/Discord │  │  Native UI      │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
│                                                                      │
│  ════════════════════════════════════════════════════════════════    │
│                                                                      │
│  LAYER 2: CONSCIOUSNESS ENGINE                                      │
│  How it thinks. The mind. ~950 lines of code.                       │
│                                                                      │
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
│  │                                                                │  │
│  │  ConsciousnessEngine.tick()                                   │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ observe → worth_thinking? → assemble context → LLM call │ │  │
│  │  │ → parse result → constitution check → update state       │ │  │
│  │  │                                                          │ │  │
│  │  │ SNAPSHOT path: scheduled ticks read accumulated state    │ │  │
│  │  │ WATCH path: critical errors trigger immediate thinking   │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ════════════════════════════════════════════════════════════════    │
│                                                                      │
│  LAYER 1: IDENTITY & VALUES                                         │
│  Who it serves. The foundation.                                     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Constitution        UserModel           SystemState           │  │
│  │  (values, ethics,    (goals, purpose,    (decisions, history,  │  │
│  │   principles,         personality,        thought log,         │  │
│  │   intervention        daily data,         missions)            │  │
│  │   triggers)           patterns)                                │  │
│  │                                                                │  │
│  │  Skills                                                        │  │
│  │  (each skill = a new sense organ that expands perception)     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Identity & Values

### Constitution (`core/constitution.py`)

The ethical and value framework governing all system decisions. **Fully customizable** — users define their own principles, life domains, intervention triggers, and guardrails.

See [CONSTITUTION_GUIDE.md](CONSTITUTION_GUIDE.md) for full customization docs.

**Required principles** (cannot be removed):
1. **Autonomy & Agency**: System observes and advises, user decides
2. **Ethical Boundaries**: No harm to self or others
3. **Transparent Reasoning**: Explainable decisions, traceable logic

**Constitution functions:**
- `validate_decision(action, context)` — checks any proposed autonomous action against principles
- `resolve_conflict(goals, constraints)` — when goals compete, uses weighted principles to prioritize
- `check_intervention_triggers(user_state)` — detects conditions that warrant proactive outreach
- `request_override(override)` — allows temporary exceptions (rate-limited, logged)

The constitution is consulted at the end of every inquiry process, before the system takes any autonomous action or surfaces a notification. It is the final filter.

### UserModel (`core/user_model.py`)

The user's identity — who they are, what they want, what their life looks like.

**Key state:**
- Purpose statement (evolving over time, with history)
- Goal hierarchy (life → 5yr → 1yr → quarter → month → week → day)
- Personality traits and preferences
- Strengths and growth areas
- Daily data (mood, energy, sleep, exercise, notes — keyed by date)

The UserModel is the "memory" half of the user representation. The world model (in the consciousness layer) is the "prediction" half. Together they form the system's understanding of the user.

### SystemState (`core/state.py`)

Persistence for everything: decision history, agent states, missions, thought log. JSON on disk at `data/user_data/{user_id}/`.

### Skills (expandable)

Each skill is a **sense organ** that expands what the system can perceive and act on.

```
OBSERVATION SKILLS (feed the observers)
  health_data     — Apple Health, Fitbit, Whoop
  calendar        — Google Calendar
  screen_time     — App usage, browser patterns
  journal_reader  — Parse user's journal entries

INVESTIGATION SKILLS (answer questions during inquiry)
  web_research    — Search the web for information
  data_analysis   — Statistical analysis on user data
  memory_search   — Search past observations and insights

ACTION SKILLS (change the world)
  calendar_modify — Reschedule, block time
  send_reminder   — Push notification, message
  suggest_to_user — Surface insight with recommendation
```

**Adding a skill expands consciousness.** Before the health_data skill exists, the system is blind to health. It has no expectations, no observations, no prediction errors in that domain. Adding the skill is like growing a new sense organ — the system can now notice, think about, and act on health.

---

## Layer 2: Consciousness Engine

The mind. See [CONSCIOUSNESS.md](CONSCIOUSNESS.md) for the full philosophical framework.

### The Core Cycle

The fundamental operation of consciousness:

```
EXPECT ──► OBSERVE ──► SURPRISE? ──► THINK ──► UPDATE
  ▲                                                │
  └────────────────────────────────────────────────┘
```

1. **World Model** maintains expectations about the user's life (sleep patterns, energy rhythms, goal progress, emotional baseline)
2. **Observers** compare reality to expectations, producing **prediction errors**
3. **Attention Gate** filters: is this noise (normal variance) or signal (meaningful change)?
4. **Inquiry Process** (LLM) thinks about significant signals: Frame → Hypothesize → Investigate → Conclude → Decide
5. **Constitution Check** validates any proposed action against user's values
6. **World Model Update** — expectations evolve, narrative updates, dormant questions stored or resolved

### Implementation: Not Classes, Prompts

The cognitive architecture from CONSCIOUSNESS.md (Observers, Attention Gate, Inquiry Process, Narrative Thread) is implemented as **sections of LLM prompts**, not as separate Python classes. The intelligence lives in prompt engineering and state design.

```python
# The consciousness engine in its entirety:
class ConsciousnessEngine:
    def tick(self, tick_type: str):
        raw_errors = self.observe(tick_type)          # Python math — no LLM
        self.state.add_observations(raw_errors)

        if self.worth_thinking(raw_errors, tick_type): # threshold check
            context = self.assemble_context(tick_type)  # select relevant state
            result = self.think(prompt, context)         # LLM call
            self.state.apply(result)                     # update state

        critical = [e for e in raw_errors if e.severity == "critical"]
        if critical:
            self.emit_watch_event(critical)             # urgent → think now
```

### Tick Types — The Multi-Speed Mind

Different aspects of consciousness operate at different speeds, just like the brain.

```
TYPE            FREQUENCY     LLM?    PURPOSE
────            ─────────     ────    ───────

hourly_pulse    every hour    No      Pre-attentive signal detection (Python math).
                                        Queue errors. Escalate to LLM via watch event
                                        when a critical signal is detected.

daily_review    9pm daily     Yes     Review: what happened vs expectations.
                                        Process prediction errors. Update narrative.
                                        Resolve or create dormant questions.

weekly_reflect  Sunday 9pm   Yes     Step back. Cross-domain synthesis.
                                        Connect dots between domains.

monthly_deep    1st of month  Yes     Existential. Purpose alignment.
                                        Is the user becoming who they want to be?

urgent          On-demand     Yes     Triggered by watch event or user command.
                                        Any signal worth immediate reasoning.
```

**Fast loops detect, slow loops think.** The hourly tick is a pre-attentive filter — like the peripheral nervous system detecting signals before the brain consciously processes them. It uses Python math to compare reality to expectations, and escalates significant signals to LLM reasoning via watch events. Daily/weekly/monthly ticks are scheduled conscious reasoning. Any loop can trigger LLM thinking when the situation warrants it.

### Cross-Loop Communication: Snapshot + Watch

How do loops at different speeds share context?

**Snapshot reads (99% of the time):** Each scheduled tick reads accumulated shared state as a time-ranged query. The weekly tick reads "last 7 days of observations" — which includes outputs from all hourly and daily ticks that ran during the week. Cross-domain synthesis happens naturally because the LLM sees all the evidence in one context window.

**Watch events (rare, urgent):** When the hourly Python tick detects a critical prediction error (severity ≥ 0.8), it emits a watch event that triggers immediate LLM thinking, bypassing the schedule.

No event bus. No message queues. No consolidation step. The shared state IS the communication channel.

### Extensible Trigger Mechanisms

Prediction error is the primary trigger today, but the meta-loop is designed to be invoked by multiple mechanisms, each with a different goal:

```
TRIGGER                    GOAL                      PROMPT ADAPTS TO
──────                     ────                      ────────────────
Prediction error           Understand what changed    Observe → Assess → Think
Schedule (daily/weekly)    Review and reflect         Synthesize → Plan → Narrate
Watch event (critical)     Urgent assessment          Quick: noise or signal?
User command               Fulfill direct request     Execute user's intent
Dormant question ready     Resolve subconscious       Focus on the resurfacing question
Goal deadline approaching  Planning                   Break down into tasks
External event (skill)     Process new information     Integrate new data
Cascading thought          Follow-up on prior tick    Deepen or redirect thinking
```

The engine, state, and context assembly stay the same. Only the trigger source and prompt template change. This makes adding new trigger types a matter of adding a prompt template and a trigger registration — not restructuring the core.

### Key Concepts

**World Model** — A set of expectations per life domain. Each expectation has dual representation: numeric value (for Python comparison) and natural language description (for LLM reasoning). Tracks confidence and data points. Low-confidence expectations produce dampened prediction errors — this handles the cold start problem.

**Prediction Error** — `|expected - actual| / expected`, scaled by confidence. The fundamental unit of conscious thought. Only prediction errors above a threshold trigger LLM thinking.

**Narrative Thread** — The unified story of "who is this person, what's happening in their life right now." Included in every LLM prompt. Updated after every thinking cycle. This is what prevents the system from being a collection of disconnected alerts and makes it feel like one coherent mind.

**Dormant Questions** — Unresolved thoughts. "Is the user losing interest in fitness or just going through a busy period?" Stored with resolution signals (what data would answer this). When new observations match those signals, the question resurfaces. This creates the experience of insight emerging over time.

**Constitution Check** — Every autonomous action proposed by the inquiry process is validated against the user's constitution before execution. The system cannot act outside the user's values.

**Hierarchical Memory** — Raw observations compress into daily summaries, which compress into weekly summaries, which compress into monthly summaries. Higher-level ticks read summaries instead of raw data (~20x compression). This keeps context windows bounded while preserving semantic meaning. See [CONTEXT_ENGINEERING.md](CONTEXT_ENGINEERING.md) for the full design.

**User Input** — The system is autonomous but always honors direct user input. Users can inject context ("I'm going through a breakup"), set goals, override decisions, and steer the system's attention. LifeOS is a parallel self that acts on your behalf but takes commands from you.

---

## Layer 3: Runtime Adapters

The consciousness engine is framework-agnostic at its core. It takes a `think_fn: Callable` (any LLM) and state objects. Thin adapters wire it to different runtimes.

### Standalone Mode (`alter serve`)

```
APScheduler          → fires ticks at configured intervals
langchain            → provides think_fn (wraps Claude, GPT-4, etc.)
FastAPI + WebUI      → dashboard, thought stream, goal management
WebSocket            → real-time notifications from watch events
```

### OpenClaw Plugin Mode

```
OpenClaw Cron        → fires ticks via Gateway scheduler
OpenClaw Agent LLM   → provides think_fn (call back into OpenClaw's runtime)
WhatsApp/Discord/etc → delivers notifications via OpenClaw's channel adapters
SKILL.md             → declares tools + cron schedule for auto-discovery
```

LifeOS as an OpenClaw skill gives any OpenClaw instance: autonomous self-reflection, goal-directed behavior, constitution-based decision making, and the ability to notice things the user hasn't mentioned.

### Future: Mobile

REST API already exists. A mobile app connects as a client, receives push notifications from watch events, and provides data input (mood, journal entries).

---

## Data Flow Example

**Scenario: The system notices something the user didn't mention**

```
Tuesday, 10:00 AM — Hourly Pulse

  observe():
    Expected: Normal work routine
    Observed: Browsing job listings for 30 minutes (from screen_time skill)
    Prediction Error: 0.7 (significant — novel behavior)
    Severity: elevated

  → Written to observation log. Queued for daily review.

Tuesday, 9:00 PM — Daily Review

  assemble_context():
    - World model (all domains)
    - Today's data (including the job browsing observation)
    - Narrative: "User in career transition, generally satisfied"
    - Recent journal: mentions of "frustration" up 40% this month
    - Dormant questions: none related to career

  LLM thinks (via prompt):
    OBSERVE: Job browsing is new. Hasn't happened before.
    ASSESS: Signal, not noise. Connects to career goal + frustration pattern.
    THINK: H1=curious, H2=unhappy. Journal + mood data supports H2.
    DECIDE:
      - update_expectation: career_satisfaction → declining
      - store_question: "What specifically is driving dissatisfaction?"
        (resolution signals: user mentions career in journal, goal changes)
      - Don't notify directly — too invasive. Adjust next reflection.

  constitution_check():
    - Autonomy: Yes — not telling user what to do
    - Transparency: Will disclose if asked
    - Ethics: Not acting on private data harmfully

  state.apply():
    - World model updated
    - Dormant question stored
    - Narrative updated: "Career satisfaction may be shifting"

Wednesday, 9:00 PM — Daily Review

  The system's daily prompt, informed by the updated narrative, asks:
    "I noticed you've been working harder than usual lately.
     How are you feeling about work these days?"

  Instead of a robotic "Career metrics changed," the system speaks
  with context — because it's been thinking about this since yesterday.
```

---

## Technology Stack

### Core
- **Python 3.9+**: All application code
- **langchain**: LLM abstraction (for standalone mode)
- **Pydantic**: Data validation and structured output

### Identity Layer
- **JSON file persistence**: `data/user_data/{user_id}/` — simple, portable, local-first
- **YAML**: Constitution definitions

### Consciousness Layer
- **APScheduler**: In-process tick scheduling (standalone mode)
- **Structured JSON output**: LLM returns parsed TickResult via Pydantic

### Web & API
- **FastAPI**: REST API + WebSocket for real-time notifications
- **HTMX + Alpine.js + Tailwind CSS**: Web UI (CDN, no build step)
- **Jinja2**: Server-side templates

### CLI
- **Typer + Rich**: Terminal interface with formatted output

### Future / Optional
- **OpenClaw**: Plugin mode via SKILL.md + tool definitions
- **ChromaDB**: Vector search for memory/observation retrieval (when needed)
- **SQLite**: If JSON files become a bottleneck (WAL mode for concurrency)

---

## File Structure

```
src/alter/
├── core/                           # Layer 1: Identity & Values
│   ├── constitution.py              # Ethics framework, validation, overrides
│   ├── user_model.py                # User identity, goals, purpose, daily data
│   ├── state.py                     # System state, decision log, persistence
│   └── meta_loop.py                 # Legacy cycle logic (being replaced by consciousness engine)
│
├── consciousness/                  # Layer 2: The Mind
│   ├── state.py                     # ConsciousnessState — the shared blackboard
│   ├── engine.py                    # ConsciousnessEngine — tick() is the whole operation
│   ├── observe.py                   # Python-only prediction error math
│   ├── context.py                   # Context assembly per tick type
│   ├── prompts.py                   # Prompt templates — where the cognitive architecture lives
│   ├── parse.py                     # TickResult parsing with fallback
│   └── config.py                    # Tick types, frequencies, thresholds
│
├── adapters/                       # Layer 3: Runtime Adapters
│   ├── standalone.py                # APScheduler + langchain
│   └── openclaw/                    # OpenClaw plugin
│       ├── SKILL.md
│       ├── adapter.py
│       └── tools.py
│
├── skills/                         # Sense Organs (expandable)
│   ├── base.py                      # Skill interface: observe / investigate / act
│   └── ...                          # calendar, health, journal, web_research, etc.
│
├── api/                            # REST API (FastAPI)
│   ├── app.py                       # App factory
│   ├── service.py                   # Service layer
│   ├── models/                      # Pydantic request/response models
│   └── routers/                     # Endpoint groups
│
├── web/                            # Web UI (HTMX + Alpine.js + Tailwind)
│   ├── routes.py                    # HTML page routes + HTMX partials
│   ├── templates/                   # Jinja2 templates
│   └── static/                      # CSS, JS
│
└── cli.py                          # CLI (Typer + Rich)
```

---

## Implementation Phases

### Phase 1: Foundation [COMPLETE]
- Constitution framework
- User model and state management
- Rule-based meta-loop (5-phase cycle)
- CLI, REST API, Web UI

### Phase 2: Consciousness Engine [NEXT]
- World model with expectations and prediction error math
- ConsciousnessState (shared blackboard)
- Context assembly and prompt templates
- LLM integration (first autonomous thinking)
- Standalone adapter (APScheduler)
- Dormant questions and narrative thread

### Phase 3: Skills & Integrations
- Skill interface (observe / investigate / act)
- Calendar, health data, journal integrations
- Each skill expands what the system can perceive

### Phase 4: OpenClaw Plugin
- SKILL.md manifest with tools and cron definitions
- OpenClaw adapter (session → think_fn, watcher → channel delivery)
- LifeOS as an installable consciousness layer for OpenClaw

### Phase 5: Evolution
- Domain-specific sub-agents for deeper investigation
- LangGraph orchestration for parallel agent execution
- Multi-user support
- Mobile app
