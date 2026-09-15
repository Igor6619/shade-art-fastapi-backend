from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict, model_validator
from datetime import datetime
from uuid import UUID


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




