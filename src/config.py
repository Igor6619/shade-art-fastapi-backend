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

# class SettingsJWT(BaseModel):
#     SECRET_KEY: str
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

class SettingsSESSION(BaseModel):
    '''Настройки сессии'''

    SESSION_MAX_AGE_DAYS: int
    NAME_COOKIE: str
    
class Settings(BaseSettings):
    db: SettingsDB
    session: SettingsSESSION
    LIMIT_ON_PAGE: int = Field(
            default=20, 
            description="Количество элементов на странице по умолчанию"
    )
    DEBUG: bool = Field(
        default=False
    )
    PORT: int = Field(
        default=8000
    )


    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, 
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )
    
settings = Settings()