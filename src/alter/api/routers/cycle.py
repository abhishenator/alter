"""Meta-loop cycle and planning endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from alter.api.service import AlterService
from alter.api.deps import get_service
from alter.api.models.cycle import DailyDataRequest

router = APIRouter()


@router.post("/users/{user_id}/cycle")
def run_cycle(user_id: str, service: AlterService = Depends(get_service)):
    """Run a complete meta-loop cycle."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.run_cycle(user_id)


@router.post("/users/{user_id}/plan/daily")
def plan_daily(user_id: str, service: AlterService = Depends(get_service)):
    """Run daily planning cycle."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.run_daily_planning(user_id)


@router.post("/users/{user_id}/plan/weekly")
def plan_weekly(user_id: str, service: AlterService = Depends(get_service)):
    """Run weekly reflection."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.run_weekly_reflection(user_id)


@router.post("/users/{user_id}/plan/monthly")
def plan_monthly(user_id: str, service: AlterService = Depends(get_service)):
    """Run monthly planning."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.run_monthly_planning(user_id)


@router.post("/users/{user_id}/daily-data")
def record_daily_data(user_id: str, body: DailyDataRequest,
                      service: AlterService = Depends(get_service)):
    """Record daily metrics across life domains."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    data = {"date": body.date}
    if body.health:
        data["health"] = body.health
    if body.emotions:
        data["emotions"] = body.emotions
    if body.relationships:
        data["relationships"] = body.relationships
    if body.growth:
        data["growth"] = body.growth
    if body.wealth:
        data["wealth"] = body.wealth

    return service.record_daily_data(user_id, data)


@router.get("/users/{user_id}/daily-data/{date}")
def get_daily_data(user_id: str, date: str,
                   service: AlterService = Depends(get_service)):
    """Get daily data for a specific date."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.get_daily_data(user_id, date)


@router.get("/users/{user_id}/patterns")
def get_patterns(user_id: str, service: AlterService = Depends(get_service)):
    """Get detected behavioral patterns."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return {"patterns": service.get_patterns(user_id)}
