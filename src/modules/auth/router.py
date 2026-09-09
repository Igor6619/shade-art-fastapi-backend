from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database import get_async_session
from src.modules.auth.schemas import (
    ProfileUpdateSchema,
    UserResponseSchema,
    UserCreateSchema
)
from src.modules.auth.models import (
    User, 
    Profile
)
from src.modules.auth.security import (
    hash_password,
    verify_password
)
from uuid import UUID

# Инициализируем изолированный роутер модуля
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post(
    "/register", 
    response_model=UserResponseSchema, 
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreateSchema,
    db: AsyncSession = Depends(get_async_session)
):
    # 1. Получаем ВСЕХ пользователей с таким логином
    query = select(User).where(User.login == user_data.login)
    result = await db.execute(query)
    users = result.scalars().all()  # Получаем список объектов User
    # 2. Бежим по списку и проверяем пароль каждого
    for user in users:
        if verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Измени пароль")
            
    hashed_password = hash_password()
    if user_data.email:
        query_email = select(User).where(User.email == user_data.email)
        result_email = await db.execute(query_email)
        if result_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Этот email уже занят")
    hashed_password = hash_password(user_data.password)

    # 4. СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ И СРАЗУ ПРИВЯЗЫВАЕМ ПРОФИЛЬ
    new_user = User(
        login=user_data.login,
        email=user_data.email,
        hashed_password=hashed_password,
        # Магия: передаем пустой объект Profile(). 
        # SQLAlchemy сама поймет, какой у юзера ID, подставит его в профиль 
        # и сохранит ОБЕ записи за один транзакционный коммит!
        profile=Profile() 
    )
    
    db.add(new_user)
    await db.commit()      # Сохраняет и в users, и в profiles
    await db.refresh(new_user)

    return new_user

@router.patch("/profile/{user_id}")
async def update_profile(
        user_id: UUID,
        profile_data: ProfileUpdateSchema,
        session: AsyncSession = Depends(get_async_session)
    ):
        """
        Эндпоинт для обновления данных профиля.
        Фронтенд вызовет его, когда пользователь заполнит форму редактирования.
        """
        # Ищем профиль по user_id
        query = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="Профиль не найден")

        # Превращаем пришедшие данные в словарь, исключая те, которые пользователь не заполнил (None)
        update_data = profile_data.model_dump(exclude_unset=True)

        # Обновляем поля профиля динамически
        for key, value in update_data.items():
            setattr(profile, key, value)

        await session.commit()
        await session.refresh(profile)

        return {"status": "success", "message": "Профиль успешно обновлен"}