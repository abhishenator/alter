# ALTER — Adaptive Life Transformation & Evolution Runtime

ALTER is an autonomous consciousness layer that thinks on your behalf.
It observes your life data, detects patterns, maintains a narrative about
your life, and surfaces insights when they matter.

## Tools

### alter_status
Get the current state of ALTER's consciousness — what it's thinking about,
pending notifications, and open questions.

### alter_reflect
Trigger a conscious thinking cycle. ALTER will review recent data, compare
against expectations, generate insights, and update its understanding.

**Parameters:**
- `tick_type` (string, optional): Type of reflection. One of:
  - `daily_review` (default) — review today's data
  - `weekly_reflect` — synthesize the week's patterns
  - `monthly_deep` — deep identity and purpose review

### alter_observe
Run a quick observation check. ALTER compares current data against its
world model expectations and reports any notable signals. No LLM call —
pure pattern detection.

### alter_narrative
Get ALTER's current narrative — the unified story of your life as ALTER
understands it. This is updated after every thinking cycle.

### alter_questions
Show ALTER's dormant questions — things it's been mulling over that
haven't been resolved yet. Questions accumulate readiness as new data
arrives and are surfaced when they're ready to be answered.

### alter_notify
Deliver any pending notifications from ALTER. These are insights and
observations that ALTER wants to share with you.

## Cron

```cron
# Hourly observation — pre-attentive signal detection (no LLM)
0 * * * *  alter_observe

# Daily review — full conscious thinking cycle
0 22 * * *  alter_reflect --tick_type daily_review

# Weekly reflection — cross-domain synthesis
0 20 * * 0  alter_reflect --tick_type weekly_reflect

# Monthly deep review — identity and purpose
0 10 1 * *  alter_reflect --tick_type monthly_deep
```

## Configuration

ALTER requires:
- A user profile (created on first run)
- Daily life data (health metrics, mood, work hours, etc.)
- Optionally, a constitution (ethical framework and life domains)

Set these environment variables:
- `ALTER_USER_ID` — User identifier (default: "default")
- `ALTER_DATA_DIR` — Data directory (default: "data/user_data")
