from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, ForeignKey, DateTime, Boolean, Float, Date
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime

# --- Enumy pro stavy a role ---

class UserRole(str, enum.Enum):
    majitel = "majitel"
    spravce = "spravce"
    recepcni = "recepcni"
    skladnik = "skladnik"
    uklizecka = "uklizecka"
    host = "host"

class TaskStatus(str, enum.Enum):
    cekajici = "čekající"
    probiha = "probíhá"
    dokonceno = "dokončeno"
    zablokovano = "zablokováno"

class RoomStatus(str, enum.Enum):
    available_clean = "Volno - Uklizeno"
    available_dirty = "Volno - Čeká na úklid"
    occupied = "Obsazeno"
    cleaning_in_progress = "Probíhá úklid"
    under_maintenance = "V údržbě"

# --- Modely Tabulek ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.host)
    is_active = Column(Boolean, default=True)
    
    tasks_assigned = relationship("Task", back_populates="assignee", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.cekajici)
    notes = Column(String(1000), nullable=True)
    
    assignee_id = Column(Integer, ForeignKey("users.id"))
    assignee = relationship("User", back_populates="tasks_assigned")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(10), unique=True, index=True, nullable=False)
    type = Column(String(100), nullable=False, default="Standard")
    capacity = Column(Integer, default=2)
    status = Column(SQLAlchemyEnum(RoomStatus), default=RoomStatus.available_clean)
    
    location_id = Column(Integer, ForeignKey("locations.id"))
    location = relationship("Location", back_populates="room")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    
    room = relationship("Room", back_populates="location", uselist=False)
    stock_items = relationship("Stock", back_populates="location")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(1000))
    price = Column(Float, default=0.0)

class Stock(Base):
    __tablename__ = "stock"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    item = relationship("InventoryItem")
    location = relationship("Location", back_populates="stock_items")

class Receipt(Base):
    __tablename__ = "receipts"
    id = Column(Integer, primary_key=True, index=True)
    supplier = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    items = relationship("ReceiptItem", back_populates="receipt")

class ReceiptItem(Base):
    __tablename__ = "receipt_items"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    
    receipt = relationship("Receipt", back_populates="items")
    item = relationship("InventoryItem")