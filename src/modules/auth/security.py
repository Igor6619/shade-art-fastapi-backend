import bcrypt

def hash_password(password: str) -> str:
    """Хеширует пароль пользователя."""
    # Переводим строку в байты
    password_bytes = password.encode('utf-8')
    # Генерируем соль
    salt = bcrypt.gensalt()
    # Хешируем
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Возвращаем строку для сохранения в БД
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с хешем из базы."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
