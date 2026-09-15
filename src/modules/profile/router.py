from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Response, 
    Query,
    Path,
    Cookie
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, delete 
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database import get_async_session
from src.modules.profile.schemas import (
    ProfileUpdateSchema,
    ProfileResponseSchema
)
from src.modules.profile.models import (
    Profile,
)
from src.modules.auth.utils import (
    hash_password,
    verify_password,
    get_current_user
)
from uuid import UUID
from typing import Optional, Annotated
from datetime import datetime, timedelta 

# Инициализируем изолированный роутер модуля
router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

@router.get(
    "/{user_id}", 
    response_model=ProfileResponseSchema, 
    status_code=status.HTTP_200_OK
)
async def get_profile(
    user_id: Annotated[UUID, Path(description="ID пользователя")],
    db: AsyncSession = Depends(get_async_session)
):
    # 1. Получаем ВСЕХ пользователей с таким логином
    print('user_id: ', user_id)
    profile = await db.get(Profile, user_id) # Получаем профиль пользователя User
    print('profile: ', profile)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль для данного пользователя не найден"
        )
    print ('profile: ', profile)
    return profile

@router.patch("/{user_id}")
async def update_profile(
        user_id: Annotated[UUID, Path(description="ID пользователя")],
        profile_data: ProfileUpdateSchema,
        db: AsyncSession = Depends(get_async_session)
    ):
        """
        Эндпоинт для обновления данных профиля.
        Фронтенд вызовет его, когда пользователь заполнит форму редактирования.
        """
        # Ищем профиль по user_id
        query = select(Profile).where(Profile.user_id == user_id)
        result = await db.execute(query)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="Профиль не найден")

        # Превращаем пришедшие данные в словарь, исключая те, которые пользователь не заполнил (None)
        update_data = profile_data.model_dump(exclude_unset=True)

        # Обновляем поля профиля динамически
        for key, value in update_data.items():
            setattr(profile, key, value)

        await db.commit()
        await db.refresh(profile)

        return {"status": "success", "message": "Профиль успешно обновлен"}