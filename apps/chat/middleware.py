"""WebSocket uchun JWT autentifikatsiya middleware'i (mobil rules §8.6, tasks 16.1).

Session cookie o'rniga `access` token quyidagi joylardan olinadi (birinchisi ustun):
1. Query: `?token=<access>` — mobil `VoiceSocket` shu variantni ishlatadi.
2. `Sec-WebSocket-Protocol: bearer, <access>` sarlavhasi.

Token yo'q/yaroqsiz bo'lsa `scope["user"]` `AnonymousUser` bo'ladi va consumer
1008 bilan yopadi. Ma'lumotlar bazasiga faqat token tekshirilgandan keyin murojaat qilinadi.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import AccessToken

_PROTOCOL_PREFIX = "bearer"


def extract_token(scope: dict[str, Any]) -> str | None:
    """Scope'dan access tokenni ajratadi (query → subprotocol)."""

    query = parse_qs(scope.get("query_string", b"").decode("utf-8"))
    token = (query.get("token") or [""])[0].strip()
    if token:
        return token

    for name, value in scope.get("headers", []):
        if name != b"sec-websocket-protocol":
            continue
        parts = [p.strip() for p in value.decode("utf-8").split(",")]
        if len(parts) >= 2 and parts[0].lower() == _PROTOCOL_PREFIX:
            return parts[1] or None
    return None


@database_sync_to_async
def _get_user(token: str) -> Any:
    try:
        access = AccessToken(token)  # type: ignore[arg-type]  # stub: Token | None, haqiqatda str
    except (InvalidToken, TokenError):
        return AnonymousUser()
    user_id = access.get(jwt_settings.USER_ID_CLAIM)
    if user_id is None:
        return AnonymousUser()
    user_model = get_user_model()
    user = user_model.objects.filter(pk=user_id, is_active=True).first()
    return user if user is not None else AnonymousUser()


class JwtAuthMiddleware:
    """ASGI middleware: `scope["user"]` ni JWT bo'yicha to'ldiradi."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> Any:
        token = extract_token(scope)
        scope = dict(scope)
        scope["user"] = await _get_user(token) if token else AnonymousUser()
        return await self.inner(scope, receive, send)
