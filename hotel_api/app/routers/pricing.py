# FILE: hotel_api/app/routers/pricing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import crud, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager

router = APIRouter(
    prefix="/pricing",
    tags=["Cenotvorba"],
    dependencies=[Depends(is_admin_or_manager)] # Všechny endpointy zde vyžadují oprávnění manažera/majitele
)

@router.post("/rate-plans/", response_model=schemas.RatePlan, status_code=201)
async def create_new_rate_plan(
    plan_data: schemas.RatePlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Vytvoří nový cenový plán (např. 'Standard', 'Nevratný', 'Víkendový balíček').
    """
    return await crud.create_rate_plan(db, plan=plan_data)

@router.get("/rate-plans/", response_model=List[schemas.RatePlan])
async def get_all_rate_plans(db: AsyncSession = Depends(get_db)):
    """
    Vrátí seznam všech existujících cenových plánů.
    """
    return await crud.get_rate_plans(db)

@router.post("/rates/batch", status_code=201)
async def create_new_rates_in_batch(
    rates_data: List[schemas.RateCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    Vytvoří nebo aktualizuje více cen najednou pro různé dny, typy pokojů a plány.
    Toto je efektivní způsob, jak nahrát ceník na celé období.
    """
    # Zde by v reálné aplikaci byla i logika pro update, pokud cena pro daný den/typ/plán již existuje.
    # Pro zjednodušení nyní pouze vkládáme nové.
    await crud.create_rates_batch(db, rates=rates_data)
    return {"message": f"{len(rates_data)} cenových záznamů bylo úspěšně vytvořeno."}

# Zde by mohly být i endpointy pro správu restrikcí, např. /restrictions/batch