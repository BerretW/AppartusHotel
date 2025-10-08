# FILE: hotel_api/app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import selectinload, joinedload
from . import models, schemas
from .security import get_password_hash
from datetime import date, datetime, timedelta
from fastapi import HTTPException
from typing import List, Dict

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
    db_task = models.Task(**task.dict())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

# --- CRUD pro Pokoje (Rooms) ---
async def create_room(db: AsyncSession, room: schemas.RoomCreate):
    minibar_location = models.Location(name=f"Minibar Pokoje {room.number}")
    db.add(minibar_location)
    await db.flush()
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

async def create_room_block(db: AsyncSession, block: schemas.RoomBlockCreate):
    db_block = models.RoomBlock(**block.dict())
    db.add(db_block)
    await db.commit()
    await db.refresh(db_block)
    return db_block

async def delete_room_block(db: AsyncSession, block_id: int):
    db_block = await db.get(models.RoomBlock, block_id)
    if not db_block:
        raise HTTPException(status_code=404, detail="Blokace nenalezena.")
    await db.delete(db_block)
    await db.commit()

# --- CRUD pro Sklad (Inventory) ---
async def get_or_create_central_storage(db: AsyncSession):
    result = await db.execute(select(models.Location).filter(models.Location.name == "Centrální sklad"))
    storage = result.scalars().first()
    if not storage:
        storage = models.Location(name="Centrální sklad")
        db.add(storage)
        await db.commit()
        await db.refresh(storage)
    return storage

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
    if stock_entry:
        stock_entry.quantity += quantity
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
    async with db.begin():
        await remove_stock(db, transfer_data.item_id, transfer_data.source_location_id, transfer_data.quantity)
        await add_stock(db, transfer_data.item_id, transfer_data.destination_location_id, transfer_data.quantity)

async def create_receipt(db: AsyncSession, receipt_data: schemas.ReceiptDocumentCreate):
    async with db.begin():
        central_storage = await get_or_create_central_storage(db)
        db_receipt = models.Receipt(supplier=receipt_data.supplier)
        db.add(db_receipt)
        await db.flush()
        for item_in in receipt_data.items:
            await add_stock(db, item_id=item_in.item_id, location_id=central_storage.id, quantity=item_in.quantity)
            db_receipt_item = models.ReceiptItem(receipt_id=db_receipt.id, item_id=item_in.item_id, quantity=item_in.quantity)
            db.add(db_receipt_item)
        await db.refresh(db_receipt, attribute_names=['items'])
    return db_receipt

# --- CRUD pro Dynamickou Cenotvorbu ---
async def create_rate_plan(db: AsyncSession, plan: schemas.RatePlanCreate):
    db_plan = models.RatePlan(**plan.dict())
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

async def get_rate_plans(db: AsyncSession):
    result = await db.execute(select(models.RatePlan))
    return result.scalars().all()

async def create_rates_batch(db: AsyncSession, rates: List[schemas.RateCreate]):
    db_rates = [models.Rate(**r.dict()) for r in rates]
    db.add_all(db_rates)
    await db.commit()
    return db_rates

async def calculate_accommodation_price(db: AsyncSession, start_date: date, end_date: date, room_type: str, rate_plan_id: int) -> float:
    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="Datum odjezdu musí být po datu příjezdu.")
    stay_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days)]
    query = select(models.Rate).filter(
        models.Rate.date.in_(stay_dates),
        models.Rate.room_type == room_type,
        models.Rate.rate_plan_id == rate_plan_id
    )
    result = await db.execute(query)
    rates_map = {r.date: r.price for r in result.scalars().all()}
    if len(rates_map) != len(stay_dates):
        missing_dates = [d.isoformat() for d in stay_dates if d not in rates_map]
        raise HTTPException(status_code=404, detail=f"Cena nebyla nalezena pro dny: {', '.join(missing_dates)}")
    return sum(rates_map.values())

# --- CRUD pro Dostupnost a Rezervace ---
async def find_available_room_types(db: AsyncSession, start_date: date, end_date: date, guests: int) -> List[schemas.AvailableRoomType]:
    rooms_with_capacity_q = select(models.Room).filter(models.Room.capacity >= guests)
    potential_rooms = (await db.execute(rooms_with_capacity_q)).scalars().all()
    potential_room_ids = [r.id for r in potential_rooms]
    if not potential_room_ids:
        return []
    occupied_rooms_q = select(distinct(models.Reservation.room_id)).filter(models.Reservation.room_id.in_(potential_room_ids), models.Reservation.status.in_([models.ReservationStatus.potvrzeno, models.ReservationStatus.ubytovan]), models.Reservation.check_in_date < end_date, models.Reservation.check_out_date > start_date)
    blocked_rooms_q = select(distinct(models.RoomBlock.room_id)).filter(models.RoomBlock.room_id.in_(potential_room_ids), models.RoomBlock.start_date < end_date, models.RoomBlock.end_date > start_date)
    occupied_room_ids = (await db.execute(occupied_rooms_q)).scalars().all()
    blocked_room_ids = (await db.execute(blocked_rooms_q)).scalars().all()
    unavailable_room_ids = set(occupied_room_ids) | set(blocked_room_ids)
    available_rooms_by_type: Dict[str, List[models.Room]] = {}
    for room in potential_rooms:
        if room.id not in unavailable_room_ids:
            if room.type not in available_rooms_by_type:
                available_rooms_by_type[room.type] = []
            available_rooms_by_type[room.type].append(room)
    availability_result = []
    rate_plans = await get_rate_plans(db)
    for room_type, rooms in available_rooms_by_type.items():
        for plan in rate_plans:
            try:
                price = await calculate_accommodation_price(db, start_date, end_date, room_type, plan.id)
                availability_result.append(schemas.AvailableRoomType(room_type=room_type, capacity=rooms[0].capacity, total_price=price, rate_plan_id=plan.id, rate_plan_name=plan.name))
            except HTTPException as e:
                if e.status_code == 404: continue
                raise e
    return availability_result

async def get_or_create_guest(db: AsyncSession, name: str, email: str, phone: str = None, preferences: str = None):
    result = await db.execute(select(models.Guest).filter(models.Guest.email == email))
    guest = result.scalars().first()
    if not guest:
        guest = models.Guest(name=name, email=email, phone=phone, preferences=preferences)
        db.add(guest)
        await db.commit()
        await db.refresh(guest)
    return guest

async def create_reservation(db: AsyncSession, res_data: schemas.PublicReservationRequest):
    try:
        price = await calculate_accommodation_price(db, res_data.check_in_date, res_data.check_out_date, res_data.room_type, res_data.rate_plan_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=400, detail="Pro zadané období a typ pokoje neexistuje platný ceník.")
        raise e
    rooms_of_type_q = select(models.Room.id).filter(models.Room.type == res_data.room_type)
    potential_room_ids = (await db.execute(rooms_of_type_q)).scalars().all()
    if not potential_room_ids:
        raise HTTPException(status_code=404, detail=f"Nenalezen žádný pokoj typu '{res_data.room_type}'.")
    occupied_rooms_q = select(distinct(models.Reservation.room_id)).filter(models.Reservation.room_id.in_(potential_room_ids), models.Reservation.status.in_([models.ReservationStatus.potvrzeno, models.ReservationStatus.ubytovan]), models.Reservation.check_in_date < res_data.check_out_date, models.Reservation.check_out_date > res_data.check_in_date)
    blocked_rooms_q = select(distinct(models.RoomBlock.room_id)).filter(models.RoomBlock.room_id.in_(potential_room_ids), models.RoomBlock.start_date < res_data.check_out_date, models.RoomBlock.end_date > res_data.check_in_date)
    occupied_room_ids = (await db.execute(occupied_rooms_q)).scalars().all()
    blocked_room_ids = (await db.execute(blocked_rooms_q)).scalars().all()
    unavailable_room_ids = set(occupied_room_ids) | set(blocked_room_ids)
    available_room_id = next((room_id for room_id in potential_room_ids if room_id not in unavailable_room_ids), None)
    if not available_room_id:
        raise HTTPException(status_code=409, detail="Bohužel, tento typ pokoje byl právě zarezervován.")
    guest = await get_or_create_guest(db, name=res_data.guest_name, email=res_data.guest_email, phone=res_data.phone)
    db_reservation = models.Reservation(room_id=available_room_id, guest_id=guest.id, check_in_date=res_data.check_in_date, check_out_date=res_data.check_out_date, accommodation_price=price, status=models.ReservationStatus.potvrzeno)
    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation, attribute_names=['room', 'guest'])
    return db_reservation

async def update_reservation(db: AsyncSession, reservation_id: int, res_update: schemas.ReservationUpdate):
    db_res = await db.get(models.Reservation, reservation_id)
    if not db_res:
        raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
        
    for key, value in res_update.dict(exclude_unset=True).items():
        setattr(db_res, key, value)
        
    await db.commit()
    
    # Po commitu znovu načteme objekt i jeho relace
    await db.refresh(db_res, attribute_names=['room', 'guest'])
    
    return db_res

async def perform_check_in(db: AsyncSession, reservation_id: int):
    reservation = await db.get(models.Reservation, reservation_id, options=[joinedload(models.Reservation.room)])
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    
    reservation.status = models.ReservationStatus.ubytovan
    reservation.room.status = models.RoomStatus.occupied
    
    await db.commit()
    
    # Po commitu znovu načteme objekt i jeho relace
    await db.refresh(reservation, attribute_names=['room', 'guest'])
    # Zajistíme, že i samotný pokoj má načtené čerstvé atributy
    await db.refresh(reservation.room)
    
    return reservation

async def perform_check_out(db: AsyncSession, reservation_id: int):
    reservation = await db.get(models.Reservation, reservation_id, options=[joinedload(models.Reservation.room)])
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
        
    reservation.status = models.ReservationStatus.odhlasen
    reservation.room.status = models.RoomStatus.available_dirty
    
    await db.commit()
    
    # Po commitu znovu načteme objekt i jeho relace
    await db.refresh(reservation, attribute_names=['room', 'guest'])
    await db.refresh(reservation.room)
    
    return reservation
# --- CRUD pro Účtování (Billing) ---

# **** KLÍČOVÁ OPRAVA ZDE ****
async def add_charge_to_room(db: AsyncSession, reservation_id: int, charge_data: schemas.RoomChargeCreate):
    # Načteme rezervaci
    res = await db.get(models.Reservation, reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    
    total_price = charge_data.price_per_item * charge_data.quantity
    
    # Pokud je položka ze skladu, snížíme stav
    if charge_data.item_id:
        room = await db.get(models.Room, res.room_id)
        if room and room.location_id:
            await remove_stock(db, item_id=charge_data.item_id, location_id=room.location_id, quantity=charge_data.quantity)

    db_charge = models.RoomCharge(
        reservation_id=reservation_id, # Explicitně přiřadíme ID
        description=charge_data.description,
        quantity=charge_data.quantity,
        price_per_item=charge_data.price_per_item,
        total_price=total_price,
        item_id=charge_data.item_id
    )
    
    db.add(db_charge)
    await db.commit()

    await db.refresh(db_charge)
    return db_charge

# **** KLÍČOVÁ OPRAVA ZDE ****
async def get_bill_for_reservation(db: AsyncSession, reservation_id: int) -> schemas.Bill:
    # Dotaz s `selectinload` je sám o sobě dostatečně robustní,
    # aby načetl všechna potřebná data přímo z databáze.
    # Chybný řádek byl odstraněn.
    
    result = await db.execute(
        select(models.Reservation)
        .where(models.Reservation.id == reservation_id)
        .options(
            selectinload(models.Reservation.room), 
            selectinload(models.Reservation.guest),
            selectinload(models.Reservation.charges).selectinload(models.RoomCharge.item),
            selectinload(models.Reservation.payments)
        )
    )
    reservation = result.scalars().first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    
    total_charges = sum(c.total_price for c in reservation.charges)
    total_accommodation = reservation.accommodation_price or 0
    grand_total = total_accommodation + total_charges
    total_paid = sum(p.amount for p in reservation.payments)
    
    return schemas.Bill(
        reservation_details=reservation, 
        charges=reservation.charges,
        payments=reservation.payments,
        total_accommodation=total_accommodation,
        total_charges=total_charges,
        grand_total=grand_total,
        total_paid=total_paid,
        balance=grand_total - total_paid
    )

async def record_payment(db: AsyncSession, reservation_id: int, payment_data: schemas.PaymentCreate):
    reservation = await db.get(models.Reservation, reservation_id)
    if not reservation: raise HTTPException(status_code=404, detail="Rezervace nenalezena.")
    db_payment = models.Payment(reservation_id=reservation_id, amount=payment_data.amount, method=payment_data.method, notes=payment_data.notes)
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

# --- CRUD pro Dashboard ---
async def get_timeline_data(db: AsyncSession, start_date: date, end_date: date) -> List[schemas.RoomTimeline]:
    rooms = (await db.execute(select(models.Room).order_by(models.Room.number))).scalars().all()
    reservations = (await db.execute(select(models.Reservation).options(joinedload(models.Reservation.guest)).filter(models.Reservation.check_in_date <= end_date, models.Reservation.check_out_date >= start_date))).scalars().all()
    tasks = (await db.execute(select(models.Task).options(joinedload(models.Task.assignee)).filter(models.Task.due_date >= start_date, models.Task.due_date <= end_date))).scalars().all()
    blocks = (await db.execute(select(models.RoomBlock).filter(models.RoomBlock.start_date <= end_date, models.RoomBlock.end_date >= start_date))).scalars().all()
    room_map = {room.id: schemas.RoomTimeline(room_id=room.id, room_number=room.number, events=[]) for room in rooms}
    for res in reservations:
        if res.room_id in room_map:
            room_map[res.room_id].events.append(schemas.ReservationEvent(title=f"Rezervace: {res.guest.name}", start_date=datetime.combine(res.check_in_date, datetime.min.time()), end_date=datetime.combine(res.check_out_date, datetime.min.time()), reservation_id=res.id, guest_name=res.guest.name, status=res.status))
    for task in tasks:
        if task.room_id and task.room_id in room_map:
            room_map[task.room_id].events.append(schemas.TaskEvent(title=f"Úkol: {task.title}", start_date=datetime.combine(task.due_date, datetime.min.time()), end_date=datetime.combine(task.due_date, datetime.max.time()), task_id=task.id, assignee_email=task.assignee.email if task.assignee else "Nepřiřazeno", status=task.status))
    for block in blocks:
        if block.room_id in room_map:
            room_map[block.room_id].events.append(schemas.BlockEvent(title=f"Blokace: {block.reason}", start_date=datetime.combine(block.start_date, datetime.min.time()), end_date=datetime.combine(block.end_date, datetime.min.time()), block_id=block.id, reason=block.reason))
    return list(room_map.values())

async def get_employees_schedule(db: AsyncSession, start_date: date, end_date: date) -> List[schemas.EmployeeSchedule]:
    tasks_res = await db.execute(select(models.Task).options(joinedload(models.Task.assignee), joinedload(models.Task.room)).filter(models.Task.due_date >= start_date, models.Task.due_date <= end_date, models.Task.assignee_id != None).order_by(models.Task.assignee_id, models.Task.due_date))
    employee_tasks = {}
    for task in tasks_res.scalars().all():
        if task.assignee_id not in employee_tasks:
            employee_tasks[task.assignee_id] = {"employee": task.assignee, "tasks": []}
        employee_tasks[task.assignee_id]["tasks"].append(task)
    return [schemas.EmployeeSchedule(employee=data["employee"], tasks=data["tasks"]) for data in employee_tasks.values()]

async def get_active_tasks(db: AsyncSession) -> List[schemas.ActiveTask]:
    active_tasks_res = await db.execute(select(models.Task).options(joinedload(models.Task.assignee), joinedload(models.Task.room)).filter(models.Task.status == models.TaskStatus.probiha))
    active_tasks = []
    for task in active_tasks_res.scalars().all():
        if task.assignee:
            active_tasks.append(schemas.ActiveTask(task_id=task.id, title=task.title, status=task.status, employee=task.assignee, room=task.room))
    return active_tasks