
# чтобы Python (и затем Alembic) прочитал их при инициализации
from src.modules.auth.models import User
from src.modules.profile.models import Profile


# Экспортируем Base и модели, чтобы их было удобно импортировать в env.py
__all__ = ["User", "Profile"]