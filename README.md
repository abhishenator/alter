# LifeOS — Automate Thinking

A life operating system that pays attention to your life. Not a dashboard that tracks you — a companion that notices, thinks, and speaks up at the right moment with the right context.

## What Makes LifeOS Different

Most AI tools wait for you to type a prompt. LifeOS doesn't.

LifeOS maintains a **world model** — a set of predictions about your life (sleep patterns, energy rhythms, goal progress, emotional baseline). When reality doesn't match those predictions, the system **notices**. That gap — the prediction error — is what triggers thought. Not a schedule. Not a timer. A surprise.

A boring day where everything goes as expected? LifeOS stays quiet. A week where your sleep declines, your mood drops, and your exercise disappears? LifeOS connects the dots across domains and says: *"I've noticed things have been off this week. Work has been intense — want to talk about what's happening?"*

It doesn't say that because a cron job fired. It says that because it **noticed**.

## Core Philosophy

- **Approximating the architecture of cognition** — LLMs provide the cognitive substrate (reasoning, logic, knowledge). LifeOS provides the architecture around it: attention, prediction, narrative, memory, values. Together, they approximate how a mind works.
- **A parallel you** — LifeOS creates an autonomous version of you that can think, plan, and notice on your behalf. It approximates your starting point and helps you evolve. But it is always yours — you configure it, you command it, you override it.
- **Prediction error, not self-prompting** — the system thinks because something in the world didn't match what it expected, not because a timer fired
- **Constitution-driven** — all decisions filtered through YOUR ethical/value framework, fully customizable
- **Narrative identity** — one coherent mind, not a collection of disconnected alerts
- **Skills as sense organs** — each integration (calendar, health, journal) expands what the system can notice
- **Privacy-first** — all data stored locally, you control everything

## How It Works

```
WORLD MODEL          What LifeOS expects about your life right now
     │                (sleep ~7h, exercise Mon/Wed/Fri, mood stable...)
     ▼
OBSERVERS            Lightweight checks compare reality to expectations
     │                (Python math — no LLM cost for routine checks)
     ▼
PREDICTION ERROR     When reality doesn't match: how big is the gap?
     │                (sleep 5h vs expected 7h → error = 0.33)
     ▼
ATTENTION GATE       Is this worth thinking about?
     │                (normal variance → ignore. Third bad night → think.)
     ▼
INQUIRY              The LLM thinks: what's going on? what should change?
     │                (Frame → Hypothesize → Investigate → Conclude → Decide)
     ▼
CONSTITUTION         Does this action align with the user's values?
     │                (autonomy, ethics, transparency — always checked)
     ▼
UPDATE               World model evolves. Narrative updates. Maybe notify user.
```

The system maintains a **narrative thread** — a running understanding of who you are and what's happening in your life. This is what makes it feel like talking to someone who knows you, rather than getting alerts from a tracking app.

**Dormant questions** — thoughts the system can't resolve yet — sit in a subconscious store. When new data arrives that might answer them, they resurface. This creates the experience of: *"I've been thinking about this for a while, and now I think I understand..."*

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical design.

```
┌─────────────────────────────────────────────┐
│  CONSCIOUSNESS ENGINE                        │
│                                              │
│  World Model ──► Observers ──► Attention     │
│  (expectations)   (compare)     Gate         │
│       ▲                          │           │
│       │           Dormant        ▼           │
│       │           Questions    Inquiry       │
│       │           (subconscious) │           │
│       │                          ▼           │
│       └──── Narrative ◄── Constitution       │
│             (identity)     (values)          │
├──────────────────────────────────────────────┤
│  IDENTITY LAYER                              │
│  Constitution · UserModel · SystemState      │
├──────────────────────────────────────────────┤
│  RUNTIME ADAPTERS                            │
│  Standalone (alter serve) │ OpenClaw Plugin  │
└─────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
git clone https://github.com/abhishenator/alter.git
cd alter
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
# Add your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)
```

### Choose Your Constitution

```bash
# Use the default constitution
alter init --user-id yourname

# Or customize: start from a template and make it yours
cp config/constitution_template_spiritual.yaml data/user_data/my_constitution.yaml
# Edit to reflect your values, then init
alter init --user-id yourname
```

See [CONSTITUTION_GUIDE.md](CONSTITUTION_GUIDE.md) for full customization.

### Run LifeOS

```bash
# Start the web server (consciousness runs in background)
alter serve

# Open http://localhost:8000
```

The system starts observing, forming expectations, and — once it has enough data to make predictions — thinking autonomously.

### CLI Commands

```bash
# Core
alter init --user-id <name>          # Create your profile
alter serve                          # Start web server + consciousness engine
alter status                         # View current state across life domains

# Goals
alter goal add "Meditate daily" --domain health --horizon month
alter goal list
alter goal complete <goal-id>

# Purpose
alter purpose set "Build products that help people live better"
alter purpose show

# Manual triggers (consciousness also runs these autonomously)
alter cycle                          # Run a full consciousness cycle
alter plan-day                       # Generate today's plan

# Constitution
alter constitution show              # View your principles and domains
alter constitution validate <file>   # Validate a custom constitution
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and technical architecture
- [CONSCIOUSNESS.md](CONSCIOUSNESS.md) — The consciousness layer: first principles, prediction error model, how it thinks
- [CONTEXT_ENGINEERING.md](CONTEXT_ENGINEERING.md) — How LifeOS assembles context, manages memory, and controls token budgets
- [CONSTITUTION_GUIDE.md](CONSTITUTION_GUIDE.md) — How to customize your value framework
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — Current build plan and engineering decisions

## How LifeOS Thinks — An Example

```
Tuesday, 10:00 AM

  Behavioral Observer detects:
    Expected: User follows normal work routine
    Observed: User has been browsing job listings for 30 minutes
    Prediction Error: 0.7 (significant — hasn't happened before)

  Attention Gate scores: HIGH (novel + connects to career goals)

  Inquiry Process:
    Hypotheses:
      H1: Casually curious (low concern)
      H2: Actively unhappy, hasn't verbalized it yet (high concern)

    Investigation:
      - Recent journal: mentions of "frustration" up 40% this month
      - Work patterns: longer hours, fewer breaks
      - Emotional data: slight mood decline over 2 weeks

    Conclusion: H2 most likely.

    Decision: Don't surface directly (too invasive). Instead:
      1. Update world model: career_satisfaction = declining
      2. Store dormant question: "What's driving the dissatisfaction?"
      3. Adjust next reflection to create space for user to express this

  Constitution Check:
    Autonomy: Yes — creating space, not telling user what to do
    Transparency: Will share observation if user asks

  That evening, instead of "How was your day?", the system asks:
    "I noticed you've been working harder than usual lately.
     How are you feeling about work these days?"

  The system was already thinking about it before the user brought it up.
  Not because it was scheduled to. Because it noticed.
```

## Project Status

All core phases (C1–C7) are complete. LifeOS is a fully functional autonomous consciousness system.

- [x] Constitution framework (fully customizable values, overrides, amendments)
- [x] User model (goals, purpose, personality, daily data)
- [x] System state (decision log, persistence)
- [x] Meta-loop (5-phase cycle — rule-based foundation)
- [x] CLI (full command suite)
- [x] REST API (all CRUD endpoints)
- [x] Web UI (warm, elegant light theme — HTMX + Alpine.js + Tailwind)
- [x] Consciousness state layer (world model, observations, prediction error math, summaries, compaction)
- [x] Context assembly + prompt templates (hierarchical memory, token budgets)
- [x] Consciousness engine (LLM integration, autonomous ticks — daily/weekly/monthly/urgent)
- [x] Standalone adapter (APScheduler background thinking via `alter serve`)
- [x] Dormant questions + narrative thread (subconscious memory, identity)
- [x] OpenClaw plugin adapter (6 tools, session protocol, channel delivery)
- [x] Skills expansion (health, calendar, journal — extensible sense organs)
- [x] 307 unit tests passing

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the detailed build plan.

## Philosophy

LifeOS is built on the belief that:

1. **You are autonomous** — the system observes and advises, you decide. It takes commands from you and honors them. It is an extension of your agency, not a replacement.
2. **LLMs are cognitive infrastructure** — they represent humanity's collective reasoning, knowledge, and wisdom. LifeOS doesn't try to make them smarter. It builds the *architecture* — attention, memory, narrative, values — that turns raw cognitive ability into a coherent mind.
3. **Prediction error drives thought** — the system thinks because something surprised it, not because a timer fired
4. **You configure your own evolution** — LifeOS approximates your starting point (values, patterns, goals) and from there helps you grow. Your constitution defines the direction. Your daily inputs steer the course.
5. **Balance is essential** — success in one domain shouldn't harm others
6. **Privacy is sacred** — your data stays yours, always
7. **A companion, not a dashboard** — someone who notices when you're off, remembers what you said last week, connects dots you haven't connected. It helps you plan, handles the mundane, and helps you live more wholly.

## Contributing

Areas of focus:

- Constitution templates (different value systems and life philosophies)
- Skills (new "sense organs" — each integration expands consciousness)
- Observer patterns (better prediction error detection)
- Prompt engineering (the cognitive architecture lives in prompts)

## License

MIT License

---

**Automate thinking. Live deliberately.**
