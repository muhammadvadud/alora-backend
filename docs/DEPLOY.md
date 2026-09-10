# Alora Backend - Deploy va Backup Qo'llanmasi

## 1. Loyihani Deploy Qilish (Docker orqali)

Loyiha to'liq konteynerlashtirilgan. Barcha xizmatlar (PostgreSQL, Redis, Django, Celery va Nginx) `docker-compose.yml` orqali ishga tushiriladi. GitHub Actions yoki shunga o'xshash CI platformalaridan foydalanib deploy qilinadi (qarang: `.github/workflows/ci.yml`).

**Ishga tushirish ketma-ketligi:**
1. Loyihani serverga klon qiling:
   ```bash
   git clone <repo_url>
   cd alora-backend
   ```
2. Muhit o'zgaruvchilari faylini yarating va tahrirlang:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Yodda tuting: Prod muhiti uchun `DJANGO_SETTINGS_MODULE=config.settings.prod` qilib o'rnatilishi va kerakli parollar, SENTRY_DSN kiritilishi shart.*

3. Docker xizmatlarini orqa fonda ishga tushiring:
   ```bash
   docker-compose up -d --build
   ```

**Entrypoint jarayoni:**
`scripts/entrypoint.sh` bash skripti orqali konteyner ishga tushgan zahoti avtomatik qilinadigan amallar:
- `python manage.py migrate --noinput` (Baza migratsiyalari ishga tushadi)
- `python manage.py collectstatic --noinput` (Statik fayllar Nginx uchun yig'iladi)
- So'ngra buyruqdagi kabi server ishga tushadi (`exec "$@"`). Asosiy app uchun bu `uvicorn config.asgi:application` bo'ladi.

## 2. Docker Xizmatlari

`docker-compose.yml` quyidagi xizmatlarni o'z ichiga oladi:
- `db`: PostgreSQL 16 (Ma'lumotlar bazasi, port: 5432, volume: `postgres_data`)
- `redis`: Redis 7 Alpine (Celery broker, cache va pub/sub, port: 6379)
- `django`: Django ASGI server (Uvicorn). App `docker/Dockerfile` asosida quriladi va 8000-portda ishlaydi.
- `celery_worker`: Asinxron og'ir yukli task'larni (usage saqlash, rasm kesish va boshqalar) bajaruvchi worker.
- `celery_beat`: Vaqti-vaqti bilan avtomatik bajariladigan task'lar rejalashtiruvchisi.
- `nginx`: Reverse proxy va statik fayllarni tarqatuvchi xizmat (port: 80, o'z `docker/nginx.conf` fayli bilan). U tashqariga xizmat ko'rsatadi.

### 2.1. `go-agent` holati

`go-agent` servisi hozircha `docker-compose.yml`ga qo'shilmagan: Go tomoni alohida repozitoriyda va hali tayyor emas. Tayyor bo'lgach compose'ga qo'shiladi. Backend `go-agent`ni ixtiyoriy bog'liqlik sifatida ko'radi — `/health/` da gRPC yiqilsa tizim `degraded` (200) qaytaradi, `error` emas.

## 3. Zaxiralash (Backup) va Tiklash (Restore) Tartibi

**Ma'lumotlar bazasi zaxirasi (Backup):**
`scripts/backup_db.sh` skripti orqali PostgreSQL ma'lumotlar bazasining zaxira nusxasi olinadi. 
Bu skriptni crontab orqali avtomatlashtirish kerak.
U S3 bucket'ga nusxalashni ham qo'llab-quvvatlaydi (`BACKUP_S3_BUCKET` o'zgaruvchisi orqali).

**Tiklash (Restore):**
Olingan zaxira nusxadan tiklash uchun quyidagi buyruqdan foydalaning:
```bash
pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" alora-YYYYMMDD-HHMMSS.dump
```

Sinalmagan backup — backup emas. Tiklashni kamida bir marta sinab ko'ring.

**Media fayllar:**
Media fayllar odatda S3'da saqlanadi. Agar lokal saqlansa, media papkasini ham alohida S3'ga sinxronlash (masalan, `aws s3 sync` orqali) kerak.
