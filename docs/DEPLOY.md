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

## 3. Zaxiralash (Backup) Tartibi

**Ma'lumotlar bazasi:**
PostgreSQL ma'lumotlari `postgres_data` Docker volume'ida saqlanadi. Har kuni xavfsiz dump qilib borish zarur. Host mashinada crontab orqali avtomatlashtirish mumkin:
```bash
docker exec -t <container_name_db> pg_dumpall -c -U alora > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql
```
Olingan `.sql` dump fayllari zudlik bilan boshqa tashqi ob'yekt omboriga (masalan AWS S3) nusxalanishi (sync) shart.

**Media fayllar (Rasmlar, Hujjatlar):**
Media fayllar odatda S3'da saqlanishi kerak. Agar vaqtincha yoki maxsus holatlarda serverning o'zida saqlansa, loyihadagi tegishli media papkasining barcha tarkibini xuddi shu tarzda S3 bucket ga (misol uchun `aws s3 sync`) jo'natib turish rejalashtiriladi.
