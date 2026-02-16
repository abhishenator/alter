# ALTER - Adaptive Life Transformation & Evolution Runtime

A meta-cognitive AI system that bridges high-level life purpose with concrete daily actions through autonomous background orchestration, continuous learning, and constitution-based decision making.

## Vision

ALTER is your personal AI companion that:
- 🧠 Maintains a meta-cognitive loop (thinks about thinking, plans about planning)
- 📜 Operates based on YOUR constitution (fully customizable values and principles)
- 🤖 Orchestrates specialized sub-agents working in parallel
- 📊 Integrates your life data (calendar, health, activity, etc.)
- 🎯 Translates life purpose into daily actionable tasks
- 🔄 Learns and evolves with you over time

## Key Features

- **Meta-Loop (Consciousness Layer)**: Continuous cycle of Reflect → Reason → Plan → Execute → Evolve
- **Constitution-Driven**: All decisions filtered through your ethical/value framework
- **Parallel Sub-Agents**: 9 specialized agents (Idea, Research, Health, Activity, Wealth, Relationship, Emotion, Skill, Execution)
- **Data Integration**: Calendar, browser, health data, phone apps, journaling
- **Fully Customizable**: Define your own constitution or use templates
- **Privacy-First**: All data stored locally, encrypted
- **Background Operation**: Runs continuously, generates insights proactively

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/alter.git
cd alter

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# At minimum, add OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### 3. Choose Your Constitution

**Option A: Use Default**
```bash
# Default constitution is ready to use
alter init
```

**Option B: Customize**
```bash
# Copy and customize
cp config/constitution.yaml data/user_data/my_constitution.yaml
# Edit data/user_data/my_constitution.yaml

# Or use a template
cp config/constitution_template_spiritual.yaml data/user_data/my_constitution.yaml
```

See [CONSTITUTION_GUIDE.md](CONSTITUTION_GUIDE.md) for full customization options.

### 4. Run ALTER

```bash
# Start the system
alter start

# Or run in interactive mode
alter interactive
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete system design.

```
┌─────────────────────────────────────────┐
│         META-LOOP (Consciousness)        │
│  Reflect → Reason → Plan → Execute      │
│                ↓                         │
│         CONSTITUTION LAYER               │
│      (Your values & principles)          │
│                ↓                         │
│          SUB-AGENT NETWORK               │
│  [Idea] [Research] [Health] [Activity]  │
│  [Wealth] [Relation] [Emotion] [Skill]  │
│                ↓                         │
│         EXECUTION & SKILLS               │
│  [OpenClaw] [WebResearch] [Analysis]    │
└─────────────────────────────────────────┘
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete system design and technical details
- [CONSTITUTION_GUIDE.md](CONSTITUTION_GUIDE.md) - How to customize your constitution
- `docs/` - Additional guides and API reference

## Usage Examples

### Daily Workflow

```bash
# Morning: Meta-loop generates daily plan
alter morning-briefing

# Throughout day: Activity monitoring runs in background
# Sub-agents execute tasks in parallel

# Evening: Review progress and synthesize insights
alter evening-reflection
```

### Custom Commands

```bash
# Ask for ideas in specific domain
alter generate-ideas --domain=career --count=10

# Run research on topic
alter research "best practices for system design"

# Override constitution temporarily
alter override sleep_hours --duration=3days --reason="Project deadline"

# Activate context mode
alter activate vacation-mode

# Review your constitution
alter constitution show

# Get weekly strategic review
alter weekly-review
```

## Development

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=alter --cov-report=html

# Run specific test file
pytest tests/unit/test_constitution.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Project Status

🚧 **Currently in development** - Phase 1 (Foundation)

- [x] Architecture design
- [x] Constitution framework design
- [x] Project structure
- [ ] Core implementation (constitution loader, state management)
- [ ] Meta-loop implementation
- [ ] Sub-agent framework
- [ ] Data integrations
- [ ] Web UI

See [ARCHITECTURE.md](ARCHITECTURE.md) Phase 1-6 for complete roadmap.

## Philosophy

ALTER is built on the belief that:

1. **You are autonomous**: The system advises, you decide
2. **Purpose matters**: Optimization without meaning is empty
3. **Balance is essential**: Success in one domain shouldn't harm others
4. **Growth is continuous**: Change is constant, adaptation is survival
5. **Privacy is sacred**: Your data stays yours, always

## Contributing

Contributions welcome! Areas of focus:

- Additional constitution templates
- New sub-agent implementations
- Integration connectors (calendar, health, etc.)
- Documentation improvements
- Bug reports and feature requests

## License

MIT License - See LICENSE file for details

## Acknowledgments

Inspired by:
- US Constitution (framework for governance)
- Cognitive psychology (meta-cognition, self-regulation)
- Spiritual traditions (holistic well-being, purpose)
- Modern AI architectures (LangGraph, multi-agent systems)

---

**Built with ❤️ for humans seeking growth, purpose, and balance**
