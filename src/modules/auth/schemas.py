from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict, model_validator
from datetime import datetime
from uuid import UUID
from src.modules.auth.models import UserRole
from src.modules.profile.schemas import ProfileResponseSchema


class UserResponseSchema(BaseModel):
    """Схема для безопасного ответа клиенту после регистрации или авторизации"""

    id: UUID
    login: str
    
    is_active: bool
    created_at: datetime
    role: UserRole
    # Вкладываем схему профиля. При регистрации здесь вернутся null-поля и дата создания
    profile: ProfileResponseSchema

    model_config = ConfigDict(from_attributes=True)  # Позволяет автоматически мапить объекты SQLAlchemy (User) в Pydantic


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
        min_length=5,
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


    user: UserResponseSchema 
    status:bool = Field(
        description="Статус входа на сайт"
    )
    redirect_to_url:str = Field(
        description="Перенаправляем"
    )

    model_config = ConfigDict(from_attributes=True)


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

class GetMeResponseSchema(BaseModel):
    '''Схема пользователя из сессии которая хранится на сервере'''

    user_id: str
    role: str = "user"
    first_name: str = "Пользователь"

    @model_validator(mode="before")
    @classmethod
    def extract_from_jsonb_payload(cls, data: Any) -> Any:
        if hasattr(data, "payload"):
            payload = data.payload or {}
        raw_first_name = payload.get("first_name")
        first_name_value = raw_first_name if raw_first_name is not None else "Пользователь"
        return {
            # Приводим к строке, так как в Next.js String(user.user_id)
            "user_id": str(payload.get("user_id", "")), 
            "role": payload.get("role", "user"),
            "first_name": first_name_value,
        }