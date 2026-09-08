#!/bin/bash
set -e

echo "Migratsiyalarni ishga tushirish..."
python manage.py migrate --noinput

echo "Statik fayllarni yig'ish..."
python manage.py collectstatic --noinput

echo "Serverni ishga tushirish..."
exec "$@"
