"""Ovozli suhbat uchun WebSocket consumer (TZ 5.2).

Kanal: /ws/voice/{conversation_id}/

Oqim: mijozdan kelgan audio bo'laklari (bytes) navbatga qo'yiladi, ular
Agent.VoiceChat bidi-stream'iga uzatiladi; Go qaytargan VoiceEvent'lar
mijozga qaytariladi (audio — binary, matn — JSON).

gRPC klienti sinxron (grpcio), shuning uchun stream alohida oqimda (thread)
aylantiriladi va natijalar event loop'ga uzatiladi — event loop bloklanmaydi.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from typing import Any
from urllib.parse import parse_qs

import structlog
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from apps.chat.grpc_client import voice_chat_stream
from apps.chat.models import Conversation
from apps.chat.tasks import save_message_and_usage

logger = structlog.get_logger(__name__)

# Mijozdan kelayotgan audio bo'laklari uchun navbat chegarasi
QUEUE_MAXSIZE = 64


class VoiceChatConsumer(AsyncWebsocketConsumer):
    """Ovozli suhbat kanali."""

    conversation_id: str
    _queue: asyncio.Queue[bytes | None]
    _pump_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        """Ulanishni tekshiradi va qabul qiladi."""

        user = self.scope.get("user")
        if user is None or not getattr(user, "is_authenticated", False):
            # Autentifikatsiyasiz ulanish rad etiladi (1008 — policy violation)
            await self.close(code=1008)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        conversation = await self._get_conversation(self.conversation_id, user)
        if conversation is None:
            await self.close(code=1008)
            return

        self._conversation = conversation
        self._user = user
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        self._locale = parse_qs(query_string).get("locale", ["uz"])[0] or "uz"
        self._transcript = ""

        self._queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        await self.accept()
        self._pump_task = asyncio.create_task(self._pump_events())
        logger.info("voice_ws_connected", conversation_id=self.conversation_id)

    async def disconnect(self, close_code: int) -> None:
        """Ulanish uzilganda gRPC oqimini to'xtatadi."""

        queue = getattr(self, "_queue", None)
        if queue is not None:
            # None — oqim tugaganini bildiradigan belgi
            await queue.put(None)
        if self._pump_task is not None:
            self._pump_task.cancel()
        logger.info(
            "voice_ws_disconnected",
            conversation_id=getattr(self, "conversation_id", None),
            code=close_code,
        )

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """Mijozdan kelgan audio bo'lagini navbatga qo'yadi."""

        if bytes_data:
            await self._queue.put(bytes_data)
            return
        if text_data:
            payload = json.loads(text_data)
            if payload.get("kind") == "end":
                await self._queue.put(None)

    # ── Ichki yordamchilar ────────────────────────────────────────────

    @staticmethod
    @sync_to_async
    def _get_conversation(conversation_id: str, user: Any) -> Conversation | None:
        """Suhbatni topadi va foydalanuvchining unga huquqi borligini tekshiradi."""

        user_model = get_user_model()
        queryset = Conversation.objects.filter(pk=conversation_id, is_active=True)
        if not isinstance(user, user_model):
            return None
        if getattr(user, "role", None) == "employee":
            queryset = queryset.filter(user=user)
        else:
            queryset = queryset.filter(tenant=user.tenant)
        return queryset.first()

    def _chunk_iterator(self, loop: asyncio.AbstractEventLoop) -> Iterator[bytes]:
        """Navbatdagi audio bo'laklarini sinxron iteratorga aylantiradi."""

        while True:
            future = asyncio.run_coroutine_threadsafe(self._queue.get(), loop)
            chunk = future.result()
            if chunk is None:
                return
            yield chunk

    async def _pump_events(self) -> None:
        """gRPC oqimini alohida thread'da aylantirib, natijani mijozga uzatadi."""

        loop = asyncio.get_running_loop()

        def _consume() -> list[Any]:
            return list(
                voice_chat_stream(
                    self._chunk_iterator(loop),
                    session_id=self._conversation.session_id,
                    user_id=str(self._user.id),
                    tenant_id=str(self._conversation.tenant_id),
                    role=str(self._user.role),
                    locale=self._locale,
                    customer_mode="1" if self._conversation.mode == "customer" else "0",
                    conversation_id=self.conversation_id,
                )
            )

        try:
            events = await asyncio.to_thread(_consume)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("voice_stream_failed", error=str(exc))
            await self.send(
                text_data=json.dumps(
                    {"kind": "error", "error": "AI xizmati vaqtincha ishlamayapti"},
                    ensure_ascii=False,
                )
            )
            await self.close(code=1011)
            return

        for event in events:
            kind = getattr(event, "kind", "")
            chat_event = getattr(event, "chat_event", None)
            if kind == "transcript":
                transcript = getattr(event, "content", "")
                if transcript:
                    self._transcript = f"{self._transcript} {transcript}".strip()
                    await self.send(
                        text_data=json.dumps(
                            {"kind": "transcript", "content": transcript},
                            ensure_ascii=False,
                        )
                    )

            audio = getattr(event, "audio_data", None) or getattr(event, "audio", None)
            if audio:
                await self.send(bytes_data=audio)
            text = getattr(event, "content", None) or getattr(event, "text", None)
            if not isinstance(text, str):
                text = None
            if text and kind != "transcript":
                await self.send(
                    text_data=json.dumps(
                        {"kind": kind or "content", "content": text},
                        ensure_ascii=False,
                    )
                )

            if kind == "done":
                usage = getattr(chat_event, "usage", None) or getattr(event, "usage", None)
                save_message_and_usage.delay(
                    conversation_id=self.conversation_id,
                    user_message_content=self._transcript,
                    ai_event_data={"content": "", "usage": self._proto_to_dict(usage)},
                    tenant_id=str(self._conversation.tenant_id),
                )

    @staticmethod
    def _proto_to_dict(value: Any) -> dict[str, Any]:
        """Proto usage obyektini task uchun oddiy lug'atga aylantiradi."""
        if value is None:
            return {}
        fields = (
            "provider",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "cached_tokens",
            "reasoning_tokens",
            "stt_seconds",
            "tts_chars",
            "tool_calls_json",
            "latency_ms",
        )
        return {field: getattr(value, field) for field in fields if hasattr(value, field)}
