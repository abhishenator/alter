# ALTER - Adaptive Life Transformation & Evolution Runtime

## Vision
A meta-cognitive AI system that bridges high-level life purpose with concrete daily actions through autonomous background orchestration, continuous learning, and constitution-based decision making.

## Core Philosophy
- **Meta-cognition first**: System thinks about thinking, plans about planning
- **Constitution-driven**: All decisions filtered through ethical/value framework
- **Parallel intelligence**: Multiple specialized agents working concurrently
- **Continuous evolution**: Daily learning and adaptation based on user growth
- **Proactive companion**: Generates ideas, validates them, guides action

---

## System Architecture

### 1. Meta-Loop (Consciousness Layer)

The central cognitive engine that maintains coherent identity and purpose.

```
┌─────────────────────────────────────────────────────────────┐
│                     META-LOOP CYCLE                          │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   REFLECT    │───▶│   REASON     │───▶│    PLAN      │  │
│  │              │    │              │    │              │  │
│  │ - Life state │    │ - Goals gap  │    │ - Strategies │  │
│  │ - Progress   │    │ - Priorities │    │ - Tasks      │  │
│  │ - Patterns   │    │ - Tradeoffs  │    │ - Delegation │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ▲                                        │           │
│         │                                        ▼           │
│  ┌──────────────┐                      ┌──────────────┐    │
│  │   EVOLVE     │◀─────────────────────│   EXECUTE    │    │
│  │              │                      │              │    │
│  │ - Update model│                     │ - Orchestrate│    │
│  │ - Refine goals│                     │ - Monitor    │    │
│  │ - Learn       │                     │ - Coordinate │    │
│  └──────────────┘                      └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- Maintain user's identity model (purpose, values, personality, goals)
- Generate and refine long-term strategies (1-year, 5-year, life)
- Translate high-level purpose into concrete quarterly/monthly/weekly/daily objectives
- Orchestrate sub-agents with coherent mission alignment
- Synthesize sub-agent reports into actionable insights
- Adapt strategies based on feedback and results

**Key State:**
- Life constitution (user's core values and principles)
- Purpose statement (evolving over time)
- Goal hierarchy (life → 5yr → 1yr → quarter → month → week → day)
- Personality model (traits, preferences, strengths, growth areas)
- Life domains status (health, wealth, relationships, emotions, growth)
- Historical decisions and their outcomes

**Execution Schedule:**
- Deep reflection: Weekly (Sunday evening)
- Strategic planning: Monthly (1st of month)
- Tactical planning: Daily (morning, 6am)
- Progress synthesis: Daily (evening, 9pm)
- Emergency re-planning: On-demand (major life events)

---

### 2. Constitution Layer

The ethical and value framework that governs all system decisions.

**FULLY CUSTOMIZABLE**: Users can define their own constitution from scratch or use default.

**Default Core Principles (Inspired by US Constitution + Science-backed Growth):**

1. **Autonomy & Agency** (Required): System advises, user decides. Preserve free will.
2. **Truth & Evidence**: Decisions based on data, research, proven methods.
3. **Long-term Optimization**: Favor sustainable growth over quick fixes.
4. **Holistic Balance**: Optimize across all life domains, not just one.
5. **Continuous Growth**: Change is constant, adaptation is survival.
6. **Ethical Boundaries** (Required): No harm to self or others. Respect privacy and consent.
7. **Transparent Reasoning** (Required): Explainable decisions, traceable logic.
8. **Empirical Validation**: Test ideas, measure outcomes, iterate.

**User Customization:**
- Full custom constitution: Define your own principles, values, life domains
- Template-based: Start with default/minimalist/spiritual template and modify
- Hybrid: Mix and match from multiple templates
- Override system: Temporarily or permanently override any non-required principle

**Constitution Functions:**
- `load_constitution(user_path=None) -> Constitution`  # Load custom or default
- `validate_decision(action, context) -> (approved: bool, reasoning: str)`
- `resolve_conflict(goals, constraints) -> prioritized_goals`
- `ethical_check(plan) -> (ethical: bool, concerns: list)`
- `apply_override(override_request) -> (approved: bool, logged: bool)`

**See**: `CONSTITUTION_GUIDE.md` for full customization documentation

---

### 3. Sub-Agent Layer

Specialized agents that execute focused tasks in parallel, report findings to meta-loop.

```
┌─────────────────────────────────────────────────────────────────┐
│                        SUB-AGENT NETWORK                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  IDEA AGENT    │  │ RESEARCH AGENT │  │ HEALTH AGENT   │   │
│  │                │  │                │  │                │   │
│  │ - Generate     │  │ - Market scan  │  │ - Track vitals │   │
│  │ - Brainstorm   │  │ - Validate     │  │ - Workout plan │   │
│  │ - Synthesize   │  │ - Trends       │  │ - Nutrition    │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ ACTIVITY AGENT │  │ WEALTH AGENT   │  │RELATION AGENT  │   │
│  │                │  │                │  │                │   │
│  │ - Monitor      │  │ - Finance      │  │ - Contact mgmt │   │
│  │ - Summarize    │  │ - Invest       │  │ - Social cues  │   │
│  │ - Patterns     │  │ - Career       │  │ - Empathy      │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ EMOTION AGENT  │  │  SKILL AGENT   │  │ EXECUTION AGENT│   │
│  │                │  │                │  │                │   │
│  │ - Mood track   │  │ - Learn        │  │ - Task mgmt    │   │
│  │ - Journaling   │  │ - Practice     │  │ - Scheduling   │   │
│  │ - Therapy      │  │ - Mastery      │  │ - Tools (claw) │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Agent Interface (Standardized):**
```python
class SubAgent:
    def receive_mission(self, mission: Mission) -> None
    def execute(self) -> AgentReport
    def get_status(self) -> AgentStatus
    def terminate(self) -> None
```

**Agent Report Structure:**
```python
@dataclass
class AgentReport:
    agent_id: str
    mission_id: str
    status: str  # completed, partial, failed
    findings: dict
    recommendations: list[str]
    evidence: list[Evidence]
    confidence: float
    next_actions: list[str]
    timestamp: datetime
```

**Agent Capabilities:**

Each agent has access to:
- **Knowledge base**: Domain-specific information
- **Tools**: APIs, data sources, analysis functions
- **Memory**: Past executions and learnings
- **OpenClaw integration**: For complex coding/analysis tasks

---

### 4. Data Integration Layer

Ingests and processes data from multiple sources.

**Data Sources:**

1. **Calendar** (Google Calendar API)
   - Meetings, events, time blocking
   - Free/busy analysis
   - Scheduling patterns

2. **Browser** (Browser history export / Screen Time API)
   - Time spent on sites/apps
   - Productivity vs distraction patterns
   - Research topics of interest

3. **Health Data** (Apple Health, Fitbit, Whoop)
   - Sleep quality and duration
   - Exercise and movement
   - Heart rate variability (HRV)
   - Nutrition logging

4. **Phone Apps** (Screen Time, App Usage APIs)
   - App categories and time
   - Notification patterns
   - Focus mode usage

5. **User Input**
   - Daily journal/reflection prompts
   - Manual goal updates
   - Feedback on suggestions
   - Day summary (text or voice)

**Data Pipeline:**
```
Raw Data → Ingestion → Normalization → Enrichment → Storage → Analysis
```

**Privacy & Security:**
- All data stored locally with encryption
- User controls what data is collected
- No data sent to third parties
- Anonymization for any external API calls

---

### 5. Orchestration Engine

Coordinates parallel execution of sub-agents, manages state, handles communication.

**Built with: LangGraph**

**Key Components:**

1. **StateGraph**: Main workflow state machine
2. **Parallel Execution**: Run multiple agents concurrently
3. **Message Passing**: Communication between meta-loop and agents
4. **Checkpointing**: Save/restore system state
5. **Error Handling**: Graceful degradation, retry logic

**Orchestration Patterns:**

```python
# Pattern 1: Fan-out / Fan-in
meta_loop → [agent1, agent2, agent3] → aggregate → meta_loop

# Pattern 2: Sequential with branching
meta_loop → agent1 → decision → {agent2a | agent2b} → meta_loop

# Pattern 3: Continuous monitoring
agent_monitor → (data stream) → event_trigger → meta_loop
```

**State Management:**
```python
@dataclass
class SystemState:
    meta_state: MetaLoopState
    agent_states: dict[str, AgentState]
    missions: list[Mission]
    reports: list[AgentReport]
    user_model: UserModel
    constitution: Constitution
    timestamp: datetime
```

---

### 6. Execution & Skill Layer

Sub-agents can delegate work to specialized tools and systems.

**Available Skills:**

1. **OpenClaw Integration**
   - Complex coding tasks
   - File analysis
   - Git operations
   - Terminal commands

2. **Web Research**
   - Search APIs (Perplexity, Tavily)
   - Content scraping
   - Trend analysis

3. **Data Analysis**
   - Statistical analysis (pandas, numpy)
   - Visualization (matplotlib, plotly)
   - ML/AI (scikit-learn)

4. **Communication**
   - Email drafting
   - Slack/Discord notifications
   - SMS reminders

5. **Task Management**
   - Calendar modifications
   - Todoist/Notion integration
   - Reminder scheduling

**Skill Selection Logic:**
```python
def select_skill(task: Task, context: Context) -> Skill:
    if task.requires_coding:
        return OpenClawSkill()
    elif task.requires_research:
        return WebResearchSkill()
    elif task.requires_analysis:
        return DataAnalysisSkill()
    else:
        return DefaultSkill()
```

---

## System Flow Example

**Scenario: User wants to improve career prospects**

1. **User Input (Morning)**
   ```
   "I want to transition to a senior engineering role in the next 6 months"
   ```

2. **Meta-Loop Processing**
   - Analyzes current career state (from activity data)
   - Breaks down into sub-goals:
     * Build expertise in system design
     * Contribute to open source
     * Network with senior engineers
     * Prepare for interviews
   - Creates missions for sub-agents

3. **Sub-Agent Orchestration (Parallel)**

   **Research Agent:**
   - Mission: "Identify top skills needed for senior roles"
   - Executes: Web research, job posting analysis
   - Reports: "System design (85%), leadership (70%), mentoring (65%)"

   **Skill Agent:**
   - Mission: "Create learning plan for system design"
   - Executes: Find courses, books, practice problems
   - Reports: "Designed Distributed Systems course + 5 case studies"

   **Activity Agent:**
   - Mission: "Analyze current time allocation"
   - Executes: Review calendar and screen time
   - Reports: "15hrs/week available, mostly evenings"

   **Execution Agent:**
   - Mission: "Setup learning environment"
   - Executes: Uses OpenClaw to setup repo, tools
   - Reports: "Repo created, first exercise ready"

4. **Meta-Loop Synthesis (Evening)**
   - Aggregates all reports
   - Creates concrete weekly plan:
     * Mon/Wed/Fri: 2hrs system design study (7-9pm)
     * Tue/Thu: 1hr open source contributions
     * Weekend: 3hrs practice problems
   - Updates calendar with time blocks
   - Sends user summary: "Your path to senior role: 3 focus areas over 24 weeks"

5. **Continuous Monitoring**
   - Activity Agent tracks adherence to plan
   - Health Agent ensures not burning out
   - Emotion Agent monitors motivation levels
   - Meta-loop adjusts plan if falling behind or ahead

6. **Weekly Reflection**
   - Meta-loop asks user: "How did this week feel?"
   - User: "Good progress but evenings are tough after work"
   - Meta-loop: Shifts more to weekends, reduces evening load
   - Constitution check: Still sustainable? Not harming relationships?

---

## Technology Stack

### Core Framework
- **Python 3.11+**: Main language
- **LangGraph**: Orchestration and state management
- **LangChain**: LLM abstractions and tools

### LLM & AI
- **OpenAI GPT-4**: Meta-loop reasoning
- **Claude 3.5 Sonnet** (via API): Sub-agent execution
- **Embeddings**: Text similarity and semantic search

### Data & Storage
- **SQLite**: Local persistent storage
- **ChromaDB**: Vector database for memories
- **Pandas**: Data analysis and manipulation

### Integrations
- **Google Calendar API**: Calendar access
- **Apple HealthKit** (via py-healthkit): Health data
- **Screen Time API**: Activity monitoring
- **OpenClaw SDK**: Coding task delegation

### Infrastructure
- **FastAPI**: REST API for user interface
- **Celery**: Background task scheduling
- **Redis**: Job queue and caching
- **Docker**: Containerized deployment

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Setup project structure
- [ ] Implement constitution framework
- [ ] Build basic meta-loop (without sub-agents)
- [ ] Create user model and state management
- [ ] Simple CLI for interaction

### Phase 2: Meta-Loop Intelligence (Weeks 3-4)
- [ ] Implement full meta-loop cycle (Reflect → Reason → Plan → Execute → Evolve)
- [ ] Goal hierarchy system
- [ ] Decision logging and reasoning traces
- [ ] Constitution validation at each step

### Phase 3: Sub-Agent Layer (Weeks 5-7)
- [ ] Build 3 core agents: Idea, Research, Activity
- [ ] Implement agent interface and communication
- [ ] Parallel execution with LangGraph
- [ ] Report aggregation and synthesis

### Phase 4: Data Integration (Weeks 8-9)
- [ ] Calendar integration
- [ ] Browser/screen time integration
- [ ] Health data integration
- [ ] User input pipeline (journal, prompts)

### Phase 5: Execution Skills (Weeks 10-11)
- [ ] OpenClaw integration
- [ ] Web research capabilities
- [ ] Task management automation
- [ ] Communication skills (email, notifications)

### Phase 6: Polish & Deploy (Weeks 12)
- [ ] Web UI for monitoring and control
- [ ] Mobile notifications
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Self-hosting guide

---

## Success Metrics

**System Level:**
- Meta-loop cycle completion rate (daily, weekly, monthly)
- Sub-agent task success rate
- Decision-to-action latency
- Constitution violation rate (should be 0%)

**User Impact:**
- Goal achievement rate (% of goals completed)
- Life domain balance score (1-10 across 5 domains)
- User engagement (daily interaction frequency)
- Self-reported life satisfaction (weekly survey)

**Technical:**
- System uptime (target: 99%)
- LLM API cost per day
- Processing time per meta-loop cycle
- Data ingestion success rate

---

## Open Questions & Future Considerations

1. **Multi-user**: How to scale to multiple users while maintaining personalization?
2. **Learning**: Can meta-loop improve its reasoning over time without re-training?
3. **Collaboration**: Should users be able to share anonymized strategies/patterns?
4. **Safety**: What guardrails prevent over-optimization or unhealthy obsession?
5. **Explainability**: How to make meta-loop reasoning transparent and debuggable?
6. **Offline mode**: Can system function with degraded capabilities when APIs are down?

---

## File Structure

```
alter/
├── README.md
├── ARCHITECTURE.md (this file)
├── pyproject.toml
├── requirements.txt
├── .env.example
│
├── src/
│   ├── alter/
│   │   ├── __init__.py
│   │   │
│   │   ├── core/
│   │   │   ├── constitution.py      # Constitution framework
│   │   │   ├── meta_loop.py          # Meta-loop implementation
│   │   │   ├── user_model.py         # User identity and goals
│   │   │   └── state.py              # System state management
│   │   │
│   │   ├── agents/
│   │   │   ├── base.py               # Base agent interface
│   │   │   ├── idea_agent.py
│   │   │   ├── research_agent.py
│   │   │   ├── health_agent.py
│   │   │   ├── activity_agent.py
│   │   │   ├── wealth_agent.py
│   │   │   ├── relationship_agent.py
│   │   │   ├── emotion_agent.py
│   │   │   ├── skill_agent.py
│   │   │   └── execution_agent.py
│   │   │
│   │   ├── orchestration/
│   │   │   ├── graph.py              # LangGraph workflow
│   │   │   ├── coordinator.py        # Agent coordination
│   │   │   └── scheduler.py          # Task scheduling
│   │   │
│   │   ├── skills/
│   │   │   ├── base.py
│   │   │   ├── openclaw.py           # OpenClaw integration
│   │   │   ├── web_research.py
│   │   │   ├── data_analysis.py
│   │   │   └── communication.py
│   │   │
│   │   ├── integrations/
│   │   │   ├── calendar.py           # Google Calendar
│   │   │   ├── health.py             # Apple Health
│   │   │   ├── browser.py            # Browser history
│   │   │   └── screen_time.py        # App usage
│   │   │
│   │   ├── data/
│   │   │   ├── ingestion.py
│   │   │   ├── storage.py
│   │   │   └── analysis.py
│   │   │
│   │   └── api/
│   │       ├── server.py             # FastAPI server
│   │       └── routes.py
│   │
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── data/
│   ├── user_data/                    # User-specific data (gitignored)
│   └── system/                       # System data
│
├── config/
│   ├── constitution.yaml             # Constitution definition
│   └── default_goals.yaml
│
└── docs/
    ├── user_guide.md
    ├── api_reference.md
    └── philosophy.md
```

---

## Next Steps

1. Review and approve architecture
2. Define constitution principles in detail
3. Implement Phase 1: Foundation
4. Begin meta-loop development

