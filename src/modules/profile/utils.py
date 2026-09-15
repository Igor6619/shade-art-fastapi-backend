import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from src.config import settings
from src.database import get_async_session
from src.modules.auth.models import (
    User, 
    UserSession
)
from fastapi import (
    Request, 
    Depends, 
    HTTPException, 
    status,
    Cookie
)
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.config import settings
from typing import Optional, Any


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

async def create_user_session(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    role: str, 
    first_name: str
) -> uuid.UUID:
    """
    Создает сессию в PostgreSQL.
    Возвращает session_id (UUID), который нужно записать в Cookie.
    """
    # Вычисляем время окончания сессии (timezone-naive для совпадения с DateTime)
    expires_at = datetime.now() + timedelta(days=settings.session.SESSION_MAX_AGE_DAYS)
    
    # Формируем payload, дублируя user_id в виде строки для удобства чтения во фронтенде
    payload = {
        "user_id": str(user_id),
        "role": role,
        "first_name": first_name
    }
    
    # Создаем объект сессии. session_id сгенерируется автоматически через default=uuid.uuid4
    db_session = UserSession(
        user_id=user_id,
        payload=payload,
        expires_at=expires_at
    )
    
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)  # Обновляем объект, чтобы получить сгенерированный session_id
    
    return db_session.session_id


async def get_session_payload(db: AsyncSession, session_id: uuid.UUID) -> Optional[dict[str, Any]]:
    """
    Проверяет существование и срок годности сессии.
    Возвращает dict с данными пользователя (payload) или None.
    """
    now = datetime.now()
    
    # Строим запрос: ищем сессию по ID, которая еще не просрочена
    query = select(UserSession).where(
        UserSession.session_id == session_id,
        UserSession.expires_at > now
    )
    
    result = await db.execute(query)
    session_record = result.scalar_one_or_none()
    
    if not session_record:
        return None
        
    return session_record.payload

async def get_current_user(
    # 1. FastAPI автоматически достает UUID сессии из куки "session"
    session_id: Annotated[str | None, Cookie(alias=settings.session.NAME_COOKIE)] = None,
    db: Annotated[AsyncSession, Depends(get_async_session)] = None
) -> User:
    """
    Основная зависимость: проверяет сессию в PostgreSQL по куке и возвращает объект User из БД.
    """
    # Если кука вообще отсутствует в запросе
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Вы не авторизованы (отсутствует кука сессии)",
        )
        
    try:
        # Конвертируем строковую куку в объект uuid.UUID
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный формат идентификатора сессии",
        )

    # 2. Ищем активную и непросроченную сессию в базе данных
    now = datetime.now()
    session_query = select(UserSession).where(
        UserSession.session_id == session_uuid,
        UserSession.expires_at > now
    )
    session_result = await db.execute(session_query)
    current_session = session_result.scalar_one_or_none()

    if not current_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла или не существует, войдите заново",
        )

    # 3. Ищем пользователя по user_id из сессии и сразу подтягиваем его профиль
    user_query = (
        select(User)
        .where(User.id == current_session.user_id)
        .options(joinedload(User.profile))
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

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