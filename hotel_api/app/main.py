from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Importujeme všechny potřebné routery
# Přidány nové: 'pricing', 'booking'
from .routers import auth, users, tasks, rooms, inventory, reservations, dashboard, pricing, booking
from .database import get_db
from . import crud

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kód zde se spustí PŘED startem aplikace
    print("Aplikace startuje...")
    # Zajistíme existenci Centrálního skladu při startu
    async for db in get_db():
        await crud.get_or_create_central_storage(db)
        print("Ověřena existence Centrálního skladu.")

    yield  # Zde běží samotná aplikace

    # Kód zde se spustí PO ukončení aplikace
    print("Aplikace se ukončuje.")

# Vytvoření instance aplikace
app = FastAPI(
    title="Hotel Management API",
    description="Kompletní API pro správu hotelu.",
    version="3.0.0 (s dynamickou cenotvorbou a booking engine)",
    lifespan=lifespan
)

# CORS Middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Propojení jednotlivých routerů
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(rooms.router)
app.include_router(inventory.router)
app.include_router(reservations.router)
app.include_router(dashboard.router)
app.include_router(pricing.router) # NOVÝ ROUTER
app.include_router(booking.router) # NOVÝ ROUTER

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Vítejte v Hotel Management API v3.0"}