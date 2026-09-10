"""Suhbat selectorlari."""

from typing import Any

from django.db.models import QuerySet

from apps.chat.models import Conversation, Message


def get_messages_for_conversation(conversation_id: str) -> QuerySet[Message]:
    """Suhbat uchun xabarlarni qaytaradi."""
    return Message.objects.filter(conversation_id=conversation_id).order_by("-created_at")


def get_transcript(conversation_id: str) -> list[dict[str, Any]]:
    """Suhbatning to'liq transkriptini qaytaradi."""
    messages = Message.objects.filter(conversation_id=conversation_id).order_by("created_at")

    transcript = []
    for msg in messages:
        transcript.append(
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_result": msg.tool_result,
                "created_at": msg.created_at,
            }
        )
    return transcript


def get_conversation_by_id(conversation_id: str) -> Conversation | None:
    """Suhbatni ID bo'yicha olish."""
    return Conversation.objects.filter(id=conversation_id).first()
