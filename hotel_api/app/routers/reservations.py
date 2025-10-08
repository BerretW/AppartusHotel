# FILE: hotel_api/app/routers/reservations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from .. import crud, schemas
from ..database import get_db
# TODO: Přidat a definovat závislosti pro recepční/manažery

router = APIRouter(prefix="/reservations", tags=["Rezervace a Účtování"])

@router.post("/", response_model=schemas.Reservation, status_code=201)
async def create_new_reservation(
    reservation_data: schemas.ReservationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Vytvoří novou rezervaci pro hosta."""
    return await crud.create_reservation(db, res_data=reservation_data)

@router.get("/", response_model=List[schemas.Reservation])
async def get_reservation_list(
    start_date: date,
    end_date: date,
    room_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Získá seznam rezervací s možností filtrace."""
    return await crud.get_reservations(db, start_date=start_date, end_date=end_date, room_id=room_id, status=status)

@router.post("/{reservation_id}/checkin", response_model=schemas.Reservation)
async def checkin_guest(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """
    Provede check-in hosta a změní stav pokoje na 'Obsazeno'.
    """
    return await crud.perform_check_in(db, reservation_id=reservation_id)

@router.post("/{reservation_id}/checkout", response_model=schemas.Reservation)
async def checkout_guest(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """
    Provede check-out hosta a změní stav pokoje na 'Volno - Čeká na úklid'.
    """
    return await crud.perform_check_out(db, reservation_id=reservation_id)

@router.get("/{reservation_id}/bill", response_model=schemas.Bill)
async def get_reservation_bill(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """Získá kompletní přehled účtu pro danou rezervaci."""
    return await crud.get_bill_for_reservation(db, reservation_id=reservation_id)

@router.post("/{reservation_id}/payment", status_code=201)
async def record_payment_for_reservation(
    reservation_id: int,
    payment_data: schemas.PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Zaznamená platbu k účtu rezervace."""
    await crud.record_payment(db, reservation_id=reservation_id, payment_data=payment_data)
    return {"message": "Platba byla úspěšně zaznamenána."}