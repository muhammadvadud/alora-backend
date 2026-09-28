"""Ovozli WS handshake — haqiqiy ASGI zanjiri orqali (config.asgi.application).

Consumer testlari scope'ni qo'lda yasaydi va validator/middleware zanjirini
chetlab o'tadi — shu sabab `Origin`siz mobil klientning 403 olishi va
subprotocol tanlovi faqat jonli sinovda topildi (2026-09-28). Bu testlar
handshake'ni ilova kirish nuqtasidan boshlab tekshiradi.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest import mock

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from apps.common.factories import EmployeeFactory, TenantFactory
from config.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)


def _scope(conversation_id: str, token: str | None, origin: str | None) -> dict[str, Any]:
    headers = [(b"host", b"localhost")]
    subprotocols: list[str] = []
    if token is not None:
        headers.append((b"sec-websocket-protocol", f"bearer, {token}".encode()))
        subprotocols = ["bearer", token]
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    path = f"/ws/voice/{conversation_id}/"
    return {
        "type": "websocket",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"locale=uz",
        "headers": headers,
        "subprotocols": subprotocols,
        "client": ("127.0.0.1", 1),
        "server": ("localhost", 80),
    }


def _handshake(scope: dict[str, Any]) -> dict[str, Any]:
    """Ilovaga `websocket.connect` yuborib, birinchi javob xabarini qaytaradi."""

    async def run() -> dict[str, Any]:
        inbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        outbox: list[dict[str, Any]] = []
        await inbox.put({"type": "websocket.connect"})

        async def receive() -> dict[str, Any]:
            return await inbox.get()

        async def send(message: dict[str, Any]) -> None:
            outbox.append(message)

        task = asyncio.create_task(application(scope, receive, send))
        for _ in range(50):
            if outbox:
                break
            await asyncio.sleep(0.05)
        await inbox.put({"type": "websocket.disconnect", "code": 1000})
        try:
            await asyncio.wait_for(task, 3)
        except (TimeoutError, asyncio.CancelledError):
            task.cancel()
        return outbox[0]

    # gRPC oqimi bu testda kerak emas — pump ishga tushmaydi.
    with mock.patch("apps.chat.consumers.VoiceChatConsumer._pump_events", new=mock.AsyncMock()):
        return asyncio.run(run())


@pytest.fixture()
def employee_conversation():
    from apps.chat.models import Conversation

    tenant = TenantFactory()
    user = EmployeeFactory(tenant=tenant)
    conversation = Conversation.objects.create(user=user, tenant=tenant)
    return user, conversation


def test_native_client_without_origin_is_accepted_with_bearer(employee_conversation):
    user, conversation = employee_conversation
    token = str(AccessToken.for_user(user))

    message = _handshake(_scope(str(conversation.id), token, origin=None))

    assert message == {"type": "websocket.accept", "subprotocol": "bearer"}


def test_allowed_origin_is_accepted(employee_conversation):
    user, conversation = employee_conversation
    token = str(AccessToken.for_user(user))

    message = _handshake(_scope(str(conversation.id), token, origin="http://localhost"))

    assert message["type"] == "websocket.accept"


def test_foreign_origin_is_rejected(employee_conversation):
    user, conversation = employee_conversation
    token = str(AccessToken.for_user(user))

    message = _handshake(_scope(str(conversation.id), token, origin="https://evil.example"))

    assert message["type"] == "websocket.close"


def test_missing_token_is_rejected(employee_conversation):
    _, conversation = employee_conversation

    message = _handshake(_scope(str(conversation.id), None, origin=None))

    assert message["type"] == "websocket.close"
