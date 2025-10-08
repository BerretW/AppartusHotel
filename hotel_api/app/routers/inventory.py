# FILE: hotel_api/app/routers/inventory.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager, is_storekeeper_or_manager, get_current_active_user

router = APIRouter(prefix="/inventory", tags=["Sklad"])

@router.post("/items/", response_model=schemas.InventoryItem, status_code=201, dependencies=[Depends(is_admin_or_manager)])
async def create_inventory_item(item: schemas.InventoryItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_inventory_item(db=db, item=item)

# --- NOVÝ ENDPOINT ---
@router.get("/items/", response_model=List[schemas.InventoryItem], dependencies=[Depends(get_current_active_user)])
async def get_all_inventory_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Vrátí seznam všech "master" skladových položek.
    Vyžaduje přihlášení.
    """
    items = await crud.get_inventory_items(db, skip=skip, limit=limit)
    return items

@router.get("/locations/", response_model=List[schemas.Location])
async def get_all_locations(db: AsyncSession = Depends(get_db)):
    return await crud.get_locations(db)



@router.post("/receipts/", response_model=schemas.ReceiptDocument, status_code=201, dependencies=[Depends(is_storekeeper_or_manager)])
async def create_receipt(receipt: schemas.ReceiptDocumentCreate, db: AsyncSession = Depends(get_db)):
    """Vytvoří příjemku a automaticky naskladní položky do centrálního skladu."""
    return await crud.create_receipt(db=db, receipt_data=receipt)

@router.post("/stock/transfer", dependencies=[Depends(is_storekeeper_or_manager)])
async def transfer_stock_between_locations(transfer_data: schemas.StockTransfer, db: AsyncSession = Depends(get_db)):
    """Přesune zadané množství položky z jedné lokace do druhé."""
    if transfer_data.source_location_id == transfer_data.destination_location_id:
        raise HTTPException(status_code=400, detail="Zdrojová a cílová lokace nemohou být stejné.")
    await crud.transfer_stock(db, transfer_data)
    return {"message": "Přesun zásob byl úspěšně proveden."}

@router.get("/locations/{location_id}/stock", response_model=List[schemas.Stock])
async def get_stock_at_location(location_id: int, db: AsyncSession = Depends(get_db)):
    """Získá aktuální stav zásob pro danou lokaci."""
    stock_list = await crud.get_stock_by_location(db, location_id=location_id)
    return stock_list