import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Uuid, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base  # Импорт общего базового класса из src/database.py

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )
    login: Mapped[str] = mapped_column(
            String(100), 
            nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(150), 
        unique=True, 
        nullable=False, 
        index=True
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        index=True
    )


class Profile(Base):
    __tablename__ = "profiles"

    # Первичным ключом профиля делаем ID пользователя (foreign key) — это идеальная практика для 1-к-1
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    # Личные данные пользователя (все поля делаем Optional, так как при регистрации они обычно пустые)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Text для длинного описания "о себе"
    
    # Системное поле: когда профиль обновлялся в последний раз
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now()  # SQLAlchemy сама обновит время при любом изменении профиля
    )

    # Обратная связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="profile")