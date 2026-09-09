#!/usr/bin/env bash
# protos/alora.proto faylini ko'rsatilgan katalogga nusxalaydi (masalan, Go repozitoriyasiga).
# Nusxalashdan oldin mavjud fayl bilan farqni (diff) ko'rsatadi.
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "XATO: Maqsadli katalog (target directory) ko'rsatilmadi." >&2
    echo "Foydalanish: $0 <maqsadli_katalog_yoli>" >&2
    exit 1
fi

TARGET_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROTO_FILE="${PROJECT_ROOT}/protos/alora.proto"

if [ ! -f "$PROTO_FILE" ]; then
    echo "XATO: ${PROTO_FILE} topilmadi!" >&2
    exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo "XATO: Maqsadli katalog topilmadi: ${TARGET_DIR}" >&2
    exit 1
fi

TARGET_FILE="${TARGET_DIR}/alora.proto"

if [ -f "$TARGET_FILE" ]; then
    echo "Mavjud fayl bilan farqlar (diff):"
    echo "----------------------------------------"
    # diff exit code 1 bo'lsa ham skript to'xtab qolmasligi uchun || true
    diff -u "$TARGET_FILE" "$PROTO_FILE" || true
    echo "----------------------------------------"
else
    echo "Maqsadli katalogda alora.proto fayli hozircha yo'q."
fi

cp "$PROTO_FILE" "$TARGET_FILE"
echo "Muvaffaqiyatli nusxalandi: ${TARGET_FILE}"
