import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def _check_database() -> dict:
    try:
        connection.ensure_connection()
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "detail": str(e)}


def _check_redis() -> dict:
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "detail": str(e)}


def health_check(request):
    """DB, Redis va Go agent holatini qaytaradi."""
    from apps.chat.health import grpc_health

    checks = {
        "database": _check_database(),
        "redis": _check_redis(),
        "grpc": grpc_health(),
    }

    # gRPC ixtiyoriy bog'liqlik: u yiqilsa tizim "degraded", "error" emas.
    hard_failed = any(c["status"] != "ok" for k, c in checks.items() if k != "grpc")
    soft_failed = checks["grpc"]["status"] != "ok"

    overall = "error" if hard_failed else ("degraded" if soft_failed else "ok")
    status_code = 503 if hard_failed else 200

    return JsonResponse({"status": overall, **checks}, status=status_code)
