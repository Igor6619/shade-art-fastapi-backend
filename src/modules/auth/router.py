from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database import get_async_session


# Инициализируем изолированный роутер модуля
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- ВРЕМЕННЫЕ PYDANTIC СХЕМЫ (позже вынесем их в schemas.py) ---
class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str



@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterSchema,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Эндпоинт регистрации нового пользователя.
    Принимает email и пароль, проверяет дубликаты и сохраняет в БД.
    """
   
    
    return {
        "status": "success",
        "message": f"Пользователь {user_data.email} успешно зарегистрирован",
        "details": "Временный ответ. Подключите модель User для записи в БД."
    }