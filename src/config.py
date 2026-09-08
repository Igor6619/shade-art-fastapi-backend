from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Определяем путь к корневой директории проекта, чтобы Pydantic точно нашел файл .env
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Главный класс настроек приложения."""
    # Автоматически ищет .env в корне проекта
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    # Общие настройки
    APP_TITLE: str = "FastAPI App"
    DEBUG: bool = False

    # Параметры БД (замаппятся из префиксов DB_...)
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # Секреты
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        """Вычисляемое свойство для получения готовой строки подключения."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# Создаем синглтон настроек для импорта в другие модули приложения
settings = Settings()
