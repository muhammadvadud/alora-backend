# Alora Backend

Alora loyihasining backend qismi. Django 5 va PostgreSQL orqali ishlaydi. Ushbu loyiha mobil ilova va xizmatlar uchun mo'ljallangan.

## Texnologiyalar
- **Asosiy Til**: Python 3.13
- **Freywork**: Django 5.x, Django REST Framework
- **Ma'lumotlar bazasi**: PostgreSQL 16
- **Kesh va Pub/Sub**: Redis 7
- **Asinxron vazifalar**: Celery
- **Server**: Uvicorn (ASGI) va gRPC
- **Bog'liqliklar boshqaruvi**: `pyproject.toml` (va `requirements.txt`)

## O'rnatish (Docker orqali)

Loyiha to'liq Docker orqali ishlaydi (`docker-compose.yml`). Xizmatlarga `db`, `redis`, `django`, `celery_worker`, `celery_beat`, va `nginx` kiradi.

1. `.env.example` faylidan `.env` faylini nusxalab yarating:
   ```bash
   cp .env.example .env
   ```

2. `.env` dagi muhit o'zgaruvchilarini sozlang (pastda batafsil).

3. Docker-compose orqali ishga tushiring:
   ```bash
   docker-compose up -d --build
   ```
*Eslatma*: Konteynerlar ishga tushganda `scripts/entrypoint.sh` orqali migratsiyalar (`python manage.py migrate`) va statik fayllar (`collectstatic`) avtomatik ravishda bajariladi.

## Ishga tushirish (Lokal ishlab chiqish uchun)

Python 3.13 virtual muhitini yarating:
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Bog'liqliklarni o'rnating:
```bash
pip install -r requirements-dev.txt
```
*(Paketlar faqat `pyproject.toml` dan `scripts/gen_requirements.py` orqali generatsiya qilinadi).*

Baza migratsiyalarini qiling va serverni yoqing:
```bash
python manage.py migrate
python manage.py runserver
# Yoki Uvicorn bilan:
uvicorn config.asgi:application --reload
```

## Muhit O'zgaruvchilari (Environment Variables)

Muhim o'zgaruvchilar quyidagilar (`.env` faylida ko'rsatiladi):
- `DJANGO_SETTINGS_MODULE`: Sozlamalar moduli (masalan, `config.settings.dev` yoki `prod`).
- `SECRET_KEY`: Django maxfiy kaliti (prod da o'zgartiring!).
- `DEBUG`: Dastur ishlash rejimi (`True` yoki `False`).
- `ALLOWED_HOSTS`: Ruxsat etilgan domenlar ro'yxati (vergul bilan ajratilgan: `localhost,127.0.0.1`).
- `CORS_ALLOWED_ORIGINS`: CORS ruxsat etilgan origin'lar (masalan, `http://localhost:3000`).
- `DATABASE_URL`: Postgres ulanish URL'i (masalan, `postgres://alora:alora_password@localhost:5432/alora`).
- `REDIS_URL`: Redis ulanish URL'i (masalan, `redis://localhost:6379/0`).
- `SENTRY_DSN`: Sentry xatoliklarni kuzatish tizimiga ulanish uchun DSN (majburiy emas).

## Hujjatlar
Loyihadagi qo'shimcha hujjatlar bilan `docs/` papkasida tanishishingiz mumkin:
- `API-GUIDE.md`: API yo'llari va frontend/mobil jamoalar uchun qo'llanma.
- `GO-CONTRACT.md`: Go jamoasi bilan gRPC kelishuvlari.
- `DEPLOY.md`: Loyihani deploy qilish va backup olish tartibi.
