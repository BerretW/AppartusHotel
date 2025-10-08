# FILE: hotel_api/app/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from .. import crud, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard a Kalendář"],
    dependencies=[Depends(is_admin_or_manager)] # Všechny endpointy zde vyžadují oprávnění
)

@router.get("/timeline", response_model=List[schemas.RoomTimeline])
async def get_rooms_timeline(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db)
):
    """
    Vrátí kompletní časovou osu událostí (rezervace, úkoly) pro všechny pokoje
    v zadaném časovém rozmezí. Ideální pro vizuální kalendář pokojů.
    """
    return await crud.get_timeline_data(db, start_date=start_date, end_date=end_date)


@router.get("/employees-schedule", response_model=List[schemas.EmployeeSchedule])
async def get_full_employees_schedule(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db)
):
    """
    Vrátí přehled všech zaměstnanců a jejich naplánovaných úkolů v zadaném
    časovém rozmezí. Vhodné pro kalendář vytíženosti personálu.
    """
    return await crud.get_employees_schedule(db, start_date=start_date, end_date=end_date)


@router.get("/active-tasks", response_model=List[schemas.ActiveTask])
async def get_current_active_tasks(db: AsyncSession = Depends(get_db)):
    """
    Poskytuje "živý" přehled o tom, co se právě děje. Vrací seznam všech úkolů,
    které jsou ve stavu 'probíhá', včetně informací o zaměstnanci a pokoji.
    """
    return await crud.get_active_tasks(db)