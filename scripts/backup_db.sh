#!/bin/bash
set -euo pipefail
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
mkdir -p "$DEST"
pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" > "${DEST}/alora-${STAMP}.dump"
find "$DEST" -name 'alora-*.dump' -mtime "+${RETENTION_DAYS}" -delete
if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
    aws s3 cp "${DEST}/alora-${STAMP}.dump" "s3://${BACKUP_S3_BUCKET}/db/"
fi
echo "Backup tayyor: alora-${STAMP}.dump"
