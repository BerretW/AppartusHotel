from fastapi import FastAPI
from contextlib import asynccontextmanager

# Importujeme všechny potřebné routery
from .routers import auth, users, tasks, rooms, inventory
from .database import get_db
from . import crud

# Funkce, která se spustí při startu a ukončení aplikace
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kód zde se spustí PŘED startem aplikace
    print("Aplikace startuje...")
    # Zajistíme existenci Centrálního skladu při startu
    async for db in get_db():
        await crud.get_or_create_central_storage(db)
        print("Ověřena existence Centrálního skladu.")
    
    yield # Zde běží samotná aplikace
    
    # Kód zde se spustí PO ukončení aplikace
    print("Aplikace se ukončuje.")


# Vytvoření instance aplikace s použitím naší lifespan funkce
app = FastAPI(
    title="Hotel Management API",
    description="Kompletní API pro správu hotelu.",
    version="2.0.0 (s Alembic a plnou funkcionalitou)",
    lifespan=lifespan
)

# Propojení jednotlivých routerů
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(rooms.router)
app.include_router(inventory.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Vítejte v Hotel Management API"}