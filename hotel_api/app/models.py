from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship, backref
from .database import Base
import enum
from datetime import datetime

# --- Stávající modely ---

class UserRole(str, enum.Enum):
    majitel = "majitel"
    spravce = "spravce"
    recepcni = "recepcni"
    skladnik = "skladnik"
    uklizecka = "uklizecka"
    host = "host"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.uklizecka)
    is_active = Column(Boolean, default=True)
    tasks = relationship("Task", back_populates="assignee", cascade="all, delete-orphan")

class TaskStatus(str, enum.Enum):
    cekajici = "čekající"
    probiha = "probíhá"
    dokonceno = "dokončeno"
    zablokovano = "zablokováno"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    due_date = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.cekajici)
    notes = Column(String(1000), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    assignee = relationship("User", back_populates="tasks")

# --- Nové modely pro Pokoje a Sklad ---

class RoomStatus(str, enum.Enum):
    available_clean = "Volno - Uklizeno"
    available_dirty = "Volno - Čeká na úklid"
    occupied = "Obsazeno"
    cleaning_in_progress = "Probíhá úklid"
    under_maintenance = "V údržbě"

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(10), unique=True, index=True, nullable=False)
    type = Column(String(100), nullable=False, default="Standard")
    capacity = Column(Integer, default=2)
    status = Column(SQLAlchemyEnum(RoomStatus), default=RoomStatus.available_clean)
    # Vztah k lokaci (pro minibar)
    location_id = Column(Integer, ForeignKey("locations.id"))
    location = relationship("Location", back_populates="room")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False) # Např. "Centrální sklad", "Minibar Pokoje 101"
    # Vztah zpět k pokoji, pokud je to lokace pokoje
    room = relationship("Room", back_populates="location", uselist=False)
    stock_items = relationship("Stock", back_populates="location")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False) # Např. "Coca-Cola 0.33l"
    description = Column(String(1000))
    price = Column(Float, default=0.0) # Prodejní cena, např. z minibaru

class Stock(Base):
    __tablename__ = "stock"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    item_id = Column(Integer, ForeignKey("inventory_items.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    item = relationship("InventoryItem")
    location = relationship("Location", back_populates="stock_items")