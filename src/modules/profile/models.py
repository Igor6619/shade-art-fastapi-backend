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
from src.database import Base 
from enum import Enum as PythonEnum
from typing import TYPE_CHECKING

# Этот импорт увидят только IDE и mypy, но Python проигнорирует его при запуске
if TYPE_CHECKING:
    from src.modules.auth.models import User  # Ваша исходная строка импорта



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

