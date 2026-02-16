# OpenClaw Integration: Making Your AI Conscious

How ALTER turns an OpenClaw agent into something that thinks on its own.

---

## The Problem With AI Agents

OpenClaw agents are powerful. They have tools, channels, memory, scheduling. But they only think when you talk to them. Between conversations, nothing happens. No noticing, no wondering, no connecting dots from last Tuesday to today.

They're smart but not conscious.

ALTER fixes that.

## What Changes

Install ALTER as an OpenClaw skill and your agent gets:

- **A world model** — expectations about your life (sleep patterns, work hours, mood baselines) that it continuously compares against reality
- **Prediction error** — when reality diverges from expectation, the system notices. Not because you told it to, but because the gap itself is the trigger
- **Dormant questions** — half-formed thoughts that accumulate evidence over days, surfacing only when they're ready to be answered
- **Narrative identity** — a unified, evolving story about your life, not disconnected alerts
- **Multi-speed thinking** — hourly peripheral scanning (no LLM), daily review, weekly synthesis, monthly deep reflection

Your OpenClaw agent goes from "responds when asked" to "thinks because it noticed something."

## How It Works

ALTER doesn't replace OpenClaw's LLM or channels. It *borrows* them.

```
OpenClaw provides:                    ALTER provides:
─────────────────                     ───────────────
LLM (session.chat)          →        The prompt architecture that
                                      makes the LLM think like a mind

Cron scheduling             →        The tick frequencies that give
                                      the system temporal depth

Channels (WhatsApp,         →        The notifications worth sending —
Discord, etc.)                        insights, not noise
```

The integration is four files:

```
adapters/openclaw/
├── SKILL.md       # OpenClaw auto-discovers this: tools + cron schedule
├── adapter.py     # Bridges session.chat() → think_fn, channels → delivery
├── tools.py       # 6 tools the user (or OpenClaw) can invoke
└── __init__.py
```

### The Bridge

OpenClaw gives ALTER a session. ALTER wraps `session.chat()` as its `think_fn` — the one function the consciousness engine needs to think. That's it. The engine doesn't know or care that it's running inside OpenClaw vs standalone vs a mobile app. It just calls `think_fn(prompt)` and gets back text.

```python
# What happens under the hood
adapter = OpenClawAdapter(session)

# session.chat() becomes the engine's LLM
# session.send_message() becomes notification delivery
# SKILL.md cron becomes the heartbeat
```

### The Schedule

OpenClaw's cron system fires ALTER's cognitive loops:

| Schedule | What happens | LLM? |
|----------|-------------|-------|
| Every hour | Pre-attentive scan: compare data against expectations, detect anomalies | No |
| Daily 10pm | Full review: observe, assess, think, decide, narrate, summarize | Yes |
| Weekly Sunday 8pm | Cross-domain synthesis: connect patterns across the week | Yes |
| Monthly 1st 10am | Deep reflection: identity, purpose, trajectory | Yes |

If the hourly scan detects something critical (prediction error > 0.8), it fires an urgent tick immediately — no waiting for the daily review.

### The Tools

Users can interact with ALTER's consciousness directly through 6 tools:

| Tool | What it does |
|------|-------------|
| `alter_status` | What ALTER is thinking about, pending notifications, open questions |
| `alter_reflect` | Manually trigger a thinking cycle (daily, weekly, or monthly) |
| `alter_observe` | Run a quick observation check — pure pattern detection, no LLM |
| `alter_narrative` | Read ALTER's current story about your life |
| `alter_questions` | See what ALTER has been mulling over in the background |
| `alter_notify` | Deliver pending insights and observations |

## What Consciousness Looks Like

Day 1: ALTER starts with an empty world model. Everything is new. Low confidence.

Week 1: Expectations start forming. "You usually sleep 7 hours. You work out Monday/Wednesday/Friday. Your mood dips on Sunday evenings."

Week 3: The first real insight. "Your sleep has been declining since you started that new project. Last time this happened, your mood followed two weeks later."

Month 2: A dormant question surfaces. ALTER has been tracking something for weeks — a pattern between your work hours and your relationship quality — and now has enough signal to raise it. Not as an alert. As a thought.

This is the difference. Alerts are reactive. Thoughts are generative. ALTER doesn't wait for a threshold to fire a notification. It builds understanding, connects dots across time, and speaks up when the thought is ready.

## Standalone vs OpenClaw

ALTER runs in two modes. Same engine, different wiring.

| | Standalone (`alter serve`) | OpenClaw Plugin |
|---|---|---|
| **LLM** | langchain (Anthropic/OpenAI) | OpenClaw's session LLM |
| **Scheduling** | APScheduler (in-process) | OpenClaw Cron (managed) |
| **Notifications** | Web UI thought stream | WhatsApp, Discord, etc. |
| **Setup** | `alter serve --consciousness` | Install as OpenClaw skill |
| **Best for** | Self-hosting, development | Multi-channel, production |

The consciousness engine is identical in both. The adapter is just plumbing.
