"""gRPC klient — Go Agent bilan aloqa.

Ulanish pool'i, retry, deadline, keep-alive sozlamalari.
Manzil settings GRPC_AGENT_ADDR dan olinadi.
"""

from __future__ import annotations

import random
import threading
import time
from typing import TYPE_CHECKING, Any

import grpc
import structlog
from django.conf import settings

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = structlog.get_logger(__name__)

# Retry qoidalari
_MAX_RETRIES = 3
_RETRYABLE_CODES = {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED}
_BACKOFF_BASE_MS = 500
_BACKOFF_MAX_MS = 5000


class GRPCClientPool:
    """gRPC kanallar pool'i — thread-safe, qayta ishlatiladi."""

    def __init__(self) -> None:
        self._channels: dict[str, grpc.Channel] = {}
        self._lock = threading.Lock()

    def get_channel(self, target: str | None = None) -> grpc.Channel:
        """Berilgan manzil uchun kanal qaytaradi (yangi yoki mavjud)."""
        if target is None:
            target = getattr(settings, "GRPC_AGENT_ADDR", "localhost:50051")

        with self._lock:
            if target not in self._channels:
                self._channels[target] = self._create_channel(target)
            return self._channels[target]

    def _create_channel(self, target: str) -> grpc.Channel:
        """Yangi kanal yaratadi — keepalive va deadline sozlamalari bilan."""
        options = [
            # Keepalive: serverga periodik ping yuborish
            ("grpc.keepalive_time_ms", 30_000),
            ("grpc.keepalive_timeout_ms", 10_000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.http2.min_time_between_pings_ms", 10_000),
            # Max message hajmi: 4 MB
            ("grpc.max_receive_message_length", 4 * 1024 * 1024),
        ]

        channel = grpc.insecure_channel(target, options=options)

        logger.info(
            "gRPC kanal yaratildi",
            target=target,
        )

        return channel

    def close_all(self) -> None:
        """Barcha kanallarni yopadi."""
        with self._lock:
            for target, channel in self._channels.items():
                channel.close()
                logger.info("gRPC kanal yopildi", target=target)
            self._channels.clear()


# Global pool instansiyasi
_pool = GRPCClientPool()


def get_agent_channel() -> grpc.Channel:
    """Agent kanalini qaytaradi."""
    return _pool.get_channel()


def close_all_channels() -> None:
    """Barcha kanallarni yopadi."""
    _pool.close_all()


def _retry_with_backoff(
    func: Any,
    *args: Any,
    max_retries: int = _MAX_RETRIES,
    **kwargs: Any,
) -> Any:
    """Exponential backoff bilan qayta urinish.

    Faqat UNAVAILABLE va DEADLINE_EXCEEDED uchun retry qiladi.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as e:
            last_exception = e
            code = e.code()  # type: ignore[union-attr]

            if code not in _RETRYABLE_CODES:
                raise

            if attempt < max_retries - 1:
                # Exponential backoff + jitter
                backoff_ms = min(
                    _BACKOFF_BASE_MS * (2**attempt) + random.randint(0, _BACKOFF_BASE_MS),
                    _BACKOFF_MAX_MS,
                )
                backoff_sec = backoff_ms / 1000.0

                logger.warning(
                    "gRPC qayta urinish",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    backoff_ms=backoff_ms,
                    code=code.name,
                )

                time.sleep(backoff_sec)

    # Barcha urinishlar muvaffaqiyatsiz
    raise last_exception  # type: ignore[misc]


def chat_stream(
    session_id: str,
    user_id: str,
    tenant_id: str,
    message: str,
    locale: str = "uz",
    context: dict[str, str] | None = None,
    deadline_seconds: float = 60.0,
) -> Iterator[Any]:
    """Agent.Chat stream ochadi va event'larni qaytaradi.

    Args:
        session_id: Sessiya identifikatsiyasi.
        user_id: Foydalanuvchi UUID si.
        tenant_id: Tenant UUID si.
        message: Foydalanuvchi xabari.
        locale: Interfeys tili (uz/ru).
        context: Qo'shimcha kontekst.
        deadline_seconds: Javob kutish muddati (soniya).

    Yields:
        ChatEvent obyektlari.

    Raises:
        AgentUnavailable: Go agent ishlamaganda.
    """
    from grpc_gen import alora_pb2, alora_pb2_grpc

    channel = get_agent_channel()
    stub = alora_pb2_grpc.AgentStub(channel)

    ctx_map = context or {}

    request = alora_pb2.ChatRequest(
        session_id=session_id,
        user_id=user_id,
        tenant_id=tenant_id,
        message=message,
        locale=locale,
        context=ctx_map,
    )

    def _do_stream() -> Any:
        return stub.Chat(request, timeout=deadline_seconds)

    try:
        # Retry only for the initial connection/call creation
        call = _retry_with_backoff(_do_stream)
        return call
    except grpc.RpcError as e:
        code = e.code()  # type: ignore[union-attr]
        if code == grpc.StatusCode.UNAVAILABLE:
            from apps.chat.exceptions import AgentUnavailable

            raise AgentUnavailable() from e
        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            from apps.chat.exceptions import AgentTimeout

            raise AgentTimeout() from e
        raise


def reset_session(
    session_id: str,
    user_id: str,
    deadline_seconds: float = 10.0,
) -> Any:
    """Agent.ResetSession chaqiradi — kontekstni tozalaydi."""
    from grpc_gen import alora_pb2, alora_pb2_grpc

    channel = get_agent_channel()
    stub = alora_pb2_grpc.AgentStub(channel)

    request = alora_pb2.ResetRequest(
        session_id=session_id,
        user_id=user_id,
    )

    def _do_reset() -> Any:
        return stub.ResetSession(request, timeout=deadline_seconds)

    try:
        return _retry_with_backoff(_do_reset)
    except grpc.RpcError as e:
        code = e.code()  # type: ignore[union-attr]
        if code == grpc.StatusCode.UNAVAILABLE:
            from apps.chat.exceptions import AgentUnavailable

            raise AgentUnavailable() from e
        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            from apps.chat.exceptions import AgentTimeout

            raise AgentTimeout() from e
        raise


def health_check(deadline_seconds: float = 5.0) -> dict[str, Any]:
    """Agent.Health tekshiruvi — sog'lik holatini qaytaradi."""
    from grpc_gen import alora_pb2, alora_pb2_grpc

    channel = get_agent_channel()
    stub = alora_pb2_grpc.AgentStub(channel)

    request = alora_pb2.Empty()

    try:
        response = stub.Health(request, timeout=deadline_seconds)
        return {
            "status": response.status,
            "version": response.version,
            "active_sessions": response.active_sessions,
            "last_error": response.last_error,
        }
    except grpc.RpcError as e:
        return {
            "status": "unavailable",
            "version": "",
            "active_sessions": 0,
            "last_error": str(e),
        }


def voice_chat_stream(
    chunks: Iterator[Any],
    deadline_seconds: float = 120.0,
) -> Iterator[Any]:
    """Agent.VoiceChat bidi-stream ochadi.

    Args:
        chunks: VoiceChunk iteratori (audio kirish).
        deadline_seconds: Javob kutish muddati.

    Yields:
        VoiceEvent obyektlari.
    """
    from grpc_gen import alora_pb2_grpc

    channel = get_agent_channel()
    stub = alora_pb2_grpc.AgentStub(channel)

    def _do_voice_stream() -> Iterator[Any]:
        return stub.VoiceChat(chunks, timeout=deadline_seconds)

    try:
        yield from _retry_with_backoff(lambda: list(_do_voice_stream()))
    except grpc.RpcError as e:
        code = e.code()  # type: ignore[union-attr]
        if code == grpc.StatusCode.UNAVAILABLE:
            from apps.chat.exceptions import AgentUnavailable

            raise AgentUnavailable() from e
        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            from apps.chat.exceptions import AgentTimeout

            raise AgentTimeout() from e
        raise
