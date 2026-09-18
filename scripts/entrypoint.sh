#!/bin/bash
set -euo pipefail

db_kutilish() {
    if [ -z "${DATABASE_URL:-}" ]; then
        return
    fi

    echo "Ma'lumotlar bazasi tayyorligi kutilmoqda..."
    for urinish in $(seq 1 30); do
        if python -c 'import os, psycopg; psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=2).close()' >/dev/null 2>&1; then
            echo "Ma'lumotlar bazasi tayyor."
            return
        fi
        echo "Ma'lumotlar bazasi hali tayyor emas ($urinish/30)..."
        sleep 2
    done
    echo "XATO: ma'lumotlar bazasiga ulanish imkoni bo'lmadi." >&2
    exit 1
}

case "${1:-}" in
    celery|gunicorn|uvicorn|python|python3|manage.py)
        db_kutilish
        ;;
esac

case "${1:-}" in
    celery|gunicorn|uvicorn|python|python3|manage.py)
        echo "Migratsiyalarni ishga tushirish..."
        python manage.py migrate --noinput

        echo "Statik fayllarni yig'ish..."
        python manage.py collectstatic --noinput
        ;;
esac

exec "$@"
