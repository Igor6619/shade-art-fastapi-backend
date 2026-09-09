from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

# 1. Создаем асинхронный движок для работы с БД
# echo=settings.DEBUG выводит все SQL-запросы в консоль, когда в .env включен DEBUG=True
engine = create_async_engine(
    settings.db.db_url_async,
    echo=settings.DEBUG,
)

# 2. Создаем фабрику для генерации асинхронных сессий
async_session_maker = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False,
    class_=AsyncSession
)

# 3. Базовый класс для всех будущих моделей таблиц (User, Product и т.д.)
class Base(DeclarativeBase):
    pass

# 4. Функция-зависимость (Dependency Injection) для роутеров FastAPI.
# Она автоматически открывает сессию перед запросом и закрывает её после ответа.
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
