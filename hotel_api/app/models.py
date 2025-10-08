# FILE: hotel_api/app/models.py
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

class ReservationStatus(str, enum.Enum):
    potvrzeno = "potvrzeno"
    ubytovan = "ubytován"
    odhlasen = "odhlášen"
    zruseno = "zrušeno"
    no_show = "no-show"  # NOVÝ STAV

# --- Modely Tabulek ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.host)
    is_active = Column(Boolean, default=True)
    
    tasks_assigned = relationship("Task", back_populates="assignee")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.cekajici)
    notes = Column(String(1000), nullable=True)
    
    assignee_id = Column(Integer, ForeignKey("users.id"))
    assignee = relationship("User", back_populates="tasks_assigned")
    
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    room = relationship("Room", back_populates="tasks")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), unique=True, index=True, nullable=False)
    type = Column(String(100), nullable=False, default="Standard")
    capacity = Column(Integer, default=2)
    # price_per_night = Column(Float, default=1000.0) # TOTO POLE JE NAHRAZENO CENOVÝMI PLÁNY
    status = Column(SQLAlchemyEnum(RoomStatus), default=RoomStatus.available_clean)
    
    location_id = Column(Integer, ForeignKey("locations.id"))
    location = relationship("Location", back_populates="room")
    reservations = relationship("Reservation", back_populates="room")
    tasks = relationship("Task", back_populates="room")
    blocks = relationship("RoomBlock", back_populates="room") # NOVÁ RELACE

# NOVÝ MODEL: Blokace pokojů (pro údržbu atd.)
class RoomBlock(Base):
    __tablename__ = "room_blocks"
    id = Column(Integer, primary_key=True, index=True)
    reason = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    room = relationship("Room", back_populates="blocks")

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

class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    
    # NOVÁ POLE pro CRM
    preferences = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="guest")

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    status = Column(SQLAlchemyEnum(ReservationStatus), default=ReservationStatus.potvrzeno)
    
    # Změna: cena za ubytování je nyní oddělená
    accommodation_price = Column(Float, nullable=False, default=0.0)
    
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    
    # NOVÁ POLE
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    room = relationship("Room", back_populates="reservations")
    guest = relationship("Guest", back_populates="reservations")
    charges = relationship("RoomCharge", back_populates="reservation")
    payments = relationship("Payment", back_populates="reservation")

# ... (ostatní modely zůstávají stejné)

class RoomCharge(Base):
    __tablename__ = "room_charges"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False) # NOVÉ POLE
    quantity = Column(Integer, nullable=False)
    price_per_item = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    charged_at = Column(DateTime, default=datetime.utcnow)
    
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True) # Může být i služba bez vazby na sklad
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    
    item = relationship("InventoryItem")
    reservation = relationship("Reservation", back_populates="charges")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    method = Column(String(50), nullable=False)
    notes = Column(String(255), nullable=True) # NOVÉ POLE
    paid_at = Column(DateTime, default=datetime.utcnow)
    
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    reservation = relationship("Reservation", back_populates="payments")

# --- NOVÁ SEKCE: DYNAMICKÁ CENOTVORBA ---

class RatePlan(Base):
    """ Cenový plán (např. 'Standardní', 'Nevratný', 'Se snídaní') """
    __tablename__ = "rate_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))

class Rate(Base):
    """ Konkrétní cena pro typ pokoje na konkrétní den a v rámci plánu """
    __tablename__ = "rates"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    
    room_type = Column(String(100), nullable=False) # Cena se váže na typ pokoje, ne na konkrétní pokoj
    rate_plan_id = Column(Integer, ForeignKey("rate_plans.id"), nullable=False)
    
    rate_plan = relationship("RatePlan")

class Restriction(Base):
    """ Omezení (např. minimální délka pobytu) """
    __tablename__ = "restrictions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    
    min_stay = Column(Integer, nullable=True) # Minimum stay
    closed_to_arrival = Column(Boolean, default=False) # Nelze se ubytovat
    
    room_type = Column(String(100), nullable=False)
    rate_plan_id = Column(Integer, ForeignKey("rate_plans.id"), nullable=False)
    
    rate_plan = relationship("RatePlan")