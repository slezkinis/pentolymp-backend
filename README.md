# pentolymp-backend

## Перед запуском
1. Установите зависимости
2. Создайте `.env` и положите `SECRET_KEY` - рандомный набор символов.
3. Создайте БД командой:
``` sh
python3 manage.py migrate
```
4. Запустите сервер:
``` sh
python3 manage.py runserver
```

Swagger доступен по пути: `/swagger`