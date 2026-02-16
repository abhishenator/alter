"""
Constitution system - Ethical and value framework for ALTER.

Handles loading, validating, and applying constitution principles to decisions.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid


class ConstitutionValidationError(Exception):
    """Raised when constitution validation fails."""
    pass


@dataclass
class Principle:
    """A core principle in the constitution."""
    id: str
    name: str
    description: str
    rules: List[str]
    weight: int  # 1-10, higher = more important

    def __post_init__(self) -> None:
        if not 1 <= self.weight <= 10:
            raise ConstitutionValidationError(f"Principle weight must be 1-10, got {self.weight}")


@dataclass
class LifeDomain:
    """A domain of life to track and optimize."""
    id: str
    name: str
    description: str
    metrics: List[str]
    minimum_standards: Dict[str, Any]


@dataclass
class DecisionValidationResult:
    """Result of validating a decision against constitution."""
    approved: bool
    reasoning: str
    violated_principles: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ConflictResolution:
    """Result of resolving a conflict between principles."""
    chosen_option: str
    reasoning: str
    tradeoffs: List[str] = field(default_factory=list)


@dataclass
class OverrideRequest:
    """Request to override a constitution rule."""
    override_id: str
    type: str  # temporary, contextual, permanent, emergency
    rule_id: str
    duration_days: Optional[int] = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OverrideResult:
    """Result of processing an override request."""
    approved: bool
    override_id: Optional[str] = None
    reason: str = ""
    expires_at: Optional[datetime] = None
    override_applied: bool = False
    activated: Optional[bool] = None  # For contextual overrides
    suspended_rules: Optional[List[str]] = None  # For contextual overrides


@dataclass
class Amendment:
    """A proposed amendment to the constitution."""
    amendment_id: str
    rule_id: str
    change: Dict[str, Any]
    reason: str
    status: str  # pending_approval, approved, rejected
    reflection_period_hours: int = 24
    proposed_at: datetime = field(default_factory=datetime.now)


@dataclass
class StandardViolation:
    """A violation of minimum standards."""
    domain: str
    metric: str
    expected: Any
    actual: Any
    severity: str  # low, medium, high


@dataclass
class Intervention:
    """An intervention triggered by the constitution."""
    intervention_id: str
    urgency: str  # immediate, weekly, monthly
    condition: str
    message: str
    recommended_action: str
    timestamp: datetime = field(default_factory=datetime.now)


class Constitution:
    """
    Main constitution class - the ethical and value framework.

    Loads from YAML, validates decisions, manages overrides and amendments.
    """

    # Required principles that cannot be removed
    REQUIRED_PRINCIPLES = {"autonomy", "ethics", "transparency"}

    def __init__(
        self,
        version: str,
        constitution_type: str,
        core_principles: List[Principle],
        life_domains: List[LifeDomain],
        decision_framework: Dict[str, Any],
        intervention_triggers: Dict[str, Any],
        guardrails: List[Dict[str, Any]],
        override_system: Dict[str, Any],
        meta_principles: Dict[str, Any]
    ):
        self.version = version
        self.constitution_type = constitution_type
        self.core_principles = core_principles
        self.life_domains = life_domains
        self.decision_framework = decision_framework
        self.intervention_triggers = intervention_triggers
        self.guardrails = guardrails
        self.override_system = override_system
        self.meta_principles = meta_principles

        # Runtime state
        self.active_overrides: List[OverrideRequest] = []
        self.override_history: List[OverrideRequest] = []
        self.pending_amendments: List[Amendment] = []

        # Validate on initialization
        self._validate()

    def _validate(self) -> None:
        """Validate that constitution has required elements."""
        principle_ids = {p.id for p in self.core_principles}

        missing = self.REQUIRED_PRINCIPLES - principle_ids
        if missing:
            raise ConstitutionValidationError(
                f"Constitution missing required principles: {missing}"
            )

    @classmethod
    def load(cls, custom_path: Optional[Path] = None) -> Constitution:
        """
        Load constitution from file.

        Priority:
        1. Custom path if provided
        2. User's custom constitution (data/user_data/my_constitution.yaml)
        3. Default constitution (config/constitution.yaml)
        """
        if custom_path and custom_path.exists():
            path = custom_path
        else:
            # Try user custom first
            user_path = Path("data/user_data/my_constitution.yaml")
            if user_path.exists():
                path = user_path
            else:
                # Fall back to default
                path = Path("config/constitution.yaml")

        with open(path, 'r') as f:
            yaml_content = f.read()

        return cls.from_yaml(yaml_content)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> Constitution:
        """Parse constitution from YAML string."""
        data = yaml.safe_load(yaml_content)

        # Parse core principles
        principles = []
        for p_data in data.get("core_principles", []):
            principle = Principle(
                id=p_data["id"],
                name=p_data.get("name", p_data["id"]),
                description=p_data.get("description", ""),
                rules=p_data.get("rules", []),
                weight=p_data.get("weight", 5)
            )
            principles.append(principle)

        # Parse life domains
        domains = []
        for d_data in data.get("life_domains", []):
            domain = LifeDomain(
                id=d_data["id"],
                name=d_data.get("name", d_data["id"]),
                description=d_data.get("description", ""),
                metrics=d_data.get("metrics", []),
                minimum_standards=d_data.get("minimum_standards", {})
            )
            domains.append(domain)

        return cls(
            version=data.get("version", "1.0.0"),
            constitution_type=data.get("constitution_type", "default"),
            core_principles=principles,
            life_domains=domains,
            decision_framework=data.get("decision_framework", {}),
            intervention_triggers=data.get("intervention_triggers", {}),
            guardrails=data.get("guardrails", []),
            override_system=data.get("override_system", {}),
            meta_principles=data.get("meta_principles", {})
        )

    def validate_decision(self, decision: Dict[str, Any]) -> DecisionValidationResult:
        """
        Validate a decision against constitution principles.

        Args:
            decision: Dict with action, domain, impact, etc.

        Returns:
            DecisionValidationResult with approval status and reasoning
        """
        violated = []
        warnings = []

        # Check if decision harms any domain significantly
        impact = decision.get("impact", {})
        for domain, value in impact.items():
            if value < -3:  # Significant negative impact
                # Check if this violates minimum standards
                domain_obj = self.get_domain(domain)
                if domain_obj and domain in ["health", "relationships"]:
                    # High-priority domains
                    violated.append(f"{domain}_protection")

        # Check active overrides
        override_applied = self._check_active_overrides(decision)

        # If violations but override is active, allow it
        if violated and not override_applied:
            return DecisionValidationResult(
                approved=False,
                reasoning=f"Decision violates protected domains: {violated}",
                violated_principles=violated,
                warnings=warnings
            )

        # Decision is approved
        reasoning = "Decision aligns with constitution principles"
        if override_applied:
            reasoning += " (with active override)"

        return DecisionValidationResult(
            approved=True,
            reasoning=reasoning,
            violated_principles=[],
            warnings=warnings
        )

    def resolve_conflict(self, conflict: Dict[str, Any]) -> ConflictResolution:
        """
        Resolve a conflict between competing options using principle weights.

        Args:
            conflict: Dict with options and their principle impacts

        Returns:
            ConflictResolution with chosen option and reasoning
        """
        options = conflict.get("options", [])
        if not options:
            raise ValueError("No options provided for conflict resolution")

        # Score each option based on principle weights
        scores = {}
        for option in options:
            score = 0
            option_name = option.get("name", "")
            principles = option.get("principles", {})

            for principle_id, impact in principles.items():
                principle = self.get_principle(principle_id)
                if principle:
                    score += impact * principle.weight

            scores[option_name] = score

        # Choose highest scoring option
        chosen = max(scores, key=scores.get)

        reasoning = f"Selected '{chosen}' based on weighted principle scores. "
        reasoning += f"Scores: {scores}"

        return ConflictResolution(
            chosen_option=chosen,
            reasoning=reasoning,
            tradeoffs=[f"Option '{opt['name']}' scored {scores[opt['name']]}" for opt in options]
        )

    def request_override(self, override_request: Dict[str, Any]) -> OverrideResult:
        """
        Process a request to override constitution rules.

        Args:
            override_request: Dict with type, rule_id, duration, reason

        Returns:
            OverrideResult indicating if approved
        """
        override_type = override_request.get("type", "temporary")
        rule_id = override_request.get("rule_id", "")
        duration_days = override_request.get("duration_days", 1)
        reason = override_request.get("reason", "")

        # Check if rule is blocked from override
        blocked_rules = self.override_system.get("override_limits", {}).get("blocked_overrides", {}).get("never_override", [])

        if rule_id in blocked_rules or any(rule_id.startswith(blocked) for blocked in blocked_rules):
            return OverrideResult(
                approved=False,
                reason=f"Rule '{rule_id}' is blocked from override for safety"
            )

        # Check rate limits
        if override_type == "temporary":
            recent_overrides = [o for o in self.override_history
                               if o.timestamp > datetime.now() - timedelta(days=30)]

            limit = self.override_system.get("override_limits", {}).get("rate_limits", {}).get("temporary_overrides_per_month", 8)

            if len(recent_overrides) >= limit:
                return OverrideResult(
                    approved=False,
                    reason=f"Rate limit exceeded: {len(recent_overrides)}/{limit} overrides this month"
                )

        # Approve override
        override_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=duration_days) if duration_days else None

        override = OverrideRequest(
            override_id=override_id,
            type=override_type,
            rule_id=rule_id,
            duration_days=duration_days,
            reason=reason
        )

        self.active_overrides.append(override)
        self.override_history.append(override)

        return OverrideResult(
            approved=True,
            override_id=override_id,
            reason="Override approved and logged",
            expires_at=expires_at,
            override_applied=True
        )

    def activate_context(self, context_request: Dict[str, Any]) -> OverrideResult:
        """
        Activate a contextual override mode (e.g., vacation mode).

        Args:
            context_request: Dict with context_name, duration, suspended_rules

        Returns:
            OverrideResult indicating activation status
        """
        context_name = context_request.get("context_name", "")
        duration_days = context_request.get("duration_days", 7)
        suspended_rules = context_request.get("suspended_rules", [])

        override_id = str(uuid.uuid4())

        # Create override for each suspended rule pattern
        for rule_pattern in suspended_rules:
            override = OverrideRequest(
                override_id=override_id,
                type="contextual",
                rule_id=rule_pattern,
                duration_days=duration_days,
                reason=f"Contextual mode: {context_name}"
            )
            self.active_overrides.append(override)

        return OverrideResult(
            approved=True,
            override_id=override_id,
            reason=f"Context '{context_name}' activated",
            expires_at=datetime.now() + timedelta(days=duration_days),
            override_applied=True,
            activated=True,
            suspended_rules=suspended_rules
        )

    def suggest_amendments(self) -> List[Amendment]:
        """
        Suggest amendments based on override patterns.

        Analyzes frequently overridden rules and suggests permanent changes.
        """
        suggestions = []

        # Count overrides per rule
        rule_counts: Dict[str, int] = {}
        for override in self.override_history[-100:]:  # Last 100 overrides
            rule_counts[override.rule_id] = rule_counts.get(override.rule_id, 0) + 1

        # Suggest amendments for frequently overridden rules
        for rule_id, count in rule_counts.items():
            if count >= 5:  # Overridden 5+ times
                amendment = Amendment(
                    amendment_id=str(uuid.uuid4()),
                    rule_id=rule_id,
                    change={"suggestion": "Consider adjusting this rule"},
                    reason=f"Rule overridden {count} times, may not fit user needs",
                    status="pending_approval"
                )
                suggestions.append(amendment)

        return suggestions

    def propose_amendment(self, amendment: Dict[str, Any]) -> Amendment:
        """
        Propose an amendment to the constitution.

        Args:
            amendment: Dict with rule_id, change, reason

        Returns:
            Amendment object with pending status
        """
        amendment_obj = Amendment(
            amendment_id=str(uuid.uuid4()),
            rule_id=amendment["rule_id"],
            change=amendment["change"],
            reason=amendment["reason"],
            status="pending_approval"
        )

        self.pending_amendments.append(amendment_obj)
        return amendment_obj

    def get_life_domains(self) -> List[LifeDomain]:
        """Get all life domains defined in constitution."""
        return self.life_domains

    def get_domain(self, domain_id: str) -> Optional[LifeDomain]:
        """Get a specific life domain by ID."""
        for domain in self.life_domains:
            if domain.id == domain_id:
                return domain
        return None

    def get_principle(self, principle_id: str) -> Optional[Principle]:
        """Get a specific principle by ID."""
        for principle in self.core_principles:
            if principle.id == principle_id:
                return principle
        return None

    def get_rule_value(self, rule_path: str) -> Any:
        """
        Get the value of a rule by path (e.g., 'health/sleep_hours').

        Args:
            rule_path: Path to rule like 'domain/metric'

        Returns:
            Rule value if found, None otherwise
        """
        parts = rule_path.split("/")
        if len(parts) != 2:
            return None

        domain_id, metric = parts
        domain = self.get_domain(domain_id)

        if domain and metric in domain.minimum_standards:
            return domain.minimum_standards[metric]

        return None

    def check_minimum_standards(self, user_data: Dict[str, Any]) -> List[StandardViolation]:
        """
        Check user data against minimum standards.

        Args:
            user_data: Dict with domain -> metric -> value

        Returns:
            List of StandardViolation objects
        """
        violations = []

        for domain in self.life_domains:
            domain_data = user_data.get(domain.id, {})

            for metric, expected in domain.minimum_standards.items():
                actual = domain_data.get(metric)

                if actual is not None and actual < expected:
                    violations.append(StandardViolation(
                        domain=domain.id,
                        metric=metric,
                        expected=expected,
                        actual=actual,
                        severity="high" if actual < expected * 0.7 else "medium"
                    ))

        return violations

    def check_intervention_triggers(
        self,
        user_state: Dict[str, Any],
        trigger_type: str = "immediate"
    ) -> List[Intervention]:
        """
        Check if any intervention triggers are activated.

        Args:
            user_state: Current user state with metrics
            trigger_type: Type of triggers to check (immediate, weekly, monthly)

        Returns:
            List of activated Intervention objects
        """
        interventions = []

        triggers = self.intervention_triggers.get(f"{trigger_type}_intervention", [])

        for trigger in triggers:
            condition = trigger.get("condition", "")
            action = trigger.get("action", "")

            # Simple condition checking (would be more sophisticated in practice)
            if "sleep" in condition.lower() and "health" in user_state:
                sleep_data = user_state["health"].get("sleep_hours_last_3_days", [])
                if sleep_data and all(hours < 5 for hours in sleep_data):
                    interventions.append(Intervention(
                        intervention_id=str(uuid.uuid4()),
                        urgency=trigger_type,
                        condition=condition,
                        message=f"Sleep deprivation detected. {action}",
                        recommended_action=action
                    ))

        return interventions

    def _check_active_overrides(self, decision: Dict[str, Any]) -> bool:
        """Check if decision is covered by active overrides."""
        # Clean expired overrides
        now = datetime.now()
        self.active_overrides = [
            o for o in self.active_overrides
            if not o.duration_days or o.timestamp + timedelta(days=o.duration_days) > now
        ]

        # Check if any active override covers this decision
        decision_domain = decision.get("domain", "")
        for override in self.active_overrides:
            if decision_domain in override.rule_id or override.rule_id in str(decision):
                return True

        return False
