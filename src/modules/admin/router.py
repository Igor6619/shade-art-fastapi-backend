from typing import Annotated
from fastapi import APIRouter, Depends
from src.modules.auth.utils import(
    RoleChecker,
    get_current_user
) 
from models import User 


# Инициализируем роутер админки
# Передаем в dependencies наш RoleChecker. Теперь ВСЕ эндпоинты в этом файле
# будут автоматически требовать роль 'admin' на входе!
router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(RoleChecker(["admin"]))] 
)

@router.get("/")
async def get_admin_main(
    # Если вам внутри функции нужны данные самого админа (например, для логов),
    # вы можете дополнительно вызвать get_current_user. 
    # Благодаря кэшированию FastAPI, повторного запроса в БД не произойдет!
    current_admin: Annotated[User, Depends(get_current_user)]
):
    """
    Главная панель администратора.
    Доступна ТОЛЬКО пользователям с ролью 'admin'.
    """
    return {
        "status": "success",
        "message": f"Привет, Администратор {current_admin.login}! Доступ к панели разрешен.",
        "stats": {
            "total_users": 154,
            "active_sessions": 12,
            "server_status": "healthy"
        }
    }

@router.get("/users-list")
async def get_all_users():
    """
    Секретный роут для управления пользователями.
    Он тоже автоматически защищен, так как привязан к этому роутеру.
    """
    return {
        "message": "Здесь будет список всех пользователей для модерации."
    }