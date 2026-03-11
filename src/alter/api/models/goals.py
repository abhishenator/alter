"""Goal-related API models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GoalCreateRequest(BaseModel):
    description: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    time_horizon: str = "quarter"
    parent_goal_id: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    domain: str
    description: str
    time_horizon: str
    parent_goal_id: Optional[str]
    status: str
    outcome: Optional[str]
    created_at: str
    completed_at: Optional[str]


class GoalListResponse(BaseModel):
    goals: List[GoalResponse]
    total: int


class GoalUpdateRequest(BaseModel):
    description: Optional[str] = None
    domain: Optional[str] = None
    time_horizon: Optional[str] = None
    parent_goal_id: Optional[str] = None


class GoalCompleteRequest(BaseModel):
    outcome: str = "success"
    notes: str = ""
