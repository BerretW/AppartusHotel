from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import is_admin_or_manager, is_storekeeper

router = APIRouter(prefix="/inventory", tags=["Sklad"])

@router.post("/items/", response_model=schemas.InventoryItem, status_code=201, dependencies=[Depends(is_admin_or_manager)])
async def create_inventory_item(item: schemas.InventoryItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_inventory_item(db=db, item=item)

@router.post("/stock/add", dependencies=[Depends(is_storekeeper)])
async def add_stock(item: schemas.StockBase, db: AsyncSession = Depends(get_db)):
    # Jednoduché přidání na sklad, ideálně by bylo součástí Příjemky
    await crud.add_stock(db, item_id=item.item_id, location_id=1, quantity=item.quantity) # Příklad: lokace 1 = Centrální sklad
    return {"message": "Zásoba byla úspěšně navýšena."}

@router.post("/stock/transfer")
async def transfer_stock_between_locations(transfer_data: schemas.StockTransfer, db: AsyncSession = Depends(get_db)):
    await crud.transfer_stock(db, transfer_data)
    return {"message": "Přesun zásob byl úspěšně proveden."}

@router.get("/locations/{location_id}/stock", response_model=List[schemas.Stock])
async def get_stock_at_location(location_id: int, db: AsyncSession = Depends(get_db)):
    stock_list = await crud.get_stock_by_location(db, location_id=location_id)
    return stock_list