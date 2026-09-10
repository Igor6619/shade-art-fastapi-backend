from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Response, 
    Query
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import select 
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database import get_async_session
from src.modules.auth.schemas import (
    ProfileUpdateSchema,
    UserResponseSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserLoginResponseSchema,
    UserLogoutResponseSchema
)
from src.modules.auth.models import (
    User, 
    Profile
)
from src.modules.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
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
            raise HTTPException(status_code=400, detail="Неудачная попытка")
            
    
    if user_data.login:
        query_login = select(User).where(User.login == user_data.login)
        result_login = await db.execute(query_login)
        if result_login.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Этот login уже занят")

    hashed_password = hash_password(user_data.password)

    # 4. СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ И СРАЗУ ПРИВЯЗЫВАЕМ ПРОФИЛЬ
    new_user = User(
        login=user_data.login,
        # email=user_data.email,
        hashed_password=hashed_password,
        # Магия: передаем пустой объект Profile(). 
        # SQLAlchemy сама поймет, какой у юзера ID, подставит его в профиль 
        # и сохранит ОБЕ записи за один транзакционный коммит!
        profile=Profile() 
    )
    
    db.add(new_user)
    await db.commit()      # Сохраняет и в users, и в profiles
    await db.refresh(new_user)

    # ДИНАМИЧЕСКИЙ ПЕРЕЗАПРОС: 
    # Вытаскиваем только что созданного пользователя из БД сразу вместе с его профилем
    query_result = await db.execute(
        select(User)
        .where(User.id == new_user.id)
        .options(joinedload(User.profile))  # Принудительно объединяем таблицы за 1 запрос
    )
    
    # Получаем чистый объект пользователя со всеми подгруженными связями
    user_with_profile = query_result.scalar_one()

    return user_with_profile

@router.post(
        "/login",
        response_model=UserLoginResponseSchema,
)
async def login_user(
    login_data: UserLoginSchema,
    response: Response,  # <--- Критически важно для работы с куками!
    next_url: str | None = Query(None, alias="next"),
    db: AsyncSession = Depends(get_async_session)
):
    # 1. Ищем пользователя по логину и СРАЗУ подгружаем профиль через joinedload
    query = (
        select(User)
        .where(User.login == login_data.login)
        .options(joinedload(User.profile))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Если пользователь не найден или пароль неверный — выдаем общую ошибку
    # (Из соображений безопасности не говорим конкретно "неверный пароль" или "нет юзера")
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    # 3. Генерируем токен (он автоматически заберет user.role и user.profile.first_name)
    token = create_access_token(user)

    # 4. Записываем токен в защищенную HttpOnly куку
    response.set_cookie(
        key="access_token",                     # Название куки
        value=token,                            # Сам JWT-токен
        httponly=True,                          # Запрещает JavaScript читать куку (защита от XSS)
        # secure=True,                            # Передача только по HTTPS (для локалки FastAPI делает поблажку)
        samesite="lax",                         # Защита от CSRF-атак
        max_age=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES * 60, # Время жизни куки в секундах
    )
    redirect_to = next_url if next_url else "/"
    logining_status = True
    return {
        "status": logining_status,
        "redirect_to_url": redirect_to
    }
    

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

@router.post(
    "/logout",
    response_model=UserLogoutResponseSchema,
    dependencies=[Depends(get_current_user)] 
)
async def logout_user(
    response: Response,
):
    """
    Выход из системы.
    Удаляет HttpOnly куку access_token и возвращает URL для редиректа.
    """
    # 1. Удаляем куку из браузера пользователя
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
        # secure=True  # Раскомментируйте на продакшене, если при логине использовали secure=True
    )
    
    # 2. Формируем ответ для фронтенда Next.js
    return {
        "status": True,
        "redirect_to_url": "/auth/login"  # После логаута отправляем пользователя на страницу входа
    }

