from fastapi import FastAPI
from contextlib import asynccontextmanager

# Importujeme všechny potřebné routery
from .routers import auth, users, tasks, rooms, inventory

# Importujeme klíčové objekty pro práci s databází
from .database import Base, engine

# Funkce, která se spustí při startu a ukončení aplikace
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kód zde se spustí PŘED startem aplikace
    print("Aplikace startuje, připravuji databázi...")
    async with engine.begin() as conn:
        # Vytvoří všechny tabulky definované v modelech, pokud neexistují
        await conn.run_sync(Base.metadata.create_all)
    print("Databáze je připravena.")
    
    yield # Zde běží samotná aplikace
    
    # Kód zde se spustí PO ukončení aplikace
    print("Aplikace se ukončuje.")


# Vytvoření instance aplikace s použitím naší lifespan funkce
app = FastAPI(
    title="Hotel Management API",
    description="Kompletní API pro správu hotelu.",
    version="1.2.0 (bez Alembic)",
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