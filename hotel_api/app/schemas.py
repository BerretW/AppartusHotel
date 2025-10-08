from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from .models import UserRole, TaskStatus, RoomStatus

# ===================================================================
# Schémata pro Uživatele
# ===================================================================

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: UserRole

# Definuje, jak vypadá uživatel, když ho posíláme z databáze ven (bez hesla)
class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

# ===================================================================
# Schémata pro Úkoly (Tasks)
# ===================================================================

class TaskBase(BaseModel):
    title: str
    notes: Optional[str] = None

class TaskCreate(TaskBase):
    assignee_id: int
    due_date: date

class TaskUpdateStatus(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None
    
class Task(TaskBase):
    id: int
    due_date: datetime
    status: TaskStatus
    assignee_id: int

    class Config:
        from_attributes = True

# ===================================================================
# Schémata pro Pokoje (Rooms)
# ===================================================================

class RoomBase(BaseModel):
    number: str
    type: str = "Standard"
    capacity: int = 2

class RoomCreate(RoomBase):
    pass

class RoomUpdateStatus(BaseModel):
    status: RoomStatus

class Room(RoomBase):
    id: int
    status: RoomStatus
    location_id: Optional[int] = None

    class Config:
        from_attributes = True

# ===================================================================
# Schémata pro Sklad (Inventory)
# ===================================================================

class InventoryItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItem(InventoryItemBase):
    id: int

    class Config:
        from_attributes = True

class StockBase(BaseModel):
    item_id: int
    quantity: int

class Stock(StockBase):
    id: int
    location_id: int
    item: InventoryItem # Zobrazí celé info o položce

    class Config:
        from_attributes = True
        
class Location(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ReceiptItem(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0) # Množství musí být větší než 0

class ReceiptDocumentCreate(BaseModel):
    supplier: str
    items: List[ReceiptItem]

class StockTransfer(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)
    source_location_id: int
    destination_location_id: int

class ConsumptionLog(BaseModel):
    items: List[ReceiptItem]

# ===================================================================
# Schémata pro Autentizaci
# ===================================================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None