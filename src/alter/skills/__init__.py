"""
Skills — Sense organs for the consciousness engine.

Each skill expands what ALTER can perceive, investigate, or act upon.
Before a skill exists, the system is blind to that domain. Adding a
skill is like growing a new sense organ.

Skill categories:
- Observation: feed data into daily_data → world model → prediction errors
- Investigation: answer questions during LLM inquiry (future)
- Action: execute decisions from consciousness layer (future)

Components:
- base.py: Skill base class and protocols
- registry.py: SkillRegistry for registration and discovery
- health.py: Health metrics (sleep, exercise, heart rate)
- calendar.py: Calendar events (meetings, focus time, deadlines)
- journal.py: Journal entries (mood, energy, free-text reflections)
"""
