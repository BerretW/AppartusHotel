# FILE: hotel_api/app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from . import models, schemas
from .security import get_password_hash
from datetime import date, datetime
from fastapi import HTTPException
from typing import List

# --- CRUD pro Uživatele (Users) ---
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def get_user_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(models.User.id)))
    return result.scalar_one()

async def get_employees(db: AsyncSession):
    employee_roles = [models.UserRole.uklizecka, models.UserRole.skladnik, models.UserRole.recepcni, models.UserRole.spravce]
    query = select(models.User).filter(models.User.role.in_(employee_roles))
    result = await db.execute(query)
    return result.scalars().all()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- CRUD pro Úkoly (Tasks) ---
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
    # --- Klíčová definice ---
    db_task = models.Task(
        title=task.title,
        notes=task.notes,
        assignee_id=task.assignee_id,
        due_date=task.due_date,
        room_id=task.room_id
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

# --- CRUD pro Pokoje (Rooms) ---
async def get_or_create_central_storage(db: AsyncSession):
    result = await db.execute(select(models.Location).filter(models.Location.name == "Centrální sklad"))
    storage = result.scalars().first()
    if not storage:
        storage = models.Location(name="Centrální sklad")
        db.add(storage)
        await db.commit()
        await db.refresh(storage)
    return storage

async def create_room(db: AsyncSession, room: schemas.RoomCreate):
    minibar_location = models.Location(name=f"Minibar Pokoje {room.number}")
    db.add(minibar_location)
    await db.flush()
    db_room = models.Room(**room.dict(), location_id=minibar_location.id)
    db.add(db_room)
    await db.commit()
    await db.refresh(db_room)
    return db_room

async def update_room(db: AsyncSession, room_id: int, room_update: schemas.RoomUpdate):
    db_room = await db.get(models.Room, room_id)
    if not db_room: return None
    update_data = room_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_room, key, value)
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

# --- CRUD pro Sklad (Inventory) ---
async def get_inventory_items(db: AsyncSession, skip: int = 0, limit: int = 100):
    query = select(models.InventoryItem).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

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
    result = await db.execute(select(models.Stock).filter_by(item_id=item_id, location_id=location_id))
    return result.scalars().first()

async def add_stock(db: AsyncSession, item_id: int, location_id: int, quantity: int):
    stock_entry = await get_stock_entry(db, item_id, location_id)
    if stock_entry: stock_entry.quantity += quantity
    else:
        stock_entry = models.Stock(item_id=item_id, location_id=location_id, quantity=quantity)
        db.add(stock_entry)
    await db.flush()
    return stock_entry

async def remove_stock(db: AsyncSession, item_id: int, location_id: int, quantity: int):
    stock_entry = await get_stock_entry(db, item_id, location_id)
    if not stock_entry or stock_entry.quantity < quantity:
        raise HTTPException(status_code=400, detail=f"Nedostatek polozky ID {item_id} v lokaci ID {location_id}")
    stock_entry.quantity -= quantity
    await db.flush()
    return stock_entry

async def transfer_stock(db: AsyncSession, transfer_data: schemas.StockTransfer):
    try:
        await remove_stock(db, transfer_data.item_id, transfer_data.source_location_id, transfer_data.quantity)
        await add_stock(db, transfer_data.item_id, transfer_data.destination_location_id, transfer_data.quantity)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

async def get_stock_by_location(db: AsyncSession, location_id: int):
    result = await db.execute(select(models.Stock).options(selectinload(models.Stock.item)).filter(models.Stock.location_id == location_id))
    return result.scalars().all()

async def create_receipt(db: AsyncSession, receipt_data: schemas.ReceiptDocumentCreate):
    central_storage = await get_or_create_central_storage(db)
    db_receipt = models.Receipt(supplier=receipt_data.supplier)
    db.add(db_receipt)
    await db.flush()
    try:
        for item_in in receipt_data.items:
            await add_stock(db, item_id=item_in.item_id, location_id=central_storage.id, quantity=item_in.quantity)
            db_receipt_item = models.ReceiptItem(receipt_id=db_receipt.id, item_id=item_in.item_id, quantity=item_in.quantity)
            db.add(db_receipt_item)
        await db.commit()
        await db.refresh(db_receipt)
        await db.refresh(db_receipt, attribute_names=['items'])
        return db_receipt
    except Exception as e:
        await db.rollback()
        raise e

# --- CRUD pro Rezervace a Hosty (Reservations & Guests) ---
async def get_or_create_guest(db: AsyncSession, name: str, email: str):
    result = await db.execute(select(models.Guest).filter(models.Guest.email == email))
    guest = result.scalars().first()
    if not guest:
        guest = models.Guest(name=name, email=email)
        db.add(guest)
        await db.commit()
        await db.refresh(guest)
    return guest

async def create_reservation(db: AsyncSession, res_data: schemas.ReservationCreate):
    guest = await get_or_create_guest(db, name=res_data.guest_name, email=res_data.guest_email)
    room = await db.get(models.Room, res_data.room_id)
    if not room: raise HTTPException(status_code=404, detail="Pokoj nebyl nalezen.")
    num_nights = (res_data.check_out_date - res_data.check_in_date).days
    total_price = num_nights * (room.price_per_night or 0)
    db_reservation = models.Reservation(
        room_id=res_data.room_id, guest_id=guest.id, check_in_date=res_data.check_in_date,
        check_out_date=res_data.check_out_date, total_price=total_price
    )
    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation, attribute_names=['room', 'guest'])
    return db_reservation

async def get_reservations(db: AsyncSession, start_date: date, end_date: date, room_id: int = None, status: str = None):
    query = select(models.Reservation).options(joinedload(models.Reservation.room), joinedload(models.Reservation.guest)).filter(
        models.Reservation.check_in_date <= end_date, models.Reservation.check_out_date >= start_date
    )
    if room_id: query = query.filter(models.Reservation.room_id == room_id)
    if status: query = query.filter(models.Reservation.status == status)
    result = await db.execute(query)
    return result.scalars().all()

async def perform_check_in(db: AsyncSession, reservation_id: int):
    reservation = await db.get(models.Reservation, reservation_id, options=[joinedload(models.Reservation.room)])
    if not reservation: raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    reservation.status = models.ReservationStatus.ubytovan
    reservation.room.status = models.RoomStatus.occupied
    await db.commit()
    await db.refresh(reservation, attribute_names=['room', 'guest'])
    return reservation

async def perform_check_out(db: AsyncSession, reservation_id: int):
    reservation = await db.get(models.Reservation, reservation_id, options=[joinedload(models.Reservation.room)])
    if not reservation: raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    reservation.status = models.ReservationStatus.odhlasen
    reservation.room.status = models.RoomStatus.available_dirty
    await db.commit()
    await db.refresh(reservation, attribute_names=['room', 'guest'])
    return reservation

# --- CRUD pro Účtování (Billing) ---
async def add_charge_to_room(db: AsyncSession, room_id: int, charge_data: schemas.RoomChargeCreate):
    res = await db.execute(select(models.Reservation).filter_by(room_id=room_id, status=models.ReservationStatus.ubytovan))
    reservation = res.scalars().first()
    if not reservation: raise HTTPException(status_code=400, detail="Pro tento pokoj neexistuje žádná aktivní (ubytovaná) rezervace.")
    item = await db.get(models.InventoryItem, charge_data.item_id)
    if not item: raise HTTPException(status_code=404, detail="Skladová položka nenalezena.")
    room = await db.get(models.Room, room_id)
    await remove_stock(db, item_id=item.id, location_id=room.location_id, quantity=charge_data.quantity)
    total_price = item.price * charge_data.quantity
    db_charge = models.RoomCharge(
        reservation_id=reservation.id, item_id=item.id, quantity=charge_data.quantity,
        price_per_item=item.price, total_price=total_price
    )
    db.add(db_charge)
    await db.commit()
    await db.refresh(db_charge, attribute_names=['item'])
    return db_charge

async def get_bill_for_reservation(db: AsyncSession, reservation_id: int) -> schemas.Bill:
    res = await db.execute(select(models.Reservation).options(
        joinedload(models.Reservation.room), joinedload(models.Reservation.guest),
        joinedload(models.Reservation.charges).joinedload(models.RoomCharge.item),
        joinedload(models.Reservation.payments)
    ).filter(models.Reservation.id == reservation_id))
    reservation = res.scalars().first()
    if not reservation: raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    total_charges = sum(c.total_price for c in reservation.charges) + (reservation.total_price or 0)
    total_paid = sum(p.amount for p in reservation.payments)
    return schemas.Bill(
        reservation_details=reservation, charges=reservation.charges,
        total_due=total_charges, total_paid=total_paid, balance=total_charges - total_paid
    )

async def record_payment(db: AsyncSession, reservation_id: int, payment_data: schemas.PaymentCreate):
    reservation = await db.get(models.Reservation, reservation_id)
    if not reservation: raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    db_payment = models.Payment(reservation_id=reservation_id, amount=payment_data.amount, method=payment_data.method)
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

# --- CRUD pro Dashboard ---
async def get_timeline_data(db: AsyncSession, start_date: date, end_date: date) -> List[schemas.RoomTimeline]:
    rooms_res = await db.execute(select(models.Room).order_by(models.Room.number))
    rooms = rooms_res.scalars().all()
    reservations_res = await db.execute(select(models.Reservation).options(joinedload(models.Reservation.guest)).filter(
        models.Reservation.check_in_date <= end_date, models.Reservation.check_out_date >= start_date))
    reservations = reservations_res.scalars().all()
    tasks_res = await db.execute(select(models.Task).options(joinedload(models.Task.assignee)).filter(
        models.Task.due_date >= start_date, models.Task.due_date <= end_date))
    tasks = tasks_res.scalars().all()
    room_map = {room.id: schemas.RoomTimeline(room_id=room.id, room_number=room.number, events=[]) for room in rooms}
    for res in reservations:
        if res.room_id in room_map:
            event = schemas.ReservationEvent(
                title=f"Rezervace: {res.guest.name}", start_date=datetime.combine(res.check_in_date, datetime.min.time()),
                end_date=datetime.combine(res.check_out_date, datetime.max.time()), reservation_id=res.id,
                guest_name=res.guest.name, status=res.status
            )
            room_map[res.room_id].events.append(event)
    for task in tasks:
        if task.room_id and task.room_id in room_map:
            event = schemas.TaskEvent(
                title=f"Úkol: {task.title}", start_date=datetime.combine(task.due_date, datetime.min.time()),
                end_date=datetime.combine(task.due_date, datetime.max.time()), task_id=task.id,
                assignee_email=task.assignee.email if task.assignee else "Nepřiřazeno", status=task.status
            )
            room_map[task.room_id].events.append(event)
    return list(room_map.values())

async def get_employees_schedule(db: AsyncSession, start_date: date, end_date: date) -> List[schemas.EmployeeSchedule]:
    tasks = await db.execute(select(models.Task).options(joinedload(models.Task.assignee), joinedload(models.Task.room)).filter(
        models.Task.due_date >= start_date, models.Task.due_date <= end_date, models.Task.assignee_id != None
    ).order_by(models.Task.assignee_id, models.Task.due_date))
    employee_tasks = {}
    for task in tasks.scalars().all():
        if task.assignee_id not in employee_tasks:
            employee_tasks[task.assignee_id] = {"employee": task.assignee, "tasks": []}
        employee_tasks[task.assignee_id]["tasks"].append(task)
    result = [schemas.EmployeeSchedule(employee=data["employee"], tasks=data["tasks"]) for data in employee_tasks.values()]
    return result

async def get_active_tasks(db: AsyncSession) -> List[schemas.ActiveTask]:
    active_tasks_res = await db.execute(select(models.Task).options(
        joinedload(models.Task.assignee), joinedload(models.Task.room)
    ).filter(models.Task.status == models.TaskStatus.probiha))
    active_tasks = []
    for task in active_tasks_res.scalars().all():
        if task.assignee:
            active_tasks.append(schemas.ActiveTask(
                task_id=task.id, title=task.title, status=task.status,
                employee=task.assignee, room=task.room
            ))
    return active_tasks