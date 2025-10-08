from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional  # <-- ZDE JE PŘIDÁN 'Optional'

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager, can_change_room_status

router = APIRouter(prefix="/rooms", tags=["Pokoje"])

@router.post("/", response_model=schemas.Room, status_code=status.HTTP_201_CREATED, dependencies=[Depends(is_admin_or_manager)])
async def create_room(room: schemas.RoomCreate, db: AsyncSession = Depends(get_db)):
    """Vytvoří nový pokoj a s ním asociovanou lokaci pro minibar."""
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
    """Vrátí seznam pokojů, volitelně filtrovaný podle stavu."""
    rooms = await crud.get_rooms(db, status=status, skip=skip, limit=limit)
    return rooms

@router.patch("/{room_id}/status", response_model=schemas.Room, dependencies=[Depends(can_change_room_status)])
async def update_room_status(
    room_id: int,
    status_update: schemas.RoomUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    """Aktualizuje stav pokoje (oprávnění: uklízečka, recepční, manažer)."""
    db_room = await db.get(models.Room, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Pokoj nebyl nalezen.")
    db_room.status = status_update.status
    await db.commit()
    await db.refresh(db_room)
    return db_room