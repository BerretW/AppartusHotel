from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from .. import crud, models, schemas
from ..database import get_db
from ..dependencies import get_current_active_user, is_admin_or_manager

router = APIRouter(prefix="/tasks", tags=["Úkoly"])

@router.post("/", response_model=schemas.Task, status_code=201, dependencies=[Depends(is_admin_or_manager)])
async def create_task_for_user(
    task: schemas.TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Vytvoří nový úkol pro zadaného uživatele (pouze pro manažery/adminy)."""
    assignee = await db.get(models.User, task.assignee_id)
    if not assignee:
        raise HTTPException(status_code=404, detail=f"Uživatel s ID {task.assignee_id} neexistuje.")
    return await crud.create_task(db=db, task=task)

@router.get("/my/", response_model=List[schemas.Task])
async def read_my_tasks(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Vrátí seznam úkolů přiřazených aktuálně přihlášenému uživateli v daném časovém rozmezí."""
    tasks = await crud.get_tasks_for_user(db, user_id=current_user.id, start_date=start_date, end_date=end_date)
    return tasks

@router.patch("/{task_id}/status", response_model=schemas.Task)
async def update_task_status(
    task_id: int,
    task_update: schemas.TaskUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Umožní uživateli změnit stav úkolu, který je na něj přiřazen."""
    db_task = await crud.get_task_by_id(db, task_id=task_id)
    
    # Ověření, že úkol existuje
    if not db_task:
        raise HTTPException(status_code=404, detail="Úkol nebyl nalezen.")
    
    # Ověření, že úkol patří přihlášenému uživateli (nebo je uživatel manažer)
    if db_task.assignee_id != current_user.id and current_user.role not in [models.UserRole.spravce, models.UserRole.majitel]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tento úkol nemůžete upravit.")
    
    db_task.status = task_update.status
    if task_update.notes:
        db_task.notes = task_update.notes
        
    await db.commit()
    await db.refresh(db_task)
    return db_task