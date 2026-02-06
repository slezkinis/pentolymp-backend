# pentolymp-backend

## Перед запуском
1. Создайте `.env` по примеру:
```
SECRET_KEY="12313123" - набор символов
DEBUG=True - В Debug ли бекенд. Пока ставим True
ALLOWED_HOSTS=localhost,127.0.0.1 - хосты, с которых обращаемся к бекенду. Пока эти
CORS_ALLOW_ALL_ORIGINS=True
```

## Запуск
1. Запустите бекенд в фоне.
``` sh
docker compose up --build -d
```
2. Можете создать админа командой:
``` sh
docker compose exec backend /bin/bash -c "python3 manage.py createsuperuser"
```
3. Бекенд запущен на `http://127.0.0.1:8000`. Админка: `/admin`, Swagger: `/swagger`.

4. Чтобы остановить сервер:
``` sh
docker compose down
```
