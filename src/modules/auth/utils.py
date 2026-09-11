import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from src.config import settings
from src.database import get_async_session
from src.modules.auth.models import User
from fastapi import Request, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload


def hash_password(password: str) -> str:
    """Хеширует пароль пользователя."""
    # Переводим строку в байты
    password_bytes = password.encode('utf-8')
    # Генерируем соль
    salt = bcrypt.gensalt()
    # Хешируем
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Возвращаем строку для сохранения в БД
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с хешем из базы."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def create_access_token(user: User) -> str:
    """
    Генерирует JWT access-токен для пользователя.
    В Payload зашиваем ID, логин, роль и имя из профиля.
    """
    # Безопасно получаем first_name, проверяя, подгружена ли связь 'profile'
    # и не является ли поле пустым
    first_name = None
    if "profile" in user.__dict__ and user.profile:
        first_name = user.profile.first_name if user.profile.first_name else user.login

    # 1. Готовим Payload (данные внутри токена)
    payload = {
        "user_id": str(user.id),       # ID пользователя
        "role": user.role,         # Роль (user/admin)
        "first_name": first_name   # <--- НАШЕ НОВОЕ ПОЛЕ
    }
    
    # 2. Рассчитываем время жизни токена
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expire})
    
    # 3. Подписываем Payload секретным ключом
    encoded_jwt = jwt.encode(
        payload, 
        settings.jwt.SECRET_KEY, 
        algorithm=settings.jwt.ALGORITHM
    )
    
    return encoded_jwt

def get_token_from_cookie(request: Request) -> str:
    """
    Достает токен из HttpOnly куки.
    Если куки нет — прерывает запрос с ошибкой 401.
    """

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Вы не авторизованы (отсутствует токен)",
        )
    return token

async def get_current_user(
    token: Annotated[str, Depends(get_token_from_cookie)],
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> User:
    """
    Основная зависимость: проверяет подпись JWT и возвращает объект User из БД.
    """
    try:
        # 1. Декодируем токен. PyJWT автоматически проверит время "exp"!
        payload = jwt.decode(
            token,
            settings.jwt.SECRET_KEY,
            algorithms=[settings.jwt.ALGORITHM]
        )
        
        # 2. Достаем ID пользователя из стандартного поля "sub"
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен (отсутствует user_id)",
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла, войдите заново",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или поврежденный токен",
        )

    # 3. Ищем пользователя в базе данных и сразу подтягиваем его профиль
    query = select(User).where(User.id == user_id).options(joinedload(User.profile))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден в системе",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт деактивирован",
        )

    return user

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        # Запоминаем, какие роли разрешены для конкретного роута
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]):
        # Эта логика выполняется при каждом HTTP-запросе
        if current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        return current_user