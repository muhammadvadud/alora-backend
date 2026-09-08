# Alora Backend

Alora loyihasining backend qismi. Django 5 va PostgreSQL orqali ishlaydi.

## Texnologiyalar
- Python 3.13
- Django 5.x
- Django REST Framework
- PostgreSQL 16
- Redis
- Celery
- Uvicorn (ASGI)

## O'rnatish

1. `.env.example` faylidan `.env` nusxasini yarating:
   ```bash
   cp .env.example .env
   ```

2. Docker orqali ishga tushiring:
   ```bash
   docker-compose up -d --build
   ```

## Ishga tushirish (Lokal)
```bash
pip install -r requirements.txt # Yoki pip install . yoki shunga o'xshash, pyproject.toml mavjud
python manage.py migrate
python manage.py runserver
```
