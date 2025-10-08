from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models, schemas
from .database import get_db
from .config import settings
from .models import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_roles: list[UserRole]):
    """Závislost, která ověří, zda má uživatel jednu z požadovaných rolí."""
    async def role_checker(current_user: models.User = Depends(get_current_active_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nemáte dostatečná oprávnění pro tuto operaci."
            )
        return current_user
    return role_checker

# Konkrétní závislosti pro snadnější použití
is_owner = require_role([UserRole.majitel])
is_admin_or_manager = require_role([UserRole.majitel, UserRole.spravce])
is_storekeeper_or_manager = require_role([UserRole.skladnik, UserRole.spravce, UserRole.majitel])
is_housekeeper_or_manager = require_role([UserRole.uklizecka, UserRole.spravce, UserRole.majitel])
can_change_room_status = require_role([UserRole.uklizecka, UserRole.recepcni, UserRole.spravce, UserRole.majitel])