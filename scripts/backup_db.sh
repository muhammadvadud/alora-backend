#!/bin/bash
# PostgreSQL bazasini zaxiralash (TZ §11).
#
# `pg_dump` host'da o'rnatilmagan bo'lsa, skript uni Postgres konteyneri ichidan
# ishlatadi — docker-compose bilan deploy qilingan muhitda odatiy holat shu.
#
# Muhit o'zgaruvchilari:
#   DATABASE_URL           — majburiy
#   BACKUP_DIR             — nusxalar katalogi (default: /backups)
#   BACKUP_RETENTION_DAYS  — necha kundan eski nusxalar o'chiriladi (default: 14)
#   BACKUP_PG_CONTAINER    — pg_dump ishlatiladigan konteyner (default: backend-db-1)
#   BACKUP_S3_BUCKET       — berilsa, nusxa S3 ga ham yuklanadi
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL berilishi shart}"

STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
PG_CONTAINER="${BACKUP_PG_CONTAINER:-backend-db-1}"
TARGET="${DEST}/alora-${STAMP}.dump"

mkdir -p "$DEST"

if command -v pg_dump >/dev/null 2>&1; then
    pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" > "$TARGET"
elif docker exec "$PG_CONTAINER" true >/dev/null 2>&1; then
    echo "pg_dump host'da yo'q — '${PG_CONTAINER}' konteyneri ishlatilmoqda."
    docker exec "$PG_CONTAINER" pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" > "$TARGET"
else
    echo "XATO: pg_dump topilmadi va '${PG_CONTAINER}' konteyneriga ulanib bo'lmadi." >&2
    exit 1
fi

# Bo'sh yoki juda kichik dump — muvaffaqiyat emas.
if [ ! -s "$TARGET" ]; then
    echo "XATO: zaxira fayli bo'sh: $TARGET" >&2
    rm -f "$TARGET"
    exit 1
fi

# Retention: eski nusxalarni tozalash
find "$DEST" -name 'alora-*.dump' -mtime "+${RETENTION_DAYS}" -delete

# S3 ga yuklash (ixtiyoriy)
if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
    aws s3 cp "$TARGET" "s3://${BACKUP_S3_BUCKET}/db/"
fi

echo "Backup tayyor: $TARGET ($(du -h "$TARGET" | cut -f1))"
