import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import (
    String,
    Enum, 
    Boolean, 
    UUID, 
    func,
    DateTime, 
    ForeignKey, 
    Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base  # Импорт общего базового класса из src/database.py
from enum import Enum as PythonEnum


class UserRole(str, PythonEnum):
    """Статические роли пользователей"""

    GUEST = "guest" 
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
    )
    login: Mapped[str] = mapped_column(
            String(100), 
            nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_type=True),
        default=UserRole.USER,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        index=True
    )
    profile: Mapped["Profile"] = relationship(
        "Profile", 
        back_populates="user", 
        cascade="all, delete-orphan"  # При удалении юзера удалится и его профиль
    )

    __table_args__ = (
        UniqueConstraint("login", "hashed_password", name="uq_user_login_password"),
    )


class Profile(Base):
    __tablename__ = "profiles"

    # Первичным ключом профиля делаем ID пользователя (foreign key) — это идеальная практика для 1-к-1
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    user: Mapped["User"] = relationship("User", back_populates="profile")
    # Личные данные пользователя (все поля делаем Optional, так как при регистрации они обычно пустые)
    first_name: Mapped[Optional[str]] = mapped_column(
            String(50), 
            nullable=True
    )
    last_name: Mapped[Optional[str]] = mapped_column(
            String(50), 
            nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
            String(150), 
            index=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
            String(255), 
            nullable=True
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )  # Text для длинного описания "о себе"
    
    # Системное поле: когда профиль обновлялся в последний раз
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now()  # SQLAlchemy сама обновит время при любом изменении профиля
    )

class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # ИСПРАВЛЕНО: Mapped[uuid.UUID] теперь соответствует типу UUID в БД
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        index=True, 
        nullable=False
    )
    
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False
    )