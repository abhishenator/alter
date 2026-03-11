"""Dependency injection for LifeOS API."""

from functools import lru_cache
from alter.api.service import AlterService


@lru_cache
def get_service() -> AlterService:
    """Get singleton AlterService instance."""
    return AlterService()
