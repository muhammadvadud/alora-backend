"""WS JWT middleware testlari (tasks 16.1, mobil rules §8.6).

Kelishuv: token FAQAT `Sec-WebSocket-Protocol: bearer, <access>` sarlavhasidan
olinadi. `?token=` query parametri qo'llab-quvvatlanmaydi (access-log sizib chiqadi).
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.middleware import JwtAuthMiddleware, extract_token

pytestmark = pytest.mark.django_db(transaction=True)


def _scope(query: str = "", protocol: str | None = None) -> dict[str, Any]:
    headers = [(b"host", b"testserver")]
    if protocol is not None:
        headers.append((b"sec-websocket-protocol", protocol.encode()))
    return {"type": "websocket", "query_string": query.encode(), "headers": headers}


class _Capture:
    scope: dict[str, Any] | None = None

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        self.scope = scope


def _saved_user(tenant: Any, user: Any) -> Any:
    tenant.save(force_insert=True)
    user.tenant = tenant
    user.save(force_insert=True)
    return user


def test_extract_token_subprotocol() -> None:
    assert extract_token(_scope(protocol="bearer, h456")) == "h456"


def test_extract_token_yoq() -> None:
    assert extract_token(_scope(query="locale=ru")) is None


def test_extract_token_query_butunlay_inkor_qilinadi() -> None:
    """`?token=` endi o'qilmaydi — token URL'da access-log'ga tushadi."""
    assert extract_token(_scope(query="token=q123&locale=uz")) is None


def test_extract_token_subprotocol_ustun_query_dan() -> None:
    """Subprotocol bitta manba bo'ldi: `?token=` berilsa ham subprotocol olinadi."""
    assert extract_token(_scope(query="token=q123", protocol="bearer, h456")) == "h456"


def test_extract_token_bo_sh_qism_yoq() -> None:
    """`bearer, ` bo'sh qismli sarlavha token deb hisoblanmaydi."""
    assert extract_token(_scope(protocol="bearer, ")) is None


def test_haqiqiy_access_token_user_beradi(tenant: Any, employee_user: Any) -> None:
    user = _saved_user(tenant, employee_user)
    token = str(AccessToken.for_user(user))
    inner = _Capture()

    asyncio.run(JwtAuthMiddleware(inner)(_scope(protocol=f"bearer, {token}"), None, None))

    assert inner.scope is not None
    assert inner.scope["user"].pk == user.pk


def test_yaroqsiz_token_anonymous(tenant: Any) -> None:
    inner = _Capture()
    asyncio.run(JwtAuthMiddleware(inner)(_scope(protocol="bearer, buzilgan.token.x"), None, None))
    assert inner.scope is not None
    assert isinstance(inner.scope["user"], AnonymousUser)


def test_token_bolmasa_anonymous() -> None:
    inner = _Capture()
    asyncio.run(JwtAuthMiddleware(inner)(_scope(), None, None))
    assert inner.scope is not None
    assert isinstance(inner.scope["user"], AnonymousUser)


def test_query_token_bergan_ulanish_anonymous(tenant: Any, employee_user: Any) -> None:
    """Faqat `?token=` bilan kelgan ulanish autentifikatsiyasiz qoladi."""
    user = _saved_user(tenant, employee_user)
    token = str(AccessToken.for_user(user))
    inner = _Capture()

    asyncio.run(JwtAuthMiddleware(inner)(_scope(query=f"token={token}"), None, None))

    assert inner.scope is not None
    assert isinstance(inner.scope["user"], AnonymousUser)


def test_bloklangan_foydalanuvchi_anonymous(tenant: Any, employee_user: Any) -> None:
    user = _saved_user(tenant, employee_user)
    token = str(AccessToken.for_user(user))
    user.is_active = False
    user.save(update_fields=["is_active"])
    inner = _Capture()

    asyncio.run(JwtAuthMiddleware(inner)(_scope(protocol=f"bearer, {token}"), None, None))

    assert inner.scope is not None
    assert isinstance(inner.scope["user"], AnonymousUser)
