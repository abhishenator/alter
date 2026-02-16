# Context Engineering — How ALTER Thinks With Limited Attention

*Design document for ALTER's context assembly, information processing, and memory hierarchy.*

---

## The Core Problem

ALTER's consciousness runs on LLMs. LLMs have finite context windows. But a user's life generates unbounded data — daily observations, weekly patterns, monthly narratives, dormant questions, goals, values. The challenge:

**How do you give an LLM enough context to think deeply about someone's life, without drowning it in irrelevant detail or blowing through token budgets?**

This is ALTER's most important engineering problem. Get context assembly wrong and the system either:
- **Thinks shallowly** (too little context → misses cross-domain patterns)
- **Thinks expensively** (too much context → wasted tokens, noise drowns signal)
- **Forgets** (no summarization → old insights lost, same observations repeated)

The answer is **hierarchical context assembly** — inspired by RAG systems, MemGPT's virtual memory paging, and the human brain's own memory hierarchy.

---

## Design Principles

1. **Summaries over raw data for older periods** — Daily tick reads raw observations. Weekly tick reads daily summaries. Monthly tick reads weekly summaries. Each level compresses ~7x.

2. **Position matters** — LLMs attend more to the beginning and end of context. Place the most important information (current narrative, triggering error) at the start. Place structured output instructions at the end.

3. **Token budgets are hard limits, not guidelines** — Each tick type has a defined context budget. Assembly stops when the budget is hit. Better to include less but stay within budget than to overflow and get truncated.

4. **Approximate on the hot path, exact before the API call** — Use fast character-based estimation (~4 chars = 1 token) during assembly. Count exact tokens only once, right before sending to the LLM.

5. **The LLM does the cognitive work** — Context assembly is about *what* to include. The *thinking* (pattern recognition, hypothesis generation, narrative synthesis) happens in the LLM, not in Python.

6. **Start simple, add complexity only when measured** — No vector databases, no embeddings, no cross-encoders. ALTER's data is small enough for time-ranged reads on structured JSON. Add sophisticated retrieval only when the data outgrows this.

---

## The Memory Hierarchy

Inspired by MemGPT's virtual memory paging and how human memory actually works:

```
┌─────────────────────────────────────────────────────────┐
│  WORKING MEMORY (always in context)                      │
│  - Current narrative thread (~300 tokens)                │
│  - World model expectations (~600 tokens)                │
│  - Active goals (~300 tokens)                            │
│  - Constitution principles (~300 tokens, weekly+ only)   │
│                                                          │
│  ≈ 1,500 tokens — the "who is this person" baseline     │
├─────────────────────────────────────────────────────────┤
│  SHORT-TERM MEMORY (raw, detailed, recent)               │
│  - Raw observations from last 24-48h                     │
│  - Today's daily data                                    │
│  - Recent watch events                                   │
│  - Top 5 dormant questions by readiness                  │
│                                                          │
│  ≈ 500-1,500 tokens — the "what just happened" layer    │
├─────────────────────────────────────────────────────────┤
│  MEDIUM-TERM MEMORY (summarized, compressed)             │
│  - Daily summaries (last 7-30 days)                      │
│  - Weekly summaries (last 4-26 weeks)                    │
│                                                          │
│  ≈ 200-400 tokens per summary — the "what's the trend"  │
├─────────────────────────────────────────────────────────┤
│  LONG-TERM MEMORY (highly compressed, persistent)        │
│  - Monthly summaries (kept forever)                      │
│  - Purpose history                                       │
│  - Personality profile                                   │
│  - Resolved dormant questions (archived)                 │
│                                                          │
│  ≈ Accessed on demand — the "who have they become" layer │
└─────────────────────────────────────────────────────────┘
```

### Why This Mirrors the Brain

| Brain | ALTER | Purpose |
|-------|-------|---------|
| Prefrontal cortex (working memory) | Narrative + world model | Always available, guides attention |
| Hippocampus (recent episodic) | Raw observations, daily data | Detailed, recent, decays |
| Neocortex (consolidated) | Daily/weekly summaries | Compressed patterns, gist |
| Deep memory (identity) | Monthly summaries, purpose | Who you are, rarely changes |

---

## Context Assembly Per Tick Type

Each tick type assembles a different "view" of the user's life. The key insight from RAG systems: **the right context is more important than more context.**

### Hourly Pulse (Pre-attentive Signal Detection)

The hourly tick is a fast filter — like the brain's peripheral nervous system. It detects signals and routes them. No LLM context assembly by default, but critical signals escalate to immediate LLM reasoning via watch events.

```
Read: world_model.numeric_expectations
Read: user.daily_data[today]
Compute: |expected - actual| / expected * confidence
Output: Observation objects with prediction_error scores
If critical (≥0.8): escalate → assemble urgent context → LLM thinks now
```

### Daily Review (~5K total tokens)

The daily tick gets **raw, detailed, recent** context. It's processing today's events.

```
CONTEXT ASSEMBLY                              TOKEN EST
─────────────────                             ─────────

1. WORKING MEMORY (always included)
   ├─ Narrative thread (full)                  ~300
   ├─ World model (all domains)                ~600
   └─ Active goals                             ~300

2. SHORT-TERM MEMORY (today's detail)
   ├─ Today's daily data (raw)                 ~300
   ├─ Queued observations (from hourly ticks)  ~500
   │   (elevated+ errors from last 24h)
   └─ Top 5 dormant questions by readiness     ~300

3. REASONING INSTRUCTIONS                      ~700
   (Observe → Assess → Think → Decide → Narrate)

4. OUTPUT SCHEMA                                ~200
   (TickResult JSON structure)

TOTAL INPUT:  ~3,200 tokens
RESPONSE:     ~1,800 tokens
────────────────────────────
TOTAL:        ~5,000 tokens
```

### Weekly Reflect (~9K total tokens)

The weekly tick gets **compressed summaries** instead of raw observations. This is the hierarchical compression in action.

```
CONTEXT ASSEMBLY                              TOKEN EST
─────────────────                             ─────────

1. WORKING MEMORY
   ├─ Narrative thread (full)                  ~300
   ├─ World model (all domains)                ~600
   ├─ All active goals                         ~500
   └─ Constitution principles summary          ~300

2. MEDIUM-TERM MEMORY (compressed)
   ├─ 7 daily summaries (~200 each)            ~1,400
   │   (NOT raw observations — 7x compression)
   ├─ Weekly data aggregates                    ~500
   └─ All dormant questions                     ~500

3. REASONING INSTRUCTIONS                      ~1,000
   (Cross-domain synthesis, pattern detection)

4. OUTPUT SCHEMA                                ~200
   (TickResult + WeeklySummary)

TOTAL INPUT:  ~5,300 tokens
RESPONSE:     ~3,700 tokens (deeper analysis)
────────────────────────────
TOTAL:        ~9,000 tokens
```

**Without summarization**: 7 days × ~25 observations/day × ~50 tokens = ~8,750 tokens just for observations. Plus working memory. Would exceed 12K easily.

**With summarization**: 7 daily summaries × ~200 tokens = ~1,400 tokens. Same semantic content, 6x compression.

### Monthly Deep (~12K total tokens)

The monthly tick reads **weekly summaries** — compressing an entire month into ~4 summaries.

```
CONTEXT ASSEMBLY                              TOKEN EST
─────────────────                             ─────────

1. WORKING MEMORY
   ├─ Narrative thread (full)                  ~300
   ├─ World model (with history)               ~1,000
   ├─ All goals (with completion history)       ~800
   ├─ Constitution (full)                       ~500
   └─ Purpose history                           ~300

2. LONG + MEDIUM TERM MEMORY
   ├─ 4 weekly summaries (~400 each)           ~1,600
   │   (NOT daily data — 30x compression)
   ├─ 7 recent daily summaries (detail)         ~1,400
   └─ All dormant questions                     ~500

3. REASONING INSTRUCTIONS                      ~1,200
   (Purpose alignment, identity evolution)

4. OUTPUT SCHEMA                                ~300
   (TickResult + MonthlySummary + GoalUpdates)

TOTAL INPUT:  ~7,900 tokens
RESPONSE:     ~4,100 tokens (existential analysis)
────────────────────────────
TOTAL:        ~12,000 tokens
```

### Urgent (~3K total tokens)

Focused and fast. Only what's needed to reason about the triggering error.

```
CONTEXT ASSEMBLY                              TOKEN EST
─────────────────                             ─────────

1. FOCUSED CONTEXT
   ├─ Narrative (current focus only)           ~100
   ├─ World model (triggering domain only)     ~200
   ├─ Triggering observation(s)                ~200
   └─ Related observations (same domain, 3)    ~300

2. REASONING INSTRUCTIONS                      ~400
   (Quick assessment: noise or signal?)

3. OUTPUT SCHEMA                                ~100

TOTAL INPUT:  ~1,300 tokens
RESPONSE:     ~1,700 tokens
────────────────────────────
TOTAL:        ~3,000 tokens
```

---

## Summarization Strategy

### When Summaries Are Produced

Summaries are **natural outputs of LLM ticks**, not a separate job:

```
Daily tick runs → processes hourly observations → produces daily summary
Weekly tick runs → processes daily summaries → produces weekly summary
Monthly tick runs → processes weekly summaries → produces monthly summary
```

Each tick's prompt includes: **"Produce a summary of this period that captures key insights, notable prediction errors, patterns, and factual data. A higher-level tick will read this summary instead of the raw data."**

### What a Good Summary Preserves

Drawing from RAG compression research, summaries must capture:

1. **Key facts** — Quantitative data (averages, counts, trends)
   - "Sleep averaged 5.8h (vs expected 7.5h), mood averaged 4.2/10"

2. **Key insights** — Patterns and connections the LLM discovered
   - "Sleep decline correlates with increased work hours"

3. **Prediction errors** — What surprised the system
   - "Three critical errors in health domain, one elevated in career"

4. **Narrative developments** — How the user's story evolved
   - "Career stress intensifying, approaching deadline"

5. **Dormant question activity** — Questions created or resolved
   - "Created: 'Is this burnout or temporary push?' Resolved: 'Why skipping exercise?'"

6. **Domains covered** — What areas of life were observed
   - ["health", "career", "emotions"]

### What a Good Summary Drops

- Individual observation timestamps (aggregated into "this period")
- Raw numeric data points (replaced with averages/trends)
- Normal-severity observations (only notable ones kept)
- Duplicate patterns (mentioned once, not per-occurrence)

### Preventing Context Collapse

Research shows iterative summarization can erode important details over time (the "telephone game" effect). ALTER's mitigation:

1. **Structured summaries** — Not free-form text. `key_insights`, `key_facts`, `prediction_errors_summary` as separate fields. Structured data resists compression loss.

2. **Recent detail always available** — Monthly tick reads weekly summaries AND the 7 most recent daily summaries. The latest week is never over-compressed.

3. **Facts in `key_facts` dict** — Quantitative data stored as numbers, not prose. Numbers don't degrade through summarization.

4. **Dormant questions persist independently** — They're not embedded in summaries. They have their own storage with resolution signals. Even if a summary loses a nuance, the dormant question retains it.

---

## Compaction — Garbage Collection for Memory

After summarization, raw data that's been compressed is no longer needed in full. The `compact()` method prunes:

```
Retention Policy:
─────────────────
Raw observations:     keep last 48 hours
Daily summaries:      keep last 90 days
Weekly summaries:     keep last 6 months
Monthly summaries:    keep forever (tiny — ~600 tokens each)
Delivered notifications: prune after 7 days
Resolved dormant questions: prune after 30 days
```

Compaction runs after each daily tick. It's fast (list filtering on timestamps) and keeps disk usage bounded.

### Storage Growth Estimate

After 1 year of operation:
- ~365 daily summaries → pruned to 90 → ~18K tokens on disk
- ~52 weekly summaries → pruned to 26 → ~10K tokens on disk
- ~12 monthly summaries → all kept → ~7K tokens on disk
- Raw observations → always capped at last 48h → ~2K tokens
- **Total: ~37K tokens ≈ 150KB JSON**

ALTER's memory footprint stays small indefinitely.

---

## Token Counting Strategy

### Two-Speed Approach

**Fast path (during assembly):**
```python
def estimate_tokens(text: str) -> int:
    """~4 characters per token for English. Fast, ~90% accurate."""
    return len(text) // 4
```

Used during context assembly to check "will this fit?" decisions. Wrong by ±10% is fine here — we have budget headroom.

**Exact path (before API call):**
```python
def count_tokens_exact(text: str, model: str) -> int:
    """Use tiktoken or model-specific tokenizer. 100% accurate."""
    import tiktoken
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))
```

Used once, right before sending to the LLM. If over budget, trim the lowest-priority context section.

### Budget Enforcement

```python
CONTEXT_BUDGETS = {
    "daily_review":    {"input": 3200, "output": 1800},
    "weekly_reflect":  {"input": 5300, "output": 3700},
    "monthly_deep":    {"input": 7900, "output": 4100},
    "urgent":          {"input": 1300, "output": 1700},
}
```

Assembly fills sections in priority order. If budget exceeded, drop lowest-priority section:

```
Priority order (highest → lowest):
1. Narrative thread (identity — always included)
2. Triggering observation/error (why we're thinking)
3. World model expectations (what we believe)
4. Recent observations or summaries (what happened)
5. Dormant questions (subconscious)
6. Goals (what the user wants)
7. Constitution (values — only weekly+)
8. Historical context (purpose history, personality)
```

---

## What We're NOT Building (Yet)

Drawing from lessons learned across RAG, AutoGPT, and MemGPT:

### No Vector Database
ALTER's data is small and structured. Time-ranged reads on JSON are sufficient. AutoGPT removed their vector DB because "agent runs didn't generate enough distinct facts." ALTER generates ~25 observations/day — trivially searchable without embeddings.

**When to add**: If/when skills expansion (calendar, email, web research) generates high-volume unstructured data that outgrows linear search.

### No Semantic Chunking
ALTER doesn't process external documents. Its "chunks" are observations, summaries, and state fields — already semantically bounded by design. No need for sentence-boundary detection or embedding-based splitting.

**When to add**: If/when ALTER gains a "read and understand documents" skill.

### No Cross-Encoder Reranking
With ~25 observations/day and structured queries ("last 24h, elevated+"), there's nothing to rank. The time-range + severity filter IS the retrieval.

**When to add**: If/when the observation log grows to hundreds of entries and relevance scoring becomes necessary.

### No Multi-Agent Context Isolation
ALTER is one mind, not a committee. Context flows through one engine, one state. Research shows 40-80% failure rates in multi-agent systems, with 36.9% of failures from inter-agent misalignment.

**When to add**: If/when skills become complex enough to warrant specialized sub-agents with isolated contexts.

---

## Lessons From Other Systems

### From RAG Systems
- **Position-aware assembly**: Important content at start/end of context. ALTER places narrative first, output schema last.
- **Token budget reservation**: Always reserve 20%+ for model response. ALTER's budgets explicitly allocate input vs output.
- **Start with recursive, not semantic chunking**: ALTER's "chunks" are already semantically bounded (observations, summaries) — no chunking needed.

### From OpenClaw
- **Dual compaction**: Compaction (summarize old history) + pruning (drop old tool results in-memory). ALTER uses similar: summarization for semantic compression, compact() for storage cleanup.
- **Plain text storage**: OpenClaw uses Markdown files. ALTER uses JSON. Both are inspectable, debuggable, greppable. No opaque database.
- **Heartbeat pattern**: OpenClaw's heartbeat checks a checklist. ALTER's hourly pulse is similar — check expectations against reality, act only if something's off.

### From MemGPT/Letta
- **Hierarchical tiers**: Core memory (always in context) → Recall (searchable history) → Archival (long-term). ALTER maps this to: working memory → short-term → medium-term → long-term.
- **Recursive summarization**: Each flush updates the summary. ALTER's daily summary incorporates hourly observations; weekly summary incorporates daily summaries.
- **Agent-managed memory**: MemGPT lets the LLM decide what to store/load. ALTER's LLM ticks produce summaries as natural output — the LLM decides what's worth compressing.

### From LangChain/LangGraph
- **Token-based trimming over count-based**: Don't count messages, count tokens. ALTER uses token budgets, not "include N observations."
- **Approximate counting on hot path**: `trim_messages` uses fast approximation during assembly, exact counting before API call. ALTER follows the same pattern.

### From AutoGPT's Evolution
- **Start simple**: AutoGPT removed their vector DB because it was overkill. ALTER starts with JSON files and time-ranged reads. Add complexity only when measured.
- **File-based storage is fine**: For ALTER's data volume (~150KB/year), JSON files are more than sufficient.

---

## Implementation: `consciousness/context.py` (Phase C2)

The context assembly module translates the design above into code:

```python
# Conceptual structure — not final code

class ContextAssembler:
    """Assembles the right context for each tick type."""

    def assemble(self, tick_type: str, state: ConsciousnessState,
                 user_model: UserModel, constitution: Constitution) -> dict:
        """
        Build context dict for a tick type.

        Returns sections to be inserted into the prompt template.
        Respects token budget. Drops lowest-priority sections if over.
        """
        budget = CONTEXT_BUDGETS[tick_type]["input"]
        sections = {}
        used = 0

        # Priority-ordered assembly
        for section_name, assembler_fn in self.get_section_order(tick_type):
            content = assembler_fn(state, user_model, constitution)
            estimated = estimate_tokens(content)
            if used + estimated <= budget:
                sections[section_name] = content
                used += estimated
            else:
                break  # Budget exceeded, stop adding

        return sections

    def get_section_order(self, tick_type):
        """Return section assemblers in priority order for this tick type."""
        ...
```

Key methods:
- `assemble_narrative()` — Format narrative thread
- `assemble_world_model()` — Format expectations (all domains or specific)
- `assemble_observations()` — Raw observations with time filter
- `assemble_summaries()` — Daily/weekly summaries for higher ticks
- `assemble_goals()` — Active goals, optionally with history
- `assemble_dormant_questions()` — Top N by readiness
- `assemble_constitution()` — Principles summary or full

---

## Open Questions

1. **Summary quality feedback loop**: How do we know if summaries are good? One approach: if a weekly tick repeatedly asks "what happened on Tuesday?" despite having the daily summary, the summary is missing detail. Track this as a signal.

2. **Adaptive budgets**: Should token budgets be fixed or adapt based on "how interesting" a period was? A boring week might need 4K tokens; a crisis week might need 15K. Start fixed, consider adaptive later.

3. **User-injected context**: Users should be able to add notes, corrections, or context that ALTER doesn't observe directly. "I'm going through a breakup" should enter the narrative immediately. This needs a first-class input path, not just daily data fields.

4. **Multi-modal context**: If ALTER gains a journal skill that processes photos or voice notes, how does that content enter the context window? Text descriptions (as RAG research recommends) are probably the right starting approach.

---

*This document is the design spec for `consciousness/context.py` (Phase C2). Implementation follows the principles here. When in doubt, refer back to: "the right context is more important than more context."*
