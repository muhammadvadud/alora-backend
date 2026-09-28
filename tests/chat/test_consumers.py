"""VoiceChat WebSocket oqimi testlari."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest import mock

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.consumers import VoiceChatConsumer
from apps.chat.middleware import BEARER_SUBPROTOCOL, JwtAuthMiddleware

pytestmark = pytest.mark.django_db(transaction=True)


def _make_scope(
    conversation_id: str,
    user: Any,
    *,
    query: str = "",
    protocol: str | None = None,
) -> dict[str, Any]:
    """Handshake sarlavhalarini imitatsiya qiluvchi ASGI scope."""

    headers: list[tuple[bytes, bytes]] = [(b"host", b"testserver")]
    if protocol is not None:
        headers.append((b"sec-websocket-protocol", protocol.encode()))
    return {
        "type": "websocket",
        "path": f"/ws/voice/{conversation_id}/",
        "query_string": query.encode(),
        "headers": headers,
        "url_route": {"kwargs": {"conversation_id": conversation_id}},
        "user": user,
    }


def _run_connect(scope: dict[str, Any], patch_pump: bool = True) -> VoiceChatConsumer:
    """`connect()` ni ishga tushiradi va consumer'ni qaytaradi.

    gRPC oqimini haqiqiy ishga tushirmaslik uchun `_pump_events` ni o'chirilgan
    (stub) holatda chaqiriladi — test faqat handshake natijasini tekshiradi.
    """

    consumer = VoiceChatConsumer()
    consumer.scope = scope
    consumer.accept = mock.AsyncMock()
    consumer.close = mock.AsyncMock()
    with mock.patch.object(VoiceChatConsumer, "_pump_events", mock.AsyncMock()):
        asyncio.run(consumer.connect())
    return consumer


def test_subprotocol_bilan_ulangan_tanlanadi(tenant, employee_user) -> None:
    """Mijoz "bearer" ni taklif qilsa, server javobda aynan "bearer" ni tanlaydi."""
    conversation = _conversation(tenant, employee_user)
    token = str(AccessToken.for_user(employee_user))
    scope = _make_scope(
        str(conversation.id), employee_user, protocol=f"{BEARER_SUBPROTOCOL}, {token}"
    )

    consumer = _run_connect(scope)

    consumer.accept.assert_awaited_once_with(subprotocol=BEARER_SUBPROTOCOL)
    consumer.close.assert_not_awaited()


def test_subprotocolsiz_ulangan_plain_accept(tenant, employee_user) -> None:
    """Taklif yo'q bo'lsa oddiy `accept()` — javob sarlavhasi bo'sh qoladi."""
    conversation = _conversation(tenant, employee_user)
    scope = _make_scope(str(conversation.id), employee_user)

    consumer = _run_connect(scope)

    consumer.accept.assert_awaited_once_with()


def test_locale_query_parametri_saqlanadi(tenant, employee_user) -> None:
    """`locale` token bo'lmagan parametr — query'da qoladi."""
    conversation = _conversation(tenant, employee_user)
    token = str(AccessToken.for_user(employee_user))
    scope = _make_scope(
        str(conversation.id),
        employee_user,
        query="locale=ru",
        protocol=f"{BEARER_SUBPROTOCOL}, {token}",
    )

    consumer = _run_connect(scope)

    assert consumer._locale == "ru"


def test_boshqa_subprotocol_taklif_qilinsa_plain_accept(tenant, employee_user) -> None:
    """`bearer`dan boshqa subprotocol tanlanmaydi — server hech narsani tanlamaydi."""
    conversation = _conversation(tenant, employee_user)
    scope = _make_scope(str(conversation.id), employee_user, protocol="chat, h456")

    consumer = _run_connect(scope)

    consumer.accept.assert_awaited_once_with()


def test_query_token_bilan_ulangan_1008_bilan_yopiladi(tenant, employee_user) -> None:
    """`?token=` orqali kelgan ulanish endi qabul qilinmaydi — 1008 bilan yopiladi.

    Haqiqiy yo'l: middleware query'dan token o'qimaydi → `scope["user"]` anonim
    bo'ladi → consumer 1008 bilan yopadi.
    """

    class _Capture:
        scope: dict[str, Any] | None = None

        async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
            self.scope = scope

    conversation = _conversation(tenant, employee_user)
    token = str(AccessToken.for_user(employee_user))
    scope = _make_scope(str(conversation.id), employee_user, query=f"token={token}")

    inner = _Capture()
    asyncio.run(JwtAuthMiddleware(inner)(scope, None, None))
    assert inner.scope is not None
    assert not inner.scope["user"].is_authenticated

    consumer = _run_connect(inner.scope)

    consumer.accept.assert_not_awaited()
    consumer.close.assert_awaited_once_with(code=1008)


def test_subprotocol_bergan_ulanish_1008_bilan_yopilmaydi(tenant, employee_user) -> None:
    """To'g'ri subprotocol bilan kelgan ulanish qabul qilinadi (1008 emas)."""
    conversation = _conversation(tenant, employee_user)
    token = str(AccessToken.for_user(employee_user))
    scope = _make_scope(
        str(conversation.id), employee_user, protocol=f"{BEARER_SUBPROTOCOL}, {token}"
    )

    consumer = _run_connect(scope)

    consumer.close.assert_not_awaited()
    consumer.accept.assert_awaited_once_with(subprotocol=BEARER_SUBPROTOCOL)


def test_subprotocol_orqali_auth_middleware_user_beradi(tenant, employee_user) -> None:
    """To'liq zanjir: `Sec-WebSocket-Protocol` → middleware → `scope["user"]` → accept."""

    class _Capture:
        scope: dict[str, Any] | None = None

        async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
            self.scope = scope

    conversation = _conversation(tenant, employee_user)
    token = str(AccessToken.for_user(employee_user))
    inner = _Capture()

    asyncio.run(
        JwtAuthMiddleware(inner)(
            _make_scope(str(conversation.id), employee_user, protocol=f"bearer, {token}"),
            None,
            None,
        )
    )

    assert inner.scope is not None
    authenticated = inner.scope["user"]
    assert authenticated.pk == employee_user.pk

    consumer = _run_connect(inner.scope)
    consumer.accept.assert_awaited_once_with(subprotocol=BEARER_SUBPROTOCOL)


def _conversation(tenant, user):
    """Tenant va foydalanuvchini saqlab, ulangan suhbat yaratadi."""

    from apps.chat.models import Conversation

    tenant.save(force_insert=True)
    user.tenant = tenant
    user.save(force_insert=True)
    return Conversation.objects.create(tenant=tenant, user=user, session_id="s-handshake")


def test_voice_stream_passes_metadata_and_handles_events() -> None:
    """Voice metadata uzatiladi, transcript/audio/done WS'ga to'g'ri chiqadi."""
    asyncio.run(_test_voice_stream_passes_metadata_and_handles_events())


async def _test_voice_stream_passes_metadata_and_handles_events() -> None:
    consumer = VoiceChatConsumer()
    consumer.conversation_id = "conversation-1"
    consumer._conversation = mock.Mock(
        session_id="session-1",
        tenant_id="tenant-1",
        mode="customer",
    )
    consumer._user = mock.Mock(id="user-1", role="employee")
    consumer._locale = "ru"
    consumer._transcript = ""
    consumer._queue = asyncio.Queue()
    consumer.send = mock.AsyncMock()

    usage = mock.Mock(
        provider="provider",
        model="model",
        prompt_tokens=2,
        completion_tokens=3,
        cached_tokens=0,
        reasoning_tokens=0,
        stt_seconds=1.0,
        tts_chars=4,
        tool_calls_json="[]",
        latency_ms=10,
    )
    done = mock.Mock(
        kind="done", content="", audio_data=b"", audio=b"", chat_event=mock.Mock(usage=usage)
    )
    events = [
        mock.Mock(kind="transcript", content="Salom", audio_data=b"", audio=b""),
        mock.Mock(kind="audio", content="", audio_data=b"audio", audio=b""),
        done,
    ]
    task = mock.Mock()

    with (
        mock.patch("apps.chat.consumers.voice_chat_stream", return_value=iter(events)) as stream,
        mock.patch("apps.chat.consumers.save_message_and_usage", task),
        mock.patch.object(consumer, "_chunk_iterator", return_value=iter(())),
    ):
        await consumer._pump_events()

    stream.assert_called_once_with(
        mock.ANY,
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role="employee",
        locale="ru",
        customer_mode="1",
        conversation_id="conversation-1",
    )
    assert consumer.send.await_count == 2
    assert (
        consumer.send.await_args_list[0].kwargs["text_data"]
        == '{"kind": "transcript", "content": "Salom"}'
    )
    assert consumer.send.await_args_list[1].kwargs["bytes_data"] == b"audio"
    task.delay.assert_called_once_with(
        conversation_id="conversation-1",
        user_message_content="Salom",
        ai_event_data={
            "content": "",
            "usage": {
                "provider": "provider",
                "model": "model",
                "prompt_tokens": 2,
                "completion_tokens": 3,
                "cached_tokens": 0,
                "reasoning_tokens": 0,
                "stt_seconds": 1.0,
                "tts_chars": 4,
                "tool_calls_json": "[]",
                "latency_ms": 10,
            },
        },
        tenant_id="tenant-1",
    )


def test_voice_stream_events_are_forwarded_before_stream_ends() -> None:
    """Haqiqiy streaming (16.2): birinchi event gRPC oqimi tugashidan OLDIN yuboriladi."""
    asyncio.run(_test_voice_stream_events_are_forwarded_before_stream_ends())


async def _test_voice_stream_events_are_forwarded_before_stream_ends() -> None:
    import threading

    consumer = VoiceChatConsumer()
    consumer.conversation_id = "conversation-2"
    consumer._conversation = mock.Mock(session_id="s", tenant_id="t", mode="employee")
    consumer._user = mock.Mock(id="u", role="employee")
    consumer._locale = "uz"
    consumer._transcript = ""
    consumer._queue = asyncio.Queue()

    first_sent = asyncio.Event()
    release_second = threading.Event()

    async def _send(text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if bytes_data == b"chunk-1":
            first_sent.set()

    consumer.send = _send  # type: ignore[method-assign]

    def _stream(*_args: object, **_kwargs: object):
        yield mock.Mock(kind="audio", content="", audio_data=b"chunk-1", audio=b"")
        # Ikkinchi event faqat birinchisi mijozga yetib borgach chiqariladi:
        # list(...) rejimida bu deadlock bo'lardi.
        assert release_second.wait(timeout=5), "birinchi audio oqim tugamasdan yuborilmadi"
        yield mock.Mock(kind="audio", content="", audio_data=b"chunk-2", audio=b"")

    async def _release_when_first_sent() -> None:
        await asyncio.wait_for(first_sent.wait(), timeout=5)
        release_second.set()

    with (
        mock.patch("apps.chat.consumers.voice_chat_stream", side_effect=_stream),
        mock.patch.object(consumer, "_chunk_iterator", return_value=iter(())),
    ):
        await asyncio.gather(consumer._pump_events(), _release_when_first_sent())

    assert first_sent.is_set()
