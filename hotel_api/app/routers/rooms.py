# FILE: hotel_api/app/routers/rooms.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager, can_change_room_status

router = APIRouter(prefix="/rooms", tags=["Pokoje"])

# --- Správa Pokojů ---
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

# --- NOVÉ: Správa Blokací Pokojů ---
@router.post("/blocks/", response_model=schemas.RoomBlock, status_code=201, dependencies=[Depends(is_admin_or_manager)])
async def create_a_room_block(
    block_data: schemas.RoomBlockCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Vytvoří blokaci pro pokoj na zadané období (např. z důvodu údržby).
    Pokoj nebude v tomto období nabízen k rezervaci.
    """
    return await crud.create_room_block(db, block=block_data)

@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(is_admin_or_manager)])
async def delete_a_room_block(
    block_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Odstraní existující blokaci pokoje.
    """
    await crud.delete_room_block(db, block_id=block_id)
    # Při statusu 204 se nevrací žádné tělo odpovědi