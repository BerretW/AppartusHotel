# FILE: hotel_api/app/routers/rooms.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager, can_change_room_status

router = APIRouter(prefix="/rooms", tags=["Pokoje"])

@router.post("/", response_model=schemas.Room, status_code=status.HTTP_201_CREATED, dependencies=[Depends(is_admin_or_manager)])
async def create_room(room: schemas.RoomCreate, db: AsyncSession = Depends(get_db)):
    db_room = await crud.get_room_by_number(db, number=room.number)
    if db_room:
        raise HTTPException(status_code=400, detail=f"Pokoj s císlem {room.number} jiz existuje.")
    return await crud.create_room(db=db, room=room)

@router.get("/", response_model=List[schemas.Room])
async def read_rooms(
    status: Optional[schemas.RoomStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    rooms = await crud.get_rooms(db, status=status, skip=skip, limit=limit)
    return rooms

@router.patch("/{room_id}/status", response_model=schemas.Room, dependencies=[Depends(can_change_room_status)])
async def update_room_status(
    room_id: int,
    status_update: schemas.RoomUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    db_room = await db.get(models.Room, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Pokoj nebyl nalezen.")
    db_room.status = status_update.status
    await db.commit()
    await db.refresh(db_room)
    return db_room

# --- NOVÝ ENDPOINT ---
@router.patch("/{room_id}", response_model=schemas.Room, dependencies=[Depends(is_admin_or_manager)])
async def update_room_details(
    room_id: int,
    room_update: schemas.RoomUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Umožní upravit detaily pokoje (typ, kapacita, cena).
    Vyžaduje oprávnění 'majitel' nebo 'spravce'.
    """
    updated_room = await crud.update_room(db, room_id, room_update)
    if not updated_room:
        raise HTTPException(status_code=404, detail="Pokoj nebyl nalezen.")
    return updated_room

# --- NOVÝ ENDPOINT PRO ÚČTOVÁNÍ ---
@router.post("/{room_id}/charges", response_model=schemas.RoomCharge, status_code=201)
async def add_charge_to_room_bill(
    room_id: int,
    charge_data: schemas.RoomChargeCreate,
    db: AsyncSession = Depends(get_db)
    # TODO: Přidat závislost např. na recepční
):
    """
    Přidá položku na účet pokoje (např. konzumace z minibaru) a automaticky sníží stav zásob v minibaru.
    """
    return await crud.add_charge_to_room(db, room_id=room_id, charge_data=charge_data)