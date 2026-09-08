#!/usr/bin/env bash
# protos/alora.proto dan Python gRPC kodini generatsiya qiladi.
# grpcio-tools ishlatiladi. Chiqish papkasi: grpc_gen/
# grpc_gen/ ichidagi fayllar QO'lda tahrirlanmaydi — faqat shu skript orqali yangilanadi.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="${PROJECT_ROOT}/protos"
PROTO_FILE="${PROTO_DIR}/alora.proto"
OUT_DIR="${PROJECT_ROOT}/grpc_gen"

if [ ! -f "$PROTO_FILE" ]; then
    echo "XATO: ${PROTO_FILE} topilmadi" >&2
    exit 1
fi

# Oldingi generatsiya kodini tozalash
rm -rf "${OUT_DIR:?}"/*
mkdir -p "$OUT_DIR"

# grpcio-tools orqali generatsiya
python -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTO_FILE"

# grpc_gen paketini yaratish
touch "${OUT_DIR}/__init__.py"

echo "Generatsiya tugadi: ${OUT_DIR}/"
echo "Fayllar:"
ls -la "${OUT_DIR}/"
