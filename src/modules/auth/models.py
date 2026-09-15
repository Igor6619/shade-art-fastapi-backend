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
from typing import TYPE_CHECKING

# Этот импорт увидят только IDE и mypy, но Python проигнорирует его при запуске
if TYPE_CHECKING:
    from src.modules.profile.models import Profile  # Ваша исходная строка импорта

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