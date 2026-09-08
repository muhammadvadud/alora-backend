from django.http import JsonResponse
from django.db import connection
import redis
from django.conf import settings

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
    except Exception as e:
        status["database"] = "error"
        status["status"] = "error"
        status["database_error"] = str(e)
        
    # Redis tekshiruvi
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception as e:
        status["redis"] = "error"
        status["status"] = "error"
        status["redis_error"] = str(e)
        
    status_code = 200 if status["status"] == "ok" else 503
    return JsonResponse(status, status=status_code)
