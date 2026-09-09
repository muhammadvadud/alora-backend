"""WebSocket yo'llari (Channels).

TZ 5.2: ovozli suhbat kanali. HTTP yo'llari apps/chat/urls.py da.
"""

from __future__ import annotations

from django.urls import re_path

from apps.chat.consumers import VoiceChatConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/voice/(?P<conversation_id>[0-9a-f-]{36})/$",
        VoiceChatConsumer.as_asgi(),
        name="voice-chat",
    ),
]
