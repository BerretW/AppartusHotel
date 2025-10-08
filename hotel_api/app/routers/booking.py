# FILE: hotel_api/app/routers/booking.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/booking",
    tags=["Booking Engine (Veřejné)"]
)

@router.post("/availability", response_model=List[schemas.AvailableRoomType])
async def check_availability(
    request: schemas.AvailabilityRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Veřejný endpoint pro zjištění dostupnosti a cen.
    Vrátí seznam dostupných typů pokojů s celkovou cenou za pobyt pro každý cenový plán.
    """
    if request.end_date <= request.start_date:
        raise HTTPException(status_code=400, detail="Datum odjezdu musí být po datu příjezdu.")
    return await crud.find_available_room_types(
        db,
        start_date=request.start_date,
        end_date=request.end_date,
        guests=request.guests
    )

@router.post("/reservations", response_model=schemas.Reservation, status_code=201)
async def create_public_reservation(
    request: schemas.PublicReservationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Veřejný endpoint pro vytvoření nové rezervace hostem z webu.
    """
    # Zde by v reálné aplikaci byla ještě další validace a integrace s platební bránou.
    return await crud.create_reservation(db, res_data=request)