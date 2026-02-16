"""Cycle and planning API models."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CycleResponse(BaseModel):
    cycle_completed: bool
    cycle_id: str
    phases_executed: List[str]
    missions_created: Optional[int]
    strategies_count: int
    tasks_count: int
    agents_dispatched: int


class DailyPlanResponse(BaseModel):
    cycle_type: str
    date: str
    tasks: List[Dict[str, Any]]


class WeeklyReflectionResponse(BaseModel):
    cycle_type: str
    insights: Dict[str, Any]
    adjustments: List[str]


class MonthlyPlanResponse(BaseModel):
    cycle_type: str
    goal_adjustments: List[str]


class DailyDataRequest(BaseModel):
    date: Optional[str] = None
    health: Optional[Dict[str, Any]] = None
    emotions: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, Any]] = None
    growth: Optional[Dict[str, Any]] = None
    wealth: Optional[Dict[str, Any]] = None
