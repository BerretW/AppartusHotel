# FILE: hotel_api/app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from datetime import date, datetime
from .models import UserRole, TaskStatus, RoomStatus, ReservationStatus

# --- Schémata pro Uživatele ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole

class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    class Config: from_attributes = True

class Employee(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    class Config: from_attributes = True

# --- Schémata pro Úkoly (Tasks) ---
class TaskBase(BaseModel):
    title: str
    notes: Optional[str] = None

class TaskCreate(TaskBase):
    assignee_id: int
    due_date: date
    room_id: Optional[int] = None

class TaskUpdateStatus(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None
    
class Task(TaskBase):
    id: int
    due_date: date
    status: TaskStatus
    assignee_id: int
    room_id: Optional[int] = None
    class Config: from_attributes = True

# --- Schémata pro Pokoje ---
class RoomBase(BaseModel):
    number: str
    type: str = "Standard"
    capacity: int = 2

class RoomCreate(RoomBase): pass

class RoomUpdate(BaseModel):
    type: Optional[str] = None
    capacity: Optional[int] = None

class RoomUpdateStatus(BaseModel):
    status: RoomStatus

class Room(RoomBase):
    id: int
    status: RoomStatus
    location_id: int
    class Config: from_attributes = True

# NOVÉ: Schéma pro blokaci pokoje
class RoomBlockBase(BaseModel):
    reason: str
    start_date: date
    end_date: date
    room_id: int

class RoomBlockCreate(RoomBlockBase): pass

class RoomBlock(RoomBlockBase):
    id: int
    class Config: from_attributes = True

# --- Schémata pro Sklad (Inventory) ---
class InventoryItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0

class InventoryItemCreate(InventoryItemBase): pass

class InventoryItem(InventoryItemBase):
    id: int
    class Config: from_attributes = True

class StockBase(BaseModel):
    item_id: int
    quantity: int

class Stock(StockBase):
    id: int
    location_id: int
    item: InventoryItem
    class Config: from_attributes = True
        
class Location(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class ReceiptItemCreate(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)

class ReceiptItem(ReceiptItemCreate):
     class Config: from_attributes = True

class ReceiptDocumentCreate(BaseModel):
    supplier: str
    items: List[ReceiptItemCreate]

class ReceiptDocument(BaseModel):
    id: int
    supplier: str
    created_at: datetime
    items: List[ReceiptItem]
    class Config: from_attributes = True

class StockTransfer(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)
    source_location_id: int
    destination_location_id: int

# --- Schémata pro Rezervace a Účtování ---
class GuestBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    preferences: Optional[str] = None

class GuestCreate(GuestBase): pass

class Guest(GuestBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

class ReservationCreate(BaseModel):
    room_id: int
    guest_name: str
    guest_email: EmailStr
    check_in_date: date
    check_out_date: date
    rate_plan_id: int # NOVÉ: Rezervace se váže na cenový plán

class ReservationUpdate(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    status: Optional[ReservationStatus] = None

class Reservation(BaseModel):
    id: int
    check_in_date: date
    check_out_date: date
    status: ReservationStatus
    accommodation_price: float
    room: Room
    guest: Guest
    class Config: from_attributes = True

class RoomChargeCreate(BaseModel):
    description: str
    quantity: int = Field(..., gt=0)
    price_per_item: float
    item_id: Optional[int] = None # Může jít o službu

class RoomCharge(BaseModel):
    id: int
    description: str
    item: Optional[InventoryItem] = None
    quantity: int
    total_price: float
    charged_at: datetime
    class Config: from_attributes = True

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    method: str
    notes: Optional[str] = None
    
class Payment(PaymentCreate):
    id: int
    paid_at: datetime
    class Config: from_attributes = True

class Bill(BaseModel):
    reservation_details: Reservation
    charges: List[RoomCharge]
    payments: List[Payment]
    total_accommodation: float
    total_charges: float
    grand_total: float
    total_paid: float
    balance: float
    
# --- NOVÉ: Schémata pro Booking Engine (veřejná část) ---
class AvailabilityRequest(BaseModel):
    start_date: date
    end_date: date
    guests: int = Field(..., gt=0)

class AvailableRoomType(BaseModel):
    room_type: str
    capacity: int
    total_price: float
    rate_plan_id: int
    rate_plan_name: str

class PublicReservationRequest(BaseModel):
    room_type: str
    rate_plan_id: int
    guest_name: str
    guest_email: EmailStr
    phone: Optional[str] = None
    check_in_date: date
    check_out_date: date

# --- NOVÉ: Schémata pro dynamickou cenotvorbu ---
class RatePlanBase(BaseModel):
    name: str
    description: Optional[str] = None

class RatePlanCreate(RatePlanBase): pass

class RatePlan(RatePlanBase):
    id: int
    class Config: from_attributes = True

class RateBase(BaseModel):
    date: date
    price: float = Field(..., gt=0)
    room_type: str
    rate_plan_id: int

class RateCreate(RateBase): pass

class Rate(RateBase):
    id: int
    class Config: from_attributes = True

class RestrictionBase(BaseModel):
    date: date
    min_stay: Optional[int] = None
    closed_to_arrival: Optional[bool] = None
    room_type: str
    rate_plan_id: int
    
class RestrictionCreate(RestrictionBase): pass

class Restriction(RestrictionBase):
    id: int
    class Config: from_attributes = True
    
# --- Schémata pro Dashboard a Kalendář (zůstávají stejná) ---
class EventBase(BaseModel):
    title: str
    start_date: datetime
    end_date: datetime

class ReservationEvent(EventBase):
    type: str = "reservation"
    reservation_id: int
    guest_name: str
    status: ReservationStatus

class TaskEvent(EventBase):
    type: str = "task"
    task_id: int
    assignee_email: Optional[str]
    status: TaskStatus
    
# NOVÉ: Událost pro blokaci
class BlockEvent(EventBase):
    type: str = "block"
    block_id: int
    reason: str

TimelineEvent = Union[ReservationEvent, TaskEvent, BlockEvent]

class RoomTimeline(BaseModel):
    room_id: int
    room_number: str
    events: List[TimelineEvent]

class TaskWithDetails(Task):
    room: Optional[Room] = None
    assignee: Employee
    class Config: from_attributes = True

class EmployeeSchedule(BaseModel):
    employee: Employee
    tasks: List[TaskWithDetails]

class ActiveTask(BaseModel):
    task_id: int
    title: str
    status: TaskStatus
    employee: Employee
    room: Optional[Room]
    class Config: from_attributes = True

# --- Schémata pro Autentizaci (zůstávají stejná) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None