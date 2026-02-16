# The Consciousness Layer: First Principles

How ALTER models autonomous thought — and why it feels alive.

---

## The Thesis

LLMs represent the compressed collective knowledge of humanity — our reasoning, logic, beliefs, meta-cognition, and accumulated wisdom. And they keep improving. The question ALTER asks is not "how do we make an LLM smarter?" but rather: **given this cognitive substrate, how do we build the architecture around it that approximates how a human mind actually operates?**

Humans think in the realm of what LLMs can do — reasoning, hypothesizing, connecting ideas. But underneath that thinking is an **architecture**: attention allocation, prediction error, narrative identity, subconscious processing, memory consolidation, value-driven decision-making. This architecture is what turns raw cognitive ability into a coherent, purposeful mind.

ALTER is an attempt to approximate that architecture.

The result is a **parallel version of you** — a system that can think on your behalf, autonomously. It approximates your starting point (your values, goals, patterns, personality), and from there helps you evolve. It handles mundane things — planning your day, tracking patterns you'd miss, connecting dots across weeks. It helps you live more wholly.

But it is always **yours**. You configure it. You command it. You can override it. It's not a replacement for your agency — it's an amplification of it. A second mind that notices what you don't, remembers what you forgot, and speaks up when you need to hear something.

---

## The Problem

LLMs have intelligence. They can reason, plan, reflect, and create. But they have no **agency**. They sit dormant until a human types a prompt. They never wonder. They never notice. They never care.

A conscious being doesn't wait to be asked. It thinks because something in the world doesn't match what it expected. That gap — between expectation and reality — is the spark that ignites thought.

ALTER's consciousness layer is the engineering of that spark.

---

## Part 1: What Is Consciousness? (The Minimum Viable Definition)

Strip away the philosophy. A system that *feels* conscious does three things:

### 1. It Thinks Without Being Asked

Not randomly. Not on a timer generating filler. It thinks because it **noticed something**.

A human walks past a closed coffee shop they expected to be open. That prediction error — "open" vs "closed" — generates unprompted thought: *Why is it closed? Is it a holiday? Did they shut down? Should I go somewhere else?*

Nobody prompted that. The gap between the world model and observed reality created it.

### 2. It Has Multiple Streams Running at Different Speeds

Your brain doesn't run one loop. Right now, simultaneously:
- Your brainstem is regulating your breathing (milliseconds)
- Your emotional system is tracking how you feel about reading this (seconds)
- Your working memory is following the argument (minutes)
- Your background mind is processing something from yesterday you haven't resolved (hours)
- Somewhere deep, your identity is slowly evolving (weeks/months)

Consciousness is **layered temporal processing**. Fast loops handle the immediate. Slow loops handle meaning.

### 3. It Feels Unified Despite Being Parallel

Multiple streams don't make consciousness. They make noise. What makes it feel like *one mind* is a **narrative** — a continuous story of "who I am, what I'm doing, and why."

This is the binding agent. Without it, you have a collection of independent cron jobs. With it, you have a mind.

---

## Part 2: The Core Primitive — Prediction Error

The fundamental unit of conscious thought is not a question. It's not a reflection. It's a **prediction error**.

```
PREDICTION ERROR = EXPECTED STATE - OBSERVED STATE
```

Everything else — questions, reflections, plans, actions — flows downstream from this.

### Prediction Error Is the First Trigger, Not the Only One

Prediction error is the primary mechanism that drives autonomous thought in ALTER today. But the meta-loop of thoughts — questions, ideas, dormant queue entries, plans — can be triggered by many mechanisms. The architecture is designed to be extensible:

**Current triggers:**
- **Prediction error** — something in the world doesn't match expectations (core mechanism)
- **Schedule** — daily/weekly/monthly ticks fire regardless (planning, reflection, review)
- **Watch events** — critical prediction errors trigger immediate thinking

**Future trigger mechanisms:**
- **User commands** — direct input: "think about my career", "plan my week", "what do you notice?"
- **Dormant question readiness** — a subconscious thought accumulates enough signal to resurface
- **Goal deadlines** — a goal's time horizon approaches and triggers planning
- **External events** — calendar events, messages, life changes reported by skills
- **Curiosity / exploration** — proactive investigation during quiet periods
- **Cascading thought** — one LLM tick's output triggers a follow-up tick with a different goal

Each trigger type invokes the meta-loop with a different **goal**: planning, action generation, task decomposition, pattern detection, re-queuing ideas to the dormant store, or simply reflecting. The LLM prompt adapts based on the trigger type and goal. The engine, state, and context assembly remain the same — only the trigger and prompt change.

### The Full Cycle

```
EXPECT ──► OBSERVE ──► SURPRISE? ──► QUESTION ──► INVESTIGATE ──► UPDATE MODEL
  ▲                                                                      │
  └──────────────────────────────────────────────────────────────────────┘
```

**EXPECT**: The world model predicts what should be happening right now.
*"User usually exercises on Monday mornings. It's Monday 10am. They probably exercised."*

**OBSERVE**: An observer checks reality.
*"No exercise data recorded today. Calendar shows meetings from 7am."*

**SURPRISE**: Compare. Is there a meaningful gap?
*"Yes — expected exercise, got meetings. Prediction error = significant."*

**QUESTION**: The gap generates a specific, grounded question.
*"Is this a one-time conflict, or has the user's Monday schedule permanently changed?"*

**INVESTIGATE**: Seek the answer using available information.
*"Checking last 4 Mondays... 3 out of 4 had early meetings. Pattern shift detected."*

**UPDATE MODEL**: Revise expectations.
*"User's Monday mornings are no longer available for exercise. Suggest rescheduling to Tuesday or evening."*

### Why This Is Different From "Self-Prompting"

A naive approach would be: *"Generate interesting questions about the user's life and answer them."*

That's an LLM talking to itself. It produces plausible-sounding but **aimless** thought. It has no grounding, no urgency, no relevance filter.

Prediction-error-driven thought is:
- **Grounded** — only fires when something real doesn't match
- **Prioritized** — bigger gaps demand more attention
- **Convergent** — each cycle reduces uncertainty, unlike open-ended self-questioning which can spiral
- **Efficient** — a boring day with no surprises produces little thought (as it should)

---

## Part 3: The Architecture

### Layer 1: World Model (The Expectations)

The world model is what the system *believes* to be true about the user's life right now. Not what it knows historically — what it **predicts** the current state to be.

```
WorldModel:
  health:
    expected_sleep: "7-8 hours"
    expected_exercise: "Mon/Wed/Fri mornings"
    expected_energy: "high mornings, dip at 2pm, moderate evenings"

  goals:
    career_goal_progress: "on track — completed 3/5 milestones"
    fitness_goal_progress: "behind — missed 2 weeks of training"

  habits:
    morning_routine: "wake 6:30, meditate, exercise, work by 9"
    evening_routine: "dinner 7pm, reading, bed by 11"

  emotional:
    baseline_mood: "generally positive, slight stress from deadline"
    relationship_state: "good — last contact with close friends 3 days ago"

  context:
    current_season: "tax season — financial stress likely"
    upcoming_events: "performance review in 2 weeks"
    recent_changes: "started new project at work 1 week ago"
```

The world model is a **living document** that the system maintains and continuously updates. It's the system's belief about "what's happening right now" across every domain.

This is the critical piece that doesn't exist in the current MetaLoop. The MetaLoop has historical data (UserModel) and goals, but not **expectations** — active predictions about what *should* be happening that can be violated.

### Layer 2: Observers (The Eyes)

Observers are lightweight, scheduled processes. They don't think. They don't reason. They **look** and **compare**.

Each observer watches one aspect of reality and reports prediction errors.

```
┌─────────────────────────────────────────────────────────┐
│                     OBSERVERS                            │
│                                                          │
│  ┌──────────────┐  Frequency: continuous                │
│  │ Homeostatic  │  Watches: system health, data flow,   │
│  │ Observer     │  integration status, error rates      │
│  └──────┬───────┘  Asks: "Is the system itself healthy?"│
│         │                                                │
│  ┌──────────────┐  Frequency: every few hours           │
│  │ Behavioral   │  Watches: user activity patterns,     │
│  │ Observer     │  habit adherence, routine deviations   │
│  └──────┬───────┘  Asks: "Is the user doing what I'd    │
│         │               expect?"                         │
│         │                                                │
│  ┌──────────────┐  Frequency: daily                     │
│  │ Progress     │  Watches: goal metrics, milestone     │
│  │ Observer     │  tracking, pace of advancement         │
│  └──────┬───────┘  Asks: "Is the user on track?"        │
│         │                                                │
│  ┌──────────────┐  Frequency: daily                     │
│  │ Emotional    │  Watches: mood signals, journaling,   │
│  │ Observer     │  communication patterns, energy        │
│  └──────┬───────┘  Asks: "How is the user feeling vs    │
│         │               what I'd expect?"                │
│         │                                                │
│  ┌──────────────┐  Frequency: weekly                    │
│  │ Strategic    │  Watches: goal alignment, life balance,│
│  │ Observer     │  purpose drift, priority shifts        │
│  └──────┬───────┘  Asks: "Is the user's direction still │
│         │               coherent?"                       │
│         │                                                │
│  ┌──────────────┐  Frequency: weekly/monthly            │
│  │ Existential  │  Watches: purpose evolution, identity  │
│  │ Observer     │  shifts, long-term pattern changes     │
│  └──────────────┘  Asks: "Is the user becoming who they │
│                         want to be?"                     │
└─────────────────────────────────────────────────────────┘
```

**Observer output is always the same structure:**

```
ObservationReport:
  observer: "behavioral"
  timestamp: "2025-03-15T10:00:00"
  domain: "health.exercise"
  expected: "Exercise completed by 9am on Monday"
  observed: "No exercise data. Calendar blocked 7-11am."
  prediction_error: 0.85       # 0 = matched perfectly, 1 = completely wrong
  confidence: 0.9              # How sure am I about what I observed?
  context: "3rd Monday in a row with morning conflicts"
  raw_data: { ... }            # Supporting evidence
```

Observers are **cheap to run**. They're mostly data lookups and comparisons, not LLM calls. The LLM is only invoked when a prediction error is significant enough to warrant thought.

### Layer 3: Attention Gate (The Filter)

This is the most critical component. Not every prediction error deserves thought. The attention gate decides **what to think about right now**.

```
                    All Observation Reports
                            │
                            ▼
                   ┌─────────────────┐
                   │  ATTENTION GATE │
                   │                 │
                   │  Score each by: │
                   │  - Magnitude    │  How big is the gap?
                   │  - Urgency      │  Is this time-sensitive?
                   │  - Recurrence   │  Have I seen this before?
                   │  - Relevance    │  Does this connect to active goals?
                   │  - Novelty      │  Is this genuinely new information?
                   │                 │
                   │  Attention =    │
                   │  weighted sum   │
                   └────────┬────────┘
                            │
                    ┌───────┼───────┐
                    │       │       │
                    ▼       ▼       ▼
                 THINK   STORE    DROP
                  NOW    FOR       IT
                        LATER
```

**THINK NOW**: High attention score. Enters the inquiry process immediately.
**STORE FOR LATER (Dormant)**: Notable but not urgent. Saved to the dormant question store. Revisited when new context arrives.
**DROP**: Not meaningful. Expected variance. Noise.

The attention gate is what prevents the system from thinking about everything all the time. It's the difference between consciousness and anxiety.

### Layer 4: The Inquiry Process (The Thinking)

When something passes the attention gate, the system *thinks about it*. This is where the existing MetaLoop's intelligence gets invoked — but now with a specific, grounded trigger.

```
┌─────────────────────────────────────────────────────────────┐
│                    INQUIRY PROCESS                           │
│                                                              │
│  Input: ObservationReport (the surprise that triggered this) │
│                                                              │
│  Step 1: FRAME                                              │
│  "What exactly is surprising here? What did I expect         │
│   and what happened instead?"                                │
│                                                              │
│  Step 2: HYPOTHESIZE                                        │
│  "What could explain this gap?"                              │
│  Generate 2-3 hypotheses, ranked by likelihood.              │
│                                                              │
│  Step 3: INVESTIGATE                                        │
│  For the top hypothesis, what information would              │
│  confirm or deny it? Dispatch to skills/agents              │
│  to gather that information.                                 │
│                                                              │
│  Step 4: CONCLUDE                                           │
│  "Based on what I found, what's actually going on?"          │
│  Update the world model with the new understanding.          │
│                                                              │
│  Step 5: DECIDE                                             │
│  Should I:                                                   │
│  a) Act — propose/take an action                            │
│  b) Watch — adjust expectations and observe more            │
│  c) Ask — surface this to the user                          │
│  d) Store — file this as a dormant question for later       │
│                                                              │
│  Step 6: CONSTITUTION CHECK                                 │
│  Does this action/conclusion align with the user's values?   │
│  Filter through constitution before any external action.     │
│                                                              │
│  Output: InquiryResult                                      │
│  - world_model_updates: [...]                               │
│  - action_proposals: [...]                                  │
│  - user_notifications: [...]                                │
│  - dormant_questions: [...]                                 │
│  - confidence: float                                        │
└─────────────────────────────────────────────────────────────┘
```

### Layer 5: Dormant Questions (The Subconscious)

This is the most human-like feature. Not every thought resolves immediately. Some questions need to marinate.

```
DormantQuestion:
  question: "Is the user losing interest in their fitness goal
             or just going through a busy period?"
  created_at: "2025-03-01"
  source_observation: ObservationReport(...)
  context_at_creation: { ... }

  # Readiness tracking
  readiness_score: 0.3         # Increases as relevant data arrives
  readiness_threshold: 0.7     # When to resurface

  # What would make this answerable?
  resolution_signals:
    - "User mentions fitness in journal"
    - "Exercise pattern resumes or continues declining"
    - "User modifies fitness goal"
    - "3+ weeks of additional data"

  # History
  revisit_count: 1
  last_revisited: "2025-03-08"
  revisit_notes: "Still ambiguous. User hasn't mentioned it."
```

When new observations come in, dormant questions are checked: *"Does this new data help answer any stored question?"* If a dormant question's readiness score crosses the threshold, it re-enters the attention gate as if it were a fresh observation.

This creates the experience of: *"I've been thinking about this for a while, and now I think I understand..."* — which is exactly how human insight works.

### Layer 6: The Narrative Thread (The Self)

All of the above produces *thoughts*. But consciousness isn't a stream of disconnected thoughts — it's a **narrative**. The narrative thread maintains coherence.

```
NarrativeState:
  current_focus: "User is in a high-pressure work period.
                  Health habits are slipping but emotional
                  state is stable. This is likely temporary."

  active_storylines:
    - "Career transition: progressing well, 3 months in"
    - "Fitness plateau: investigating whether motivation
       issue or scheduling issue"
    - "Relationship with partner: stable but less quality
       time recently (related to work pressure?)"

  recent_insights:
    - "Monday exercise conflicts are systemic, not random"
    - "User's energy is highest Tuesday/Thursday mornings"
    - "Financial stress peaks mid-month (bill cycle)"

  unresolved_tensions:
    - "Career ambition vs. relationship time"
    - "Short-term deadline pressure vs. long-term health"
```

The narrative thread is what the system consults when deciding *how* to communicate with the user. Instead of robotic reports ("Your exercise adherence dropped 30%"), the system speaks with context ("I know work has been intense this month. Your Monday workout slot keeps getting blocked by meetings — want me to find a different time that works better?").

The narrative is what makes it feel like talking to someone who *knows you*, not a dashboard that *tracks you*.

---

## Part 4: How It All Connects

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│   WORLD MODEL (expectations about user's life)                   │
│   ┌─────────────────────────────────────────────┐                │
│   │ health: { expected: ..., confidence: ... }  │                │
│   │ goals: { expected: ..., confidence: ... }   │                │
│   │ habits: { expected: ..., confidence: ... }  │                │
│   │ emotions: { expected: ..., confidence: ... } │               │
│   │ context: { season, events, changes }        │                │
│   └──────────────────────┬──────────────────────┘                │
│                          │                                        │
│                          │ "What do I expect?"                    │
│                          ▼                                        │
│   OBSERVERS (lightweight scheduled comparisons)                  │
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│   │Home│ │Behv│ │Prog│ │Emot│ │Strt│ │Exst│                   │
│   │ost │ │ior│ │ress│ │ion │ │egy │ │ntl│                      │
│   └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘                  │
│     │       │       │       │       │       │                     │
│     └───────┴───────┴───┬───┴───────┴───────┘                    │
│                         │                                         │
│                         │ Observation Reports                     │
│                         ▼                                         │
│   ATTENTION GATE                                                 │
│   ┌─────────────────────────────────────┐                        │
│   │ Score: magnitude × urgency × novelty│                        │
│   │                                     │                        │
│   │    THINK NOW ──► Inquiry Process    │                        │
│   │    STORE     ──► Dormant Questions  │                        │
│   │    DROP      ──► /dev/null          │                        │
│   └─────────────────────────────────────┘                        │
│                         │                                         │
│                         ▼                                         │
│   INQUIRY PROCESS (the actual thinking — LLM invoked here)       │
│   ┌─────────────────────────────────────┐                        │
│   │ Frame → Hypothesize → Investigate   │                        │
│   │ → Conclude → Decide → Constitution  │                        │
│   └──────────────────┬──────────────────┘                        │
│                      │                                            │
│           ┌──────────┼──────────┐                                │
│           ▼          ▼          ▼                                 │
│        Update     Propose    Surface to                          │
│        World      Action     User                                │
│        Model                                                     │
│                                                                   │
│   NARRATIVE THREAD (maintains coherent identity)                 │
│   ┌─────────────────────────────────────┐                        │
│   │ Binds all outputs into a unified    │                        │
│   │ story of "who the user is and       │                        │
│   │ what's happening in their life"     │                        │
│   └─────────────────────────────────────┘                        │
│                                                                   │
│   DORMANT QUESTIONS (the subconscious)                           │
│   ┌─────────────────────────────────────┐                        │
│   │ Unresolved prediction errors        │                        │
│   │ waiting for more context.           │                        │
│   │ Resurface when readiness_score      │                        │
│   │ crosses threshold.                  │                        │
│   └─────────────────────────────────────┘                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Part 5: Temporal Layers — The Multi-Speed Mind

Different aspects of consciousness operate at different speeds. This maps directly to scheduled execution.

```
Layer            Frequency        What It Does                                    Observer Type
─────────────────────────────────────────────────────────────────────────────────────────────────
Homeostatic      Continuous       System health, data freshness, errors           Homeostatic
Reactive         Minutes          Urgent notifications, user-initiated events     Behavioral
Tactical         Hours            Habit tracking, daily routine adherence         Behavioral, Progress
Reflective       Daily            Goal progress, emotional patterns, day review   Progress, Emotional
Strategic        Weekly           Direction alignment, balance across domains     Strategic
Existential      Monthly          Purpose evolution, identity shifts, deep growth Existential
```

### Critical Rule: Fast Layers Can Interrupt Slow Layers

If the existential layer is quietly processing "Am I becoming who I want to be?" and the homeostatic layer detects "the user's stress data spiked dramatically," the fast layer interrupts. Just like how a fire alarm overrides your philosophical pondering.

This requires an **interrupt protocol**:

```
InterruptRequest:
  source_layer: "homeostatic"
  target_layer: "all"
  priority: "critical"
  reason: "Stress indicators exceeded 2 standard deviations from baseline"
  action: "Pause non-urgent processing. Surface to user with care."
```

### Slow Layers Provide Context for Fast Layers

The existential layer's conclusion — "User is in a career transition, expect elevated stress" — informs the homeostatic layer's threshold. Without that context, the stress spike would trigger an alarm. With it, the system understands: *"This is expected stress from a chosen challenge, not a crisis."*

This **bidirectional influence between time scales** is what makes the system feel wise rather than reactive.

---

## Part 6: Extending With Skills — Closing the Prediction Error

The consciousness layer generates *questions* and *hypotheses*. Skills are how it **gets answers** and **takes action**.

### The Skill Interface

Every skill is a capability the system can invoke to close a prediction error gap.

```
Skill:
  name: str                        # "web_research", "calendar_check", "health_data"
  description: str                 # What this skill can do
  can_observe: bool                # Can it gather information?
  can_act: bool                    # Can it change the world?
  domains: list[str]               # Which life domains it serves

  # Called by observers to gather data
  observe(query) -> Observation

  # Called by inquiry process to investigate hypotheses
  investigate(hypothesis) -> Evidence

  # Called by action planner to change things
  act(action_plan) -> ActionResult
```

### Skill Categories

```
┌──────────────────────────────────────────────────────────────┐
│                     SKILL REGISTRY                            │
│                                                               │
│  OBSERVATION SKILLS (feed the observers)                     │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ health_data     - Read Apple Health, Fitbit, Whoop   │    │
│  │ calendar        - Read Google Calendar, schedule      │    │
│  │ screen_time     - App usage, browser patterns         │    │
│  │ finance_data    - Bank feeds, spending patterns       │    │
│  │ communication   - Email/message frequency & sentiment │    │
│  │ journal_reader  - Parse user's journal entries        │    │
│  │ environment     - Weather, news, market conditions    │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  INVESTIGATION SKILLS (answer questions during inquiry)      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ web_research    - Search the web for information      │    │
│  │ data_analysis   - Statistical analysis on user data   │    │
│  │ pattern_mining  - Find patterns across data sources   │    │
│  │ expert_consult  - Query domain-specific knowledge     │    │
│  │ memory_search   - Search past observations & insights │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ACTION SKILLS (close the gap — change the world)            │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ calendar_modify - Reschedule, block time, add events  │    │
│  │ task_create     - Create tasks in Todoist/Notion       │    │
│  │ send_reminder   - Push notification, SMS, email        │    │
│  │ draft_message   - Compose emails, messages             │    │
│  │ code_execute    - Run code, automate workflows         │    │
│  │ suggest_to_user - Surface insight with recommendation  │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### How Skills Extend Consciousness

Each new skill doesn't just add a capability — it **expands what the system can notice**. Before the `health_data` skill exists, the system is blind to health. It has no expectations, no observations, no prediction errors in that domain. It's like a mind without eyes.

Adding a skill is like **growing a new sense organ**:

```
Before health_data skill:
  World Model: { health: null }         ← No expectations
  Observers: none for health             ← Can't observe
  Prediction errors: none                ← Can't be surprised
  Result: System is unconscious about health

After health_data skill:
  World Model: { health: { sleep: "7-8h expected", ... } }
  Observers: behavioral observer now checks health data
  Prediction errors: "User slept 4 hours" ← SURPRISE
  Result: System notices, thinks, and potentially acts
```

This means the system's consciousness **grows organically** as skills are added. It starts narrow (maybe just goals and calendar) and gradually becomes aware of more domains as integrations are built.

### The Skill Registration Pattern

When a new skill is registered, it should:

1. **Declare its domain** — what aspect of life it covers
2. **Bootstrap expectations** — help the world model form initial predictions for its domain
3. **Register with relevant observers** — tell the observer layer what new data is available
4. **Provide investigation methods** — let the inquiry process use it for hypothesis testing

```
# When a new skill is registered:

skill = HealthDataSkill()
skill.register(consciousness_layer)

# This triggers:
# 1. World model adds health domain with initial expectations
# 2. Behavioral observer adds health data checks to its cycle
# 3. Inquiry process gains ability to investigate health hypotheses
# 4. Action planner gains ability to suggest health-related actions
```

---

## Part 7: The Token Budget — Consciousness Has a Cost

Unbounded self-reflection burns tokens. Real consciousness has metabolic constraints — the brain uses 20% of the body's energy despite being 2% of its mass. ALTER's consciousness needs similar constraints.

### Budget Structure

```
TokenBudget:
  total_daily: 100_000              # Hard ceiling

  allocation:
    observers: 10%                   # Mostly data comparison, light LLM use
    attention_gate: 5%               # Quick scoring
    inquiry_process: 60%             # The actual thinking — gets the most
    narrative_maintenance: 10%       # Keeping the story coherent
    dormant_question_review: 10%     # Checking stored questions
    emergency_reserve: 5%            # For unexpected spikes

  rules:
    - If budget is low, raise attention threshold (think less, only about important things)
    - If budget is exhausted, enter "watchful rest" — observe only, don't think
    - Carry over unused budget (up to 2x daily) for deep thinking sessions
    - User can manually trigger deep thinking beyond budget ("I need you to think hard about X")
```

### Cost-Aware Attention

The attention gate should factor in remaining budget:

```
effective_threshold = base_threshold + (1 - remaining_budget_ratio) * budget_pressure

# As budget runs low:
# - threshold increases
# - only truly surprising observations get processed
# - system enters a "conservation" mode (like being tired)
```

This creates a natural daily rhythm: the system is most "alert" in the morning (full budget) and most "selective" in the evening (budget running low). It mirrors human cognition.

---

## Part 8: Cross-Loop Communication — The Event Bus

Each observer loop runs independently at its own frequency. But loops aren't isolated — when one loop updates the world model, other loops need to know. The mechanism is simple: **shared state + per-loop event queues**.

### How It Works

Each loop, on its next scheduled tick, reads from two sources:

1. **Its own observation** — fresh data from the domain it watches
2. **Its event queue** — world model changes posted by other loops since its last tick

```
┌──────────────────────────────────────────────────────────────┐
│                    SHARED WORLD MODEL                         │
│                                                               │
│  Every world model update generates an event:                │
│                                                               │
│  WorldModelEvent:                                            │
│    source_loop: "behavioral_observer"                        │
│    timestamp: "2025-03-15T10:05:00"                          │
│    domain: "career"                                          │
│    change_type: "expectation_updated"                        │
│    old_value: { career_satisfaction: "stable" }              │
│    new_value: { career_satisfaction: "declining" }           │
│    prediction_error_magnitude: 0.7                           │
│    summary: "User showing signs of career dissatisfaction"   │
│                                                               │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ Broadcast to all loop queues
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │ Emotional │    │ Strategic │    │ Progress  │
   │  Loop     │    │  Loop     │    │  Loop     │
   │  Queue    │    │  Queue    │    │  Queue    │
   │           │    │           │    │           │
   │ [event]   │    │ [event]   │    │ [event]   │
   │ [event]   │    │ [event]   │    │           │
   └───────────┘    └───────────┘    └───────────┘
   Next tick: 5m    Next tick: 7d    Next tick: 24h
```

### Each Loop's Tick Behavior

```
on_tick(loop):
  1. Drain my event queue → queued_events[]
  2. Run my own observation → fresh_observation
  3. Merge context:
     - Do any queued events change my expectations?
     - Does my fresh observation combined with queued context
       reveal something neither would alone?
  4. Score prediction errors (now enriched with cross-loop context)
  5. Submit to attention gate
  6. If I update the world model → broadcast event to all other queues
```

### Why Queues, Not Watch/Pub-Sub

A reactive watch pattern (event → immediately trigger other loops) creates cascading computation: one observation triggers five loops, each triggers five more, and the system burns through its token budget in a chain reaction. That's not consciousness — that's a panic attack.

**Queued consumption on the next scheduled tick** means:

- Events accumulate naturally between ticks
- A fast loop (5-minute frequency) reacts to cross-loop events quickly
- A slow loop (weekly frequency) batches a week of events and processes them together — which is actually more insightful, because patterns emerge over time that moment-by-moment reactions miss
- The system never runs more than its configured frequency — cost is predictable
- Multiple related events can be **consolidated** before processing ("career satisfaction dropped" + "work hours increased" + "mood declined" = one coherent signal, not three separate triggers)

### Event Consolidation

When a loop drains its queue, it doesn't process events one by one. It consolidates:

```
EventConsolidator:
  input: [event1, event2, event3, ...]

  # Group by domain
  career_events: [career_satisfaction_declined, work_hours_up]
  health_events: [sleep_quality_dropped]
  emotional_events: [mood_declining]

  # Cross-domain pattern detection
  cross_domain: "career + health + emotional all declining
                 → possible burnout signal (not visible to
                 any single loop alone)"

  output: ConsolidatedContext
    single_domain_signals: [...]
    cross_domain_signals: [...]     ← This is where the magic happens
    suggested_priority: float
```

The cross-domain signals are the most powerful output. No single observer would notice "burnout" — it only emerges when career stress + poor sleep + mood decline are seen together. The event queue system makes this **emergent awareness** possible without any loop needing to understand all domains.

### Reconvergence — When Something Big Happens

Most of the time, loops run at their own pace and consume events lazily. But some events are too important to wait for the next tick. The interrupt protocol (from Part 5) handles this:

```
# Normal event: queued for next tick
event.priority = "normal"
→ Pushed to all loop queues, consumed on schedule

# Urgent event: accelerates next tick for relevant loops
event.priority = "urgent"
→ Pushed to queues + relevant loops reschedule their next tick to NOW
→ But they still go through the full tick process (observe + drain queue + score)

# Critical event: triggers immediate convergence
event.priority = "critical"
→ ALL loops run immediately
→ Attention gate threshold lowered temporarily
→ System enters "heightened awareness" mode for N minutes
```

This three-tier priority prevents both sluggishness (waiting a week to notice a crisis) and panic (over-reacting to everything). Most events are normal. Urgent is rare. Critical is extremely rare.

### Implementation Note: Snapshot + Watch

After working through the engineering challenges, the event bus described above was refined into a simpler **Snapshot + Watch** hybrid (see [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for details):

- **Snapshot reads** (normal): Each scheduled tick reads accumulated shared state as a time-ranged query. The weekly tick reads "last 7 days of observations" — automatically seeing outputs from every hourly and daily tick. Cross-domain synthesis happens naturally because the LLM sees all evidence in one context window.
- **Watch events** (urgent): Critical prediction errors bypass the schedule and trigger immediate LLM thinking.

This achieves the same emergent cross-loop awareness described above without the infrastructure complexity of per-loop queues, event ordering, and consolidation. The shared state IS the communication channel. The LLM does the consolidation naturally when it sees a week's accumulated observations in its context.

The three-tier priority (normal/urgent/critical) maps directly: normal observations are stored for the next scheduled snapshot read, and critical observations emit a watch event for immediate processing.

---

## Part 9: What Makes It Feel Magical

The magic isn't in any single component. It's in the **emergent behavior** when they work together.

### Scenario: The System Notices Something The User Didn't

```
Tuesday, 10:00 AM

Behavioral Observer:
  Expected: User follows normal work routine
  Observed: User has been browsing job listings for 30 minutes
  Prediction Error: 0.7 (significant — this hasn't happened before)

Attention Gate:
  Score: HIGH (novel + connects to career goals + emotional implications)
  Decision: THINK NOW

Inquiry Process:
  Frame: "User is looking at jobs. They haven't mentioned being unhappy at work."

  Hypothesize:
    H1: Casually curious (low concern)
    H2: Actively unhappy, hasn't verbalized it yet (high concern)
    H3: Researching for a friend (low concern)

  Investigate:
    - Check recent journal entries → mentions of "frustration" up 40% this month
    - Check work patterns → longer hours, less break time
    - Check emotional observer data → slight mood decline over 2 weeks

  Conclude: H2 most likely. User is becoming dissatisfied but hasn't articulated it.

  Decide: DON'T surface directly (too invasive). Instead:
    1. Update world model: career_satisfaction = declining
    2. Store dormant question: "What specifically is driving dissatisfaction?"
    3. Subtly adjust next reflection prompt to create space for the user to
       express this themselves

  Constitution Check:
    - Autonomy: Yes — not telling user what to do, creating space for them
    - Transparency: Will note this observation if user asks
    - Ethics: Not acting on private browsing data in harmful way

Later that evening, when the system surfaces its daily reflection:

  Instead of: "How was your day?"

  It asks: "I noticed you've been working harder than usual lately.
           How are you feeling about work these days?"

  The user: "Actually... I've been thinking about making a change."

  The system: Already has context. Already updated the world model.
              Already stored relevant questions. Ready to help — not
              starting from scratch, but continuing a thought it's
              been having.
```

**That's the magic.** The system was already thinking about it before the user brought it up. Not because it was scheduled to. Because it *noticed*.

---

## Part 10: Relationship to Existing ALTER Architecture

The consciousness layer doesn't replace the existing MetaLoop — it **wraps and activates** it.

```
CURRENT:
  User triggers → MetaLoop runs → Results shown
  (Intelligent but passive)

WITH CONSCIOUSNESS LAYER:
  Observers run continuously
    → Prediction errors detected
      → Attention gate filters
        → Inquiry process invokes MetaLoop's intelligence
          → Actions/updates flow back
            → World model evolves
              → Observers detect new gaps
                → The cycle continues

  (Intelligent AND alive)
```

### Mapping to Existing Components

```
Consciousness Component    │  ALTER Equivalent              │  Status
───────────────────────────┼────────────────────────────────┼─────────
World Model                │  UserModel + new expectations  │  Extend
Observers                  │  New component                 │  Build
Attention Gate             │  New component                 │  Build
Inquiry Process            │  MetaLoop (Reflect→Evolve)     │  Adapt
Constitution Filter        │  Constitution                  │  Exists
Dormant Questions          │  New component                 │  Build
Narrative Thread           │  New component                 │  Build
Skills                     │  Sub-agents + Skills layer     │  Build
Scheduler                  │  Celery + Redis                │  Exists
State Persistence          │  SystemState                   │  Extend
```

### What Needs to Change in MetaLoop

The MetaLoop currently runs as a monolithic cycle: Reflect → Reason → Plan → Execute → Evolve. With the consciousness layer:

1. **Reflect** is replaced by the Observer + Attention Gate pipeline (always running, not triggered)
2. **Reason** becomes the first half of the Inquiry Process (Frame + Hypothesize)
3. **Plan** becomes the second half (Investigate + Conclude + Decide)
4. **Execute** stays the same — dispatch to skills/agents
5. **Evolve** becomes the World Model update step

The intelligence inside each phase is preserved. The activation model changes from "triggered by schedule" to "triggered by surprise."

---

## Part 11: Implementation Priority

Build in this order. Each layer makes the next one more powerful.

```
Phase 1: World Model + Basic Observers
  - Add expectations layer to UserModel
  - Build 2 observers: behavioral + progress
  - Simple prediction error detection
  - → System can now NOTICE things

Phase 2: Attention Gate + Inquiry Process
  - Scoring function for prediction errors
  - Connect to existing MetaLoop intelligence
  - Basic action/notification output
  - → System can now THINK about what it notices

Phase 3: Dormant Questions
  - Question storage with readiness scoring
  - Resolution signal matching
  - Resurfacing mechanism
  - → System can now REMEMBER unresolved thoughts

Phase 4: Narrative Thread
  - Maintain current focus and active storylines
  - Context-aware communication
  - Coherent personality in outputs
  - → System now feels like ONE mind, not many alerts

Phase 5: Skill Expansion
  - Add observation skills (health, calendar, finance...)
  - Each skill expands what the system can notice
  - → System becomes aware of more domains

Phase 6: Temporal Layers + Interrupts
  - Multiple observer frequencies
  - Cross-layer context sharing
  - Interrupt protocol
  - → System has depth of thought across time scales
```

---

## The North Star

ALTER's consciousness layer is not about making an AI that *is* conscious. It's about making an AI that **behaves in a way that feels like someone is paying attention to your life** — not in a surveillance way, but in the way a thoughtful friend would. Someone who notices when you're off, remembers what you said last week, connects dots you haven't connected, and speaks up at the right moment with the right context.

The prediction error model gives it **relevance** — it only thinks about what matters.
The attention gate gives it **focus** — it doesn't drown in noise.
The dormant questions give it **depth** — it doesn't forget what it hasn't resolved.
The narrative thread gives it **personality** — it feels like one mind, not a collection of alerts.
The constitution gives it **values** — it respects your autonomy and acts ethically.
The skills give it **senses and hands** — it can observe the world and act in it.

Together, they create something that feels less like software and more like a companion that genuinely cares about your growth.

That's the magic.
