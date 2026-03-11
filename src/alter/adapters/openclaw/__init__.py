"""
OpenClaw Adapter — LifeOS as an installable OpenClaw plugin.

Makes LifeOS's consciousness engine available as an OpenClaw skill:
- OpenClaw Cron fires ticks on schedule
- OpenClaw's LLM provides think_fn
- OpenClaw's channels deliver notifications (WhatsApp, Discord, etc.)

Components:
- SKILL.md: Skill manifest with tools + cron definitions
- adapter.py: OpenClawAdapter — maps session to think_fn + delivery
- tools.py: Tool definitions for OpenClaw users
"""
