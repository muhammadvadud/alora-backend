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

# Python tarjimoni: avval loyiha venv'i, keyin PATH dagi python3/python.
if [ -x "${PROJECT_ROOT}/.venv/bin/python" ]; then
    PYTHON="${PROJECT_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON="$(command -v python)"
else
    echo "XATO: Python tarjimoni topilmadi" >&2
    exit 1
fi

if [ ! -f "$PROTO_FILE" ]; then
    echo "XATO: ${PROTO_FILE} topilmadi" >&2
    exit 1
fi

if ! "$PYTHON" -c "import grpc_tools.protoc" >/dev/null 2>&1; then
    echo "XATO: grpcio-tools o'rnatilmagan (${PYTHON})" >&2
    exit 1
fi

# Oldingi generatsiya kodini tozalash
rm -rf "${OUT_DIR:?}"
mkdir -p "$OUT_DIR"

# grpcio-tools orqali generatsiya
"$PYTHON" -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --pyi_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTO_FILE"

# grpc_gen paketini yaratish
touch "${OUT_DIR}/__init__.py"

# protoc `alora_pb2_grpc.py` ichida yassi `import alora_pb2` yozadi. Kod esa
# modullarni `from grpc_gen import ...` ko'rinishida paket sifatida import qiladi,
# shuning uchun importni paketga nisbatan qilib to'g'rilaymiz.
"$PYTHON" - "$OUT_DIR" <<'PYEOF'
import pathlib
import re
import sys

out_dir = pathlib.Path(sys.argv[1])
for stub in out_dir.glob("*_pb2_grpc.py"):
    text = stub.read_text(encoding="utf-8")
    fixed = re.sub(
        r"^import (\w+_pb2) as (\w+)$",
        r"from grpc_gen import \1 as \2",
        text,
        flags=re.MULTILINE,
    )
    if fixed != text:
        stub.write_text(fixed, encoding="utf-8")
        print(f"Import to'g'rilandi: {stub.name}")
PYEOF

echo "Generatsiya tugadi: ${OUT_DIR}/"
echo "Fayllar:"
ls -la "${OUT_DIR}/"
