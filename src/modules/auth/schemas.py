from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID
from src.modules.auth.models import UserRole

class ProfileResponseSchema(BaseModel):
    """Схема для отображения данных профиля (вкладывается внутрь пользователя)"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True  # Позволяет читать данные из модели Profile


class ProfileUpdateSchema(BaseModel):
    """Схема для получения новых данных профиля от фронтенда"""
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = Field(default=None)


class UserResponseSchema(BaseModel):
    """Схема для безопасного ответа клиенту после регистрации или авторизации"""

    id: UUID
    login: str
    
    is_active: bool
    created_at: datetime
    role: UserRole
    # Вкладываем схему профиля. При регистрации здесь вернутся null-поля и дата создания
    profile: ProfileResponseSchema

    class Config:
        from_attributes = True  # Позволяет автоматически мапить объекты SQLAlchemy (User) в Pydantic


class UserCreateSchema(BaseModel):
    '''Схема создания пользователя'''

    login: str = Field(
            ...,
            min_length=3,           # Минимальная длина логина
            max_length=100,          # Максимальная длина (заменяет String(100))
            description="Уникальный логин пользователя без пробелов"
        )

    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Пароль пользователя (минимум 6 символов)"
    )
       
    @field_validator("login")
    @classmethod
    def validate_login_spaces(cls, value: str) -> str:
        """Проверяет, чтобы в логине не было пробелов ни в каком месте"""

        cleaned_value = value.strip()
        if " " in cleaned_value:
            raise ValueError("Логин не должен содержать пробелы")
        return value


class UserLoginSchema(BaseModel):
    """Схема для входа пользователя"""

    login: str
    password: str

class UserLoginResponseSchema(BaseModel):
    '''Схема ответа на попытку входа'''

    status:bool = Field(
        description="Статус входа на сайт"
    )
    redirect_to_url:str = Field(
        description="Перенаправляем"
    )

from pydantic import BaseModel, Field

class UserLogoutResponseSchema(BaseModel):
    """Схема ответа на попытку выхода из системы"""
    status: bool = Field(
        ..., 
        description="Флаг успешности выхода. True — кука успешно удалена."
    )
    redirect_to_url: str = Field(
        ..., 
        description="URL, на который фронтенд должен перенаправить пользователя после выхода."
    )
