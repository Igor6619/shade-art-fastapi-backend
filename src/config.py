import os
from pydantic import Field
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = BASE_DIR.parent / ".env"


class SettingsDB(BaseModel):
    '''Настройки BD'''

    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    NAME: str

    @property
    def db_url_async(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


class Settings(BaseSettings):
    db:SettingsDB

    LIMIT_ON_PAGE: int = Field(
            default=20, 
            description="Количество элементов на странице по умолчанию"
    )

    DEBUG: bool = Field(
        default=False
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, 
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )
    
settings = Settings()