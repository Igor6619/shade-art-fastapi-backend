import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
# Импортируем наши настройки и функцию получения сессии БД
from src.config import settings
from src.database import get_async_session
# Импортируем роутеры из наших независимых модулей
from src.modules.auth.router import router as auth_router
from src.modules.profile.router import router as profile_router
from src.modules.admin.router import router as admin_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Shade Art API",
    docs_url="/docs" if settings.DEBUG else None,
)

origins = [
    'http://localhost:3010',
    'http://127.0.0.1:3010',
    'https://shade-art.com'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Разрешаем запросы только с этих сайтов
    allow_credentials=True,           # Обязательно True, если будете передавать куки/токены
    allow_methods=["*"],              # Разрешаем любые методы (POST, GET, OPTIONS, PUT, DELETE)
    allow_headers=["*"],              # Разрешаем любые заголовки (Content-Type, Authorization и т.д.)
)
# Подключаем роутеры наших независимых модулей (псевдомодулей)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(admin_router)

@app.get("/")
async def root():
    """Тестовый эндпоинт, чтобы проверить, что сервер работает"""
    return {
        "status": "working",
        "message": "Welcome to Shade Art API",
        "debug_mode": settings.DEBUG
    }


if __name__ == "__main__":
    # Запускаем сервер uvicorn. 
    # Если DEBUG=True, сервер будет автоматически перезапускаться при изменении кода (reload=True)
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=settings.DEBUG
    )