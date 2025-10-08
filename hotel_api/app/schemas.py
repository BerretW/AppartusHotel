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
    # --- Klíčová definice ---
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

# --- Schémata pro Pokoje (Rooms) ---
class RoomBase(BaseModel):
    number: str
    type: str = "Standard"
    capacity: int = 2
    price_per_night: Optional[float] = None

class RoomCreate(RoomBase): pass

class RoomUpdate(BaseModel):
    type: Optional[str] = None
    capacity: Optional[int] = None
    price_per_night: Optional[float] = None

class RoomUpdateStatus(BaseModel):
    status: RoomStatus

class Room(RoomBase):
    id: int
    status: RoomStatus
    location_id: int
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

class GuestCreate(GuestBase): pass

class Guest(GuestBase):
    id: int
    class Config: from_attributes = True

class ReservationCreate(BaseModel):
    room_id: int
    guest_name: str
    guest_email: EmailStr
    check_in_date: date
    check_out_date: date

class Reservation(BaseModel):
    id: int
    check_in_date: date
    check_out_date: date
    status: ReservationStatus
    room: Room
    guest: Guest
    class Config: from_attributes = True

class RoomChargeCreate(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)

class RoomCharge(BaseModel):
    id: int
    item: InventoryItem
    quantity: int
    total_price: float
    charged_at: datetime
    class Config: from_attributes = True

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    method: str

class Bill(BaseModel):
    reservation_details: Reservation
    charges: List[RoomCharge]
    total_due: float
    total_paid: float
    balance: float
    
# --- Schémata pro Dashboard a Kalendář ---
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

TimelineEvent = Union[ReservationEvent, TaskEvent]

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

# --- Schémata pro Autentizaci ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None