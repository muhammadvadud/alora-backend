"""ASGI kirish nuqtasi (Uvicorn).

HTTP so'rovlar Django'ning odatiy ASGI ilovasiga, WebSocket ulanishlari esa
Channels router'iga yo'naltiriladi (TZ 5.2 — ovozli suhbat kanali).
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

# Django ilovasi WebSocket yo'llarini import qilishdan OLDIN yuklanishi shart
django_asgi_application = get_asgi_application()

from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
