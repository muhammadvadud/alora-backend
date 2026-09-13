"""VoiceChat WebSocket oqimi testlari."""

from __future__ import annotations

import asyncio
from unittest import mock

from apps.chat.consumers import VoiceChatConsumer


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
