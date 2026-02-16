"""Constitution-related API models."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class PrincipleResponse(BaseModel):
    id: str
    name: str
    description: str
    rules: List[str]
    weight: int


class DomainResponse(BaseModel):
    id: str
    name: str
    description: str
    metrics: List[str]
    minimum_standards: Dict[str, Any]


class ConstitutionResponse(BaseModel):
    version: str
    constitution_type: str
    principles: List[PrincipleResponse]
    domains: List[DomainResponse]


class OverrideRequest(BaseModel):
    type: str = "temporary"
    rule_id: str
    duration_days: int = 1
    reason: str = ""
