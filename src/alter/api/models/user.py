"""User-related API models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserInitRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    purpose: Optional[str] = None


class UserInitResponse(BaseModel):
    user_id: str
    purpose: Optional[str]
    created_at: str


class PurposeUpdateRequest(BaseModel):
    purpose: str = Field(..., min_length=1)
    notes: str = ""


class PurposeResponse(BaseModel):
    current: Optional[str]
    history: List[dict]


class UserStatusResponse(BaseModel):
    user_id: str
    purpose: Optional[str]
    active_goals_count: int
    total_goals: int
    cycle_count: int
    last_execution: Optional[str]
    life_domains: List[dict]
    personality_traits: dict
    strengths: List[str]
    growth_areas: List[str]
