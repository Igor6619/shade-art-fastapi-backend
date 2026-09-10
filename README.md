Запуск проекта из корневой папки (`shade-art-fastapi-backend`):
```
python -m src.main
```

на фронте надо создать объект-константу
```
export const UserRole = Object.freeze({
  USER: 'user',
  ADMIN: 'admin',
  MODERATOR: 'moderator'
});
```

и в компонентах импортировать
```
import { UserRole } from '@/constants/auth';
```