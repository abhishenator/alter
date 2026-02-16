"""
High-level tests for Sub-Agent system.
"""

import pytest
from datetime import datetime


class TestAgentBase:
    """Tests for base agent interface and functionality."""

    def test_agent_initialization(self):
        """Should initialize agent with ID and capabilities."""
        from alter.agents.base import SubAgent

        agent = SubAgent(agent_id="test_agent", capabilities=["research", "analysis"])

        assert agent.agent_id == "test_agent"
        assert "research" in agent.capabilities

    def test_agent_receive_mission(self):
        """Should accept mission from meta-loop."""
        from alter.agents.base import SubAgent, Mission

        agent = SubAgent(agent_id="test_agent")

        mission = Mission(
            mission_id="m1",
            description="Research productivity tools",
            success_criteria=["Find at least 5 tools", "Analyze pros/cons"],
            deadline=datetime.now()
        )

        agent.receive_mission(mission)

        assert agent.current_mission.mission_id == "m1"
        assert agent.status == "ready"

    def test_agent_execute_mission(self):
        """Should execute mission and generate report."""
        from alter.agents.base import SubAgent, Mission

        agent = SubAgent(agent_id="test_agent")

        mission = Mission(
            mission_id="m1",
            description="Simple test mission",
            success_criteria=["Complete task"]
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert report.agent_id == "test_agent"
        assert report.mission_id == "m1"
        assert report.status in ["completed", "partial", "failed"]
        assert report.findings is not None

    def test_agent_report_structure(self):
        """Should return standardized report structure."""
        from alter.agents.base import SubAgent, Mission, AgentReport

        agent = SubAgent(agent_id="test_agent")

        mission = Mission(mission_id="m1", description="Test")
        agent.receive_mission(mission)
        report = agent.execute()

        # Validate report structure
        assert hasattr(report, "agent_id")
        assert hasattr(report, "mission_id")
        assert hasattr(report, "status")
        assert hasattr(report, "findings")
        assert hasattr(report, "recommendations")
        assert hasattr(report, "confidence")
        assert hasattr(report, "next_actions")


class TestResearchAgent:
    """Tests for Research Agent."""

    def test_research_agent_market_scan(self):
        """Should perform market research and analysis."""
        from alter.agents.research_agent import ResearchAgent, Mission

        agent = ResearchAgent(agent_id="research_1")

        mission = Mission(
            mission_id="m1",
            description="Research AI productivity tools market",
            parameters={"depth": "comprehensive", "sources": ["web", "academic"]}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert report.status == "completed"
        assert len(report.findings) > 0
        assert "market_trends" in report.findings
        assert report.confidence > 0

    def test_research_agent_validate_idea(self):
        """Should validate business/project ideas."""
        from alter.agents.research_agent import ResearchAgent, Mission

        agent = ResearchAgent(agent_id="research_1")

        mission = Mission(
            mission_id="m2",
            description="Validate idea: AI-powered meal planning app",
            parameters={"validation_criteria": ["market_size", "competition", "feasibility"]}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "validation_results" in report.findings
        assert "market_size" in report.findings["validation_results"]
        assert len(report.recommendations) > 0


class TestIdeaAgent:
    """Tests for Idea Generation Agent."""

    def test_idea_agent_generate_ideas(self):
        """Should generate ideas in specified domain."""
        from alter.agents.idea_agent import IdeaAgent, Mission

        agent = IdeaAgent(agent_id="idea_1")

        mission = Mission(
            mission_id="m1",
            description="Generate 10 side project ideas in AI/ML domain",
            parameters={"domain": "ai_ml", "count": 10, "constraints": ["solo_project"]}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert len(report.findings["ideas"]) == 10
        assert all("description" in idea for idea in report.findings["ideas"])

    def test_idea_agent_synthesize_concepts(self):
        """Should combine existing ideas into novel concepts."""
        from alter.agents.idea_agent import IdeaAgent, Mission

        agent = IdeaAgent(agent_id="idea_1")

        mission = Mission(
            mission_id="m2",
            description="Synthesize new ideas from: meditation apps + productivity tools",
            parameters={"seed_concepts": ["meditation", "productivity"]}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "synthesized_ideas" in report.findings
        assert len(report.findings["synthesized_ideas"]) > 0


class TestHealthAgent:
    """Tests for Health Agent."""

    def test_health_agent_track_vitals(self):
        """Should analyze health data and identify patterns."""
        from alter.agents.health_agent import HealthAgent, Mission

        agent = HealthAgent(agent_id="health_1")

        mission = Mission(
            mission_id="m1",
            description="Analyze sleep patterns for last 30 days",
            parameters={
                "data_source": "apple_health",
                "metrics": ["sleep_duration", "sleep_quality", "hrv"]
            }
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "patterns" in report.findings
        assert "trends" in report.findings
        assert len(report.recommendations) > 0

    def test_health_agent_workout_plan(self):
        """Should create personalized workout plans."""
        from alter.agents.health_agent import HealthAgent, Mission

        agent = HealthAgent(agent_id="health_1")

        mission = Mission(
            mission_id="m2",
            description="Create 4-week workout plan for marathon training",
            parameters={"goal": "run_marathon", "current_fitness": "intermediate"}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "workout_plan" in report.findings
        assert len(report.findings["workout_plan"]["weeks"]) == 4


class TestActivityAgent:
    """Tests for Activity Monitoring Agent."""

    def test_activity_agent_monitor_patterns(self):
        """Should monitor and summarize user activity."""
        from alter.agents.activity_agent import ActivityAgent, Mission

        agent = ActivityAgent(agent_id="activity_1")

        mission = Mission(
            mission_id="m1",
            description="Summarize today's activity patterns",
            parameters={"date": "2026-02-10"}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "time_allocation" in report.findings
        assert "productivity_score" in report.findings
        assert "distractions" in report.findings

    def test_activity_agent_detect_anomalies(self):
        """Should detect unusual patterns in user behavior."""
        from alter.agents.activity_agent import ActivityAgent, Mission

        agent = ActivityAgent(agent_id="activity_1")

        mission = Mission(
            mission_id="m2",
            description="Detect anomalies in last 7 days",
            parameters={"lookback_days": 7}
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "anomalies" in report.findings
        # Anomalies might be empty if patterns are normal
        assert isinstance(report.findings["anomalies"], list)


class TestExecutionAgent:
    """Tests for Execution Agent (task management and tool usage)."""

    def test_execution_agent_use_openclaw(self):
        """Should delegate coding tasks to OpenClaw."""
        from alter.agents.execution_agent import ExecutionAgent, Mission

        agent = ExecutionAgent(agent_id="execution_1")

        mission = Mission(
            mission_id="m1",
            description="Create a Python script to analyze CSV data",
            parameters={
                "tool": "openclaw",
                "task_type": "coding",
                "requirements": ["Read CSV", "Generate summary stats", "Create visualization"]
            }
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert report.status == "completed"
        assert "code_created" in report.findings or "openclaw_result" in report.findings

    def test_execution_agent_task_scheduling(self):
        """Should schedule tasks in user's calendar."""
        from alter.agents.execution_agent import ExecutionAgent, Mission

        agent = ExecutionAgent(agent_id="execution_1")

        mission = Mission(
            mission_id="m2",
            description="Schedule learning tasks in calendar",
            parameters={
                "tasks": [
                    {"title": "Study system design", "duration": 120},
                    {"title": "Practice coding", "duration": 60}
                ]
            }
        )

        agent.receive_mission(mission)
        report = agent.execute()

        assert "scheduled_tasks" in report.findings
        assert len(report.findings["scheduled_tasks"]) == 2


class TestAgentCoordination:
    """Tests for multi-agent coordination."""

    def test_agents_execute_in_parallel(self):
        """Should execute multiple agents concurrently."""
        from alter.orchestration.coordinator import AgentCoordinator
        from alter.agents.research_agent import ResearchAgent
        from alter.agents.idea_agent import IdeaAgent
        from alter.agents.base import Mission

        coordinator = AgentCoordinator()

        # Create multiple agents with missions
        research_agent = ResearchAgent(agent_id="research_1")
        idea_agent = IdeaAgent(agent_id="idea_1")

        missions = [
            Mission(mission_id="m1", description="Research AI tools"),
            Mission(mission_id="m2", description="Generate project ideas")
        ]

        research_agent.receive_mission(missions[0])
        idea_agent.receive_mission(missions[1])

        # Execute in parallel
        reports = coordinator.execute_parallel([research_agent, idea_agent])

        assert len(reports) == 2
        assert reports[0].agent_id == "research_1"
        assert reports[1].agent_id == "idea_1"

    def test_agent_communication(self):
        """Should allow agents to communicate/share information."""
        from alter.orchestration.coordinator import AgentCoordinator
        from alter.agents.research_agent import ResearchAgent
        from alter.agents.idea_agent import IdeaAgent

        coordinator = AgentCoordinator()

        # Research agent finds information
        research_agent = ResearchAgent(agent_id="research_1")
        # Idea agent uses research findings to generate ideas
        idea_agent = IdeaAgent(agent_id="idea_1")

        # Execute research first
        research_report = coordinator.execute_single(research_agent)

        # Pass findings to idea agent
        idea_agent.receive_context(research_report.findings)

        idea_report = coordinator.execute_single(idea_agent)

        # Ideas should be informed by research
        assert idea_report.findings is not None

    def test_agent_failure_handling(self):
        """Should handle agent failures gracefully."""
        from alter.orchestration.coordinator import AgentCoordinator
        from alter.agents.base import SubAgent, Mission

        coordinator = AgentCoordinator()

        # Create agent that will fail
        agent = SubAgent(agent_id="failing_agent")
        mission = Mission(mission_id="m1", description="Impossible task")
        agent.receive_mission(mission)

        # Should not crash, should return failure report
        report = coordinator.execute_single(agent)

        assert report.status == "failed"
        assert report.findings is not None  # Should explain what went wrong


class TestAgentSkills:
    """Tests for agent skill system."""

    def test_agent_can_use_multiple_skills(self):
        """Should allow agents to use different skills as needed."""
        from alter.agents.execution_agent import ExecutionAgent
        from alter.skills.web_research import WebResearchSkill
        from alter.skills.data_analysis import DataAnalysisSkill

        agent = ExecutionAgent(agent_id="execution_1")

        # Agent should have access to multiple skills
        assert agent.has_skill("web_research")
        assert agent.has_skill("data_analysis")

    def test_agent_selects_appropriate_skill(self):
        """Should automatically select right skill for task."""
        from alter.agents.execution_agent import ExecutionAgent, Mission

        agent = ExecutionAgent(agent_id="execution_1")

        mission = Mission(
            mission_id="m1",
            description="Find and analyze data about productivity trends",
            parameters={}
        )

        agent.receive_mission(mission)

        # Should determine it needs both web_research and data_analysis
        selected_skills = agent.select_skills_for_mission(mission)

        assert "web_research" in selected_skills
        assert "data_analysis" in selected_skills
