from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from . import models, schemas
from .security import get_password_hash
from datetime import date, datetime
from fastapi import HTTPException

# ===================================================================
# CRUD pro Uživatele (Users)
# ===================================================================

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def get_user_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(models.User.id)))
    return result.scalar_one()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# ===================================================================
# CRUD pro Úkoly (Tasks)
# ===================================================================

async def get_task_by_id(db: AsyncSession, task_id: int):
    result = await db.execute(select(models.Task).filter(models.Task.id == task_id))
    return result.scalars().first()

async def get_tasks_for_user(db: AsyncSession, user_id: int, start_date: date, end_date: date):
    query = select(models.Task).filter(
        models.Task.assignee_id == user_id,
        models.Task.due_date >= start_date,
        models.Task.due_date <= end_date
    )
    result = await db.execute(query)
    return result.scalars().all()

async def create_task(db: AsyncSession, task: schemas.TaskCreate):
    db_task = models.Task(
        title=task.title,
        notes=task.notes,
        assignee_id=task.assignee_id,
        due_date=task.due_date
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

# ===================================================================
# CRUD pro Pokoje (Rooms)
# ===================================================================

async def get_or_create_central_storage(db: AsyncSession):
    """Najde nebo vytvoří Centrální sklad."""
    result = await db.execute(select(models.Location).filter(models.Location.name == "Centrální sklad"))
    storage = result.scalars().first()
    if not storage:
        storage = models.Location(name="Centrální sklad")
        db.add(storage)
        await db.commit()
        await db.refresh(storage)
    return storage

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

# ===================================================================
# CRUD pro Sklad (Inventory)
# ===================================================================

async def create_inventory_item(db: AsyncSession, item: schemas.InventoryItemCreate):
    db_item = models.InventoryItem(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def get_locations(db: AsyncSession):
    result = await db.execute(select(models.Location))
    return result.scalars().all()

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
    await db.flush() # Použijeme flush místo commit, aby se operace stala součástí větší transakce
    return stock_entry

async def remove_stock(db: AsyncSession, item_id: int, location_id: int, quantity: int):
    stock_entry = await get_stock_entry(db, item_id, location_id)
    if not stock_entry or stock_entry.quantity < quantity:
        raise HTTPException(status_code=400, detail=f"Nedostatek polozky ID {item_id} v lokaci ID {location_id}")
    stock_entry.quantity -= quantity
    await db.flush() # Použijeme flush místo commit
    return stock_entry

async def transfer_stock(db: AsyncSession, transfer_data: schemas.StockTransfer):
    # session handleuje transakci automaticky
    try:
        await remove_stock(db, transfer_data.item_id, transfer_data.source_location_id, transfer_data.quantity)
        await add_stock(db, transfer_data.item_id, transfer_data.destination_location_id, transfer_data.quantity)
        await db.commit()
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

async def create_receipt(db: AsyncSession, receipt_data: schemas.ReceiptDocumentCreate):
    """Zpracuje příjemku a navýší zásoby v centrálním skladu."""
    central_storage = await get_or_create_central_storage(db)
    
    db_receipt = models.Receipt(supplier=receipt_data.supplier)
    db.add(db_receipt)
    await db.flush()

    try:
        for item_in in receipt_data.items:
            # Přidání položek na sklad
            await add_stock(db, item_id=item_in.item_id, location_id=central_storage.id, quantity=item_in.quantity)
            
            # Vytvoření záznamu o položce na příjemce
            db_receipt_item = models.ReceiptItem(
                receipt_id=db_receipt.id,
                item_id=item_in.item_id,
                quantity=item_in.quantity
            )
            db.add(db_receipt_item)
        
        await db.commit()
        await db.refresh(db_receipt)
        # Načteme i související položky pro plnou odpověď
        await db.refresh(db_receipt, attribute_names=['items'])
        return db_receipt
    except Exception as e:
        await db.rollback()
        raise e