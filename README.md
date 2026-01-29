# pentolymp-backend

## Перед запуском
1. Установите зависимости коммандой:
``` sh
pip3 install -r requirements.txt
```
2. Создайте `.env` и положите `SECRET_KEY` - рандомный набор символов.
3. Создайте БД командой:
``` sh
python3 manage.py migrate
```
4. Можете создать админа командой:
``` sh
python3 manage.py createsuperuser
```
5. Запустите сервер:
``` sh
python3 manage.py runserver 0.0.0.0:8000
```

Swagger доступен по пути: `/swagger`