import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Tizim holatini tekshirish.
    Ma'lumotlar bazasi va Redis ulanishini tekshiradi.
    (gRPC tekshiruvi keyin qo'shiladi)
    """
    status = {
        "status": "ok",
        "database": "ok",
        "redis": "ok"
    }
    
    # DB tekshiruvi
    try:
        connection.ensure_connection()
    # Health check hech qachon yiqilmasligi kerak: har qanday nosozlik
    # javobda holat sifatida qaytadi (TZ 0.14).
    except Exception as e:  # noqa: BLE001
        status["database"] = "error"
        status["status"] = "error"
        status["database_error"] = str(e)
        
    # Redis tekshiruvi
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    # Yuqoridagi sabab: nosozlik javobda qaytadi, so'rov yiqilmaydi.
    except Exception as e:  # noqa: BLE001
        status["redis"] = "error"
        status["status"] = "error"
        status["redis_error"] = str(e)
        
    status_code = 200 if status["status"] == "ok" else 503
    return JsonResponse(status, status=status_code)
