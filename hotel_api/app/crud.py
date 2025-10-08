from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from . import models, schemas
from .security import get_password_hash
from datetime import date, datetime, time
from fastapi import HTTPException, status

# ... (všechny stávající CRUD funkce pro User a Task) ...

# --- Nové CRUD funkce pro Pokoje ---
async def create_room(db: AsyncSession, room: schemas.RoomCreate):
    # Nejprve vytvoříme lokaci pro minibar
    minibar_location = models.Location(name=f"Minibar Pokoje {room.number}")
    db.add(minibar_location)
    await db.flush() # Potřebujeme ID pro pokoj

    db_room = models.Room(**room.dict(), location_id=minibar_location.id)
    db.add(db_room)
    await db.commit()
    await db.refresh(db_room)
    return db_room

async def get_room_by_number(db: AsyncSession, number: str):
    result = await db.execute(select(models.Room).filter(models.Room.number == number))
    return result.scalars().first()

async def get_rooms(db: AsyncSession, status: schemas.RoomStatus = None, skip: int = 0, limit: int = 100):
    query = select(models.Room).offset(skip).limit(limit)
    if status:
        query = query.filter(models.Room.status == status)
    result = await db.execute(query)
    return result.scalars().all()

# --- Nové CRUD funkce pro Sklad ---

async def create_inventory_item(db: AsyncSession, item: schemas.InventoryItemCreate):
    db_item = models.InventoryItem(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def get_stock_entry(db: AsyncSession, item_id: int, location_id: int):
    result = await db.execute(
        select(models.Stock).filter_by(item_id=item_id, location_id=location_id)
    )
    return result.scalars().first()

async def add_stock(db: AsyncSession, item_id: int, location_id: int, quantity: int):
    stock_entry = await get_stock_entry(db, item_id, location_id)
    if stock_entry:
        stock_entry.quantity += quantity
    else:
        stock_entry = models.Stock(item_id=item_id, location_id=location_id, quantity=quantity)
        db.add(stock_entry)
    await db.commit()
    return stock_entry

async def remove_stock(db: AsyncSession, item_id: int, location_id: int, quantity: int):
    stock_entry = await get_stock_entry(db, item_id, location_id)
    if not stock_entry or stock_entry.quantity < quantity:
        raise HTTPException(status_code=400, detail=f"Nedostatek polozky ID {item_id} v lokaci ID {location_id}")
    stock_entry.quantity -= quantity
    await db.commit()
    return stock_entry

async def transfer_stock(db: AsyncSession, transfer_data: schemas.StockTransfer):
    # Toto by mělo být v transakci, což session handleuje automaticky
    try:
        await remove_stock(db, transfer_data.item_id, transfer_data.source_location_id, transfer_data.quantity)
        await add_stock(db, transfer_data.item_id, transfer_data.destination_location_id, transfer_data.quantity)
    except Exception as e:
        await db.rollback()
        raise e
    
async def get_stock_by_location(db: AsyncSession, location_id: int):
    result = await db.execute(
        select(models.Stock)
        .options(selectinload(models.Stock.item))
        .filter(models.Stock.location_id == location_id)
    )
    return result.scalars().all()