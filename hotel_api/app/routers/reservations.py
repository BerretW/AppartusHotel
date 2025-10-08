# FILE: hotel_api/app/routers/reservations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from .. import crud, schemas, models
from ..database import get_db
from ..dependencies import require_role

# Oprávnění pro recepční a vyšší
can_manage_reservations = require_role([models.UserRole.recepcni, models.UserRole.spravce, models.UserRole.majitel])

router = APIRouter(
    prefix="/reservations",
    tags=["Správa Rezervací (Interní)"],
    dependencies=[Depends(can_manage_reservations)]
)

@router.get("/", response_model=List[schemas.Reservation])
async def get_reservation_list(
    start_date: date,
    end_date: date,
    room_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Získá seznam rezervací pro interní účely s možností filtrace."""
    # Tato funkce `get_reservations` by se musela v crud.py rozšířit o nové filtry, pokud je potřeba.
    # Prozatím předpokládáme její základní funkčnost.
    return await crud.get_reservations(db, start_date=start_date, end_date=end_date, room_id=room_id, status=status)

@router.patch("/{reservation_id}", response_model=schemas.Reservation)
async def update_existing_reservation(
    reservation_id: int,
    reservation_update: schemas.ReservationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Upraví existující rezervaci (např. změní status na 'zruseno').
    """
    return await crud.update_reservation(db, reservation_id=reservation_id, res_update=reservation_update)

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
    """Získá kompletní přehled účtu (folio) pro danou rezervaci."""
    return await crud.get_bill_for_reservation(db, reservation_id=reservation_id)

@router.post("/{reservation_id}/charges", response_model=schemas.RoomCharge, status_code=201)
async def add_charge_to_reservation_bill(
    reservation_id: int,
    charge_data: schemas.RoomChargeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Přidá položku na účet rezervace (např. konzumace z minibaru, služba)
    a případně sníží stav zásob.
    """
    # Jednoduše zavoláme CRUD funkci. 
    # Transakce se automaticky `commit`ne na konci requestu.
    return await crud.add_charge_to_room(db, reservation_id=reservation_id, charge_data=charge_data)

@router.post("/{reservation_id}/payments", response_model=schemas.Payment, status_code=201)
async def record_payment_for_reservation(
    reservation_id: int,
    payment_data: schemas.PaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Zaznamená platbu k účtu rezervace."""
    return await crud.record_payment(db, reservation_id=reservation_id, payment_data=payment_data)