# Constitution Customization Guide

LifeOS's constitution is fully customizable. You define the principles, values, and rules that govern how the system guides you.

## Philosophy

**Your life, your rules.** The default constitution is a starting point, not a mandate. You can:
- Use it as-is
- Modify it completely
- Start from scratch
- Choose from templates
- Blend multiple approaches

## Required vs Optional Principles

### Required Principles (Cannot be removed, but can be customized)

These three principles are foundational to system integrity:

1. **Autonomy**: Ensures you remain in control
   - Customizable: How the system presents choices
   - Not customizable: That you have final say

2. **Ethics**: Prevents harm
   - Customizable: What you consider harmful
   - Not customizable: System won't enable self-harm

3. **Transparency**: Maintains trust
   - Customizable: Level of detail in explanations
   - Not customizable: System must explain its reasoning

### Optional Principles

Everything else is optional:
- Truth & Evidence
- Long-term Optimization
- Holistic Balance
- Continuous Growth
- Empirical Validation

Add your own:
- Spiritual alignment
- Financial independence
- Creative expression
- Family first
- Adventure and exploration
- Minimalism
- ... anything that matters to you

## Constitution Approaches

### 1. Use Default (Recommended for starting)

Location: `config/constitution.yaml`

Just run the system. Good balanced starting point.

### 2. Template-Based (Easiest customization)

**Step 1**: Copy a template
```bash
cp config/constitution.yaml data/user_data/my_constitution.yaml
# OR
cp config/constitution_template_minimalist.yaml data/user_data/my_constitution.yaml
# OR
cp config/constitution_template_spiritual.yaml data/user_data/my_constitution.yaml
```

**Step 2**: Edit your copy
- Change principle weights (1-10 scale)
- Add/remove rules
- Modify life domains
- Adjust minimum standards
- Customize intervention triggers

**Step 3**: System auto-detects and uses your custom constitution

### 3. Fully Custom (Maximum flexibility)

Create `data/user_data/my_constitution.yaml` from scratch.

**Minimum required structure:**
```yaml
version: "1.0.0"
constitution_type: "custom"

core_principles:
  - id: "autonomy"
    name: "Your Name for Autonomy"
    description: "What autonomy means to you"
    rules:
      - "At least one rule about user control"
    weight: 10

  - id: "ethics"
    name: "Your Name for Ethics"
    description: "Your ethical boundaries"
    rules:
      - "At least one rule about preventing harm"
    weight: 10

  - id: "transparency"
    name: "Your Name for Transparency"
    description: "How you want reasoning explained"
    rules:
      - "At least one rule about explainability"
    weight: 10

# Everything else is optional
```

### 4. Hybrid (Blend templates)

Mix and match from different templates:
- Use default principles but spiritual life domains
- Use minimalist base but add specific principles you care about
- Start with spiritual template but add financial optimization

## Constitution Elements Explained

### Core Principles

```yaml
- id: "unique_identifier"           # Machine-readable ID
  name: "Human-Readable Name"       # What you call it
  description: "Why this matters"   # Your philosophy
  rules:                            # Specific guidelines
    - "Rule 1"
    - "Rule 2"
  weight: 8                         # Priority (1-10, 10 is highest)
```

**Weight matters**: When principles conflict, higher weight wins.

**Example**:
- `autonomy: 10` + `long_term: 8` = User choice > Optimal long-term plan
- System will warn about long-term consequences but respect user decision

### Life Domains

Define what areas of life matter to you:

```yaml
- id: "domain_id"
  name: "Domain Name"
  description: "What this covers"
  metrics:
    - "Metric 1 (unit)"
    - "Metric 2 (unit)"
  minimum_standards:
    metric_key: value
```

**Examples of custom domains:**
- Creative expression (hours creating/week)
- Financial independence (net worth, passive income)
- Adventure (new experiences/month)
- Family connection (quality time with kids)
- Community impact (volunteer hours)
- Spiritual practice (meditation minutes/day)
- Environmental sustainability (carbon footprint)

### Decision Framework

How system resolves conflicts:

```yaml
decision_framework:
  conflict_resolution:
    - "Priority 1 before Priority 2"
    - "Priority 2 before Priority 3"

  risk_assessment:
    acceptable_risk:
      - "Things you're willing to try"
    unacceptable_risk:
      - "Red lines you won't cross"

  validation_gates:
    before_major_decision:
      - "Step 1"
      - "Step 2"
```

### Intervention Triggers

When system should proactively alert you:

```yaml
intervention_triggers:
  immediate_intervention:
    - condition: "When this happens"
      action: "System does this"

  weekly_intervention:
    - condition: "Weekly check for this"
      action: "Raise in weekly reflection"
```

**Examples:**
- `condition: "No creative work for 7 days"` → `action: "Reminder: schedule creative time"`
- `condition: "Spending > budget for 3 months"` → `action: "Financial review needed"`
- `condition: "No family time for 5 days"` → `action: "Schedule family activity"`

### Guardrails

Safety mechanisms:

```yaml
guardrails:
  - id: "guardrail_id"
    description: "What this prevents"
    rules:
      - "Specific rule"
      - "Another rule"
```

**Use cases:**
- Prevent workaholism
- Ensure minimum self-care
- Protect relationships
- Maintain work-life boundaries
- Prevent financial recklessness

### Override System

Control how you can override your own rules:

```yaml
override_system:
  override_limits:
    temporary_overrides_per_month: 8
    concurrent_active_overrides: 3
    blocked_overrides:
      never_override:
        - "principle_id/rule_id"
```

**Conservative approach**: Lock down most overrides
**Liberal approach**: Allow overriding almost anything
**Balanced**: Default settings

## Templates Reference

### Default Template
**Best for**: Balanced life optimization, general users

**Focus areas**:
- Health & wellness
- Wealth & career
- Relationships
- Emotional well-being
- Personal growth

**Philosophy**: Science-backed, evidence-driven, holistic balance

**File**: `config/constitution.yaml`

---

### Minimalist Template
**Best for**: Users who want minimal system interference

**Focus areas**:
- User defines their own domains
- Minimal intervention
- Maximum freedom

**Philosophy**: Light touch, user-driven, almost no guardrails

**File**: `config/constitution_template_minimalist.yaml`

---

### Spiritual/Purpose-Driven Template
**Best for**: Users prioritizing meaning, growth, spiritual development

**Focus areas**:
- Spiritual practice & connection
- Purpose & contribution
- Deep relationships
- Embodiment (mindful physical care)
- Joy & fulfillment
- Learning & becoming

**Philosophy**: Purpose over productivity, presence over performance, being before doing

**File**: `config/constitution_template_spiritual.yaml`

---

## Real-World Examples

### Example 1: Entrepreneur Constitution

```yaml
core_principles:
  - id: "autonomy"
    name: "Independence"
    rules: ["I make final decisions"]
    weight: 10

  - id: "growth"
    name: "Rapid Growth & Scaling"
    description: "Build and scale businesses"
    rules:
      - "Prioritize revenue-generating activities"
      - "Optimize for speed of learning"
      - "Take calculated risks"
    weight: 9

  - id: "leverage"
    name: "Maximum Leverage"
    description: "Do more with less"
    rules:
      - "Automate everything possible"
      - "Delegate non-core work"
      - "Build systems, not just execute tasks"
    weight: 9

life_domains:
  - id: "business"
    metrics:
      - "Revenue ($/month)"
      - "Customer acquisition"
      - "Product launches"
    minimum_standards:
      revenue_growth_mom: 10  # 10% month over month
```

### Example 2: Parent Constitution

```yaml
core_principles:
  - id: "family_first"
    name: "Family Above All"
    description: "Kids and partner are priority #1"
    rules:
      - "Never miss important family moments for work"
      - "Present time with family > distracted time"
      - "Model values I want kids to learn"
    weight: 10

life_domains:
  - id: "parenting"
    metrics:
      - "Quality time with each child (hours/week)"
      - "Family meals together (count/week)"
      - "Special 1-on-1 time per child (hours/week)"
    minimum_standards:
      quality_time_per_child: 7
      family_meals: 5
      one_on_one_time: 2

intervention_triggers:
  immediate_intervention:
    - condition: "Missed 2 family commitments this week"
      action: "Review calendar, block family time first"
```

### Example 3: Creative/Artist Constitution

```yaml
core_principles:
  - id: "creative_expression"
    name: "Art as Life Force"
    description: "Creativity is non-negotiable"
    rules:
      - "Daily creative practice, no exceptions"
      - "Protect creative energy from draining activities"
      - "Share work regularly despite fear"
    weight: 10

life_domains:
  - id: "creative_output"
    metrics:
      - "Hours creating (per day)"
      - "Works completed (per month)"
      - "Public sharing (per week)"
    minimum_standards:
      daily_creative_hours: 3
      monthly_completions: 2

  - id: "inspiration"
    metrics:
      - "Art/beauty consumed (hours/week)"
      - "Nature time (hours/week)"
      - "Novel experiences (count/month)"
    minimum_standards:
      inspiration_hours: 5
```

## Customization Workflow

### Step 1: Self-Reflection

Before customizing, reflect on:

1. **What matters most to you?** (Top 3-5 values)
2. **What does success look like?** (In 1 year, 5 years, life)
3. **What are your non-negotiables?** (Red lines)
4. **What drains vs energizes you?**
5. **What patterns do you want to change?**

### Step 2: Choose Starting Point

- **Default**: If unsure, start here
- **Template**: If one resonates with you
- **Custom**: If you have strong, specific vision

### Step 3: Customize Iteratively

Don't overthink it. Start with something, use it for 2-4 weeks, then refine.

**Good customization process:**
1. Use default for 2 weeks
2. Notice what feels off
3. Adjust 2-3 things
4. Use for 2 more weeks
5. Repeat

**Poor customization process:**
1. Spend 3 days crafting perfect constitution
2. Never actually use the system
3. Realize it doesn't fit after 1 week
4. Abandon everything

### Step 4: Learn from Overrides

The system logs every override you request. After 1-2 months:

```bash
# Review override patterns
alter constitution review-overrides

# System will show:
# - Which rules you override most often
# - Suggested constitutional amendments
# - Patterns in your behavior
```

If you override the same rule 5+ times, it's probably wrong for you. Amend the constitution.

### Step 5: Evolve with You

Your constitution should evolve as you do:

- **Life transitions**: New job, marriage, kids, retirement
- **Changed priorities**: What mattered at 25 ≠ what matters at 45
- **Growth**: As you evolve, your principles may too

**Version your constitution:**
```yaml
version: "2.1.0"  # Major.Minor.Patch
last_updated: "2026-06-15"
changelog:
  - "2.1.0: Added family_first principle after becoming parent"
  - "2.0.0: Major overhaul after career transition"
  - "1.5.0: Reduced productivity focus, increased wellbeing"
```

## Advanced: Multi-Constitution System

For power users: Multiple constitutions for different contexts.

```yaml
# data/user_data/constitutions/
├── work_mode.yaml        # During intense work periods
├── recovery_mode.yaml    # After burnout or illness
├── exploration_mode.yaml # When trying new things
└── default.yaml          # Normal operating mode
```

Activate via:
```bash
alter constitution activate work_mode
alter constitution activate recovery_mode
```

System tracks which mode you're in and applies appropriate principles.

## FAQs

**Q: Can I change the required principles?**
A: You can customize their rules and names, but can't remove them entirely. They're required for system integrity.

**Q: What if I don't know what I want?**
A: Start with default. It's designed to be broadly applicable. Refine after using it.

**Q: Can I have no minimum standards?**
A: Yes. Set them to 0 or remove the `minimum_standards` section.

**Q: How often should I update my constitution?**
A: Review quarterly. Update when life circumstances change significantly.

**Q: Can I share my constitution with others?**
A: Yes! Share your constitution file. Others can use it as a template.

**Q: What happens if my constitution has contradictions?**
A: System will flag conflicts and ask you to resolve them by adjusting weights or rules.

**Q: Can I disable all interventions?**
A: Yes. Set `intervention_triggers: {}` in your constitution.

**Q: Can I make the system more aggressive/pushy?**
A: No. The autonomy principle prevents the system from being coercive. It can only advise more frequently or urgently, but never force.

## Getting Help

```bash
# Validate your custom constitution
alter constitution validate data/user_data/my_constitution.yaml

# See which constitution is currently active
alter constitution show

# Compare your constitution to default
alter constitution diff

# Get suggestions based on your usage patterns
alter constitution suggest
```

## Community Constitutions

Check `docs/community_constitutions/` for constitutions shared by other users:
- `athlete.yaml`
- `student.yaml`
- `retiree.yaml`
- `digital_nomad.yaml`
- And more...

Use as inspiration or starting points.

---

**Remember**: Your constitution is not a prison. It's a compass. It guides, not constrains. The override system exists because flexibility is wisdom, not weakness.
