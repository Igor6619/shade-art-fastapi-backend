
# чтобы Python (и затем Alembic) прочитал их при инициализации
from src.database import Base 
from src.modules.auth.models import User, Profile


# Экспортируем Base и модели, чтобы их было удобно импортировать в env.py
__all__ = ["Base", "User", "Profile"]