"""Suhbat biznes mantiqlari."""

from __future__ import annotations

from typing import Any

from django.core.cache import cache
from rest_framework.exceptions import Throttled

from apps.chat.models import Conversation, ConversationStatus


def archive_conversation(conversation: Conversation) -> None:
    """Suhbatni arxivlash."""
    conversation.status = ConversationStatus.ARCHIVED
    conversation.save(update_fields=["status", "updated_at"])


def reset_conversation_context(conversation: Conversation) -> None:
    """Suhbat kontekstini tozalash."""
    conversation.context = {}
    conversation.save(update_fields=["context", "updated_at"])


from apps.usage.services import enforce_usage_limit


def check_usage_limit(user: Any) -> None:
    """Foydalanuvchining limitini tekshirish."""
    enforce_usage_limit(user)


def check_rate_limit(user: Any) -> None:
    """Chat uchun rate limitni Redis orqali tekshirish."""
    role = getattr(user, "role", "employee")

    try:
        from apps.pricing.models import CalcRule

        rule = CalcRule.objects.get(key=f"chat_rate_limit_{role}")
        limit = int(rule.value)
    except Exception:  # noqa: BLE001
        limits = {"employee": 10, "manager": 30, "admin": 100}
        limit = limits.get(role, 10)

    key = f"chat_rate_limit:{user.id}"

    # Atomik poyga holatini oldini olish
    cache.add(key, 0, timeout=60)
    count = cache.incr(key)

    if count > limit:
        raise Throttled(detail="Siz juda ko'p xabar yubordingiz. Iltimos biroz kuting.")


def build_agent_context(conversation: Conversation, user: Any) -> dict[str, str]:
    """Go agentga yuboriladigan `ChatRequest.context` (GO-CONTRACT §1.1).

    Kalitlar shartnomada qat'iy: `role`, `customer_mode`, `conversation_id`.
    Mijoz rejimi suhbatning `mode` maydonidan olinadi — mobil uni PATCH bilan
    almashtiradi, har xabarda qayta yubormaydi.
    """
    from apps.common.choices import ConversationMode

    return {
        "role": str(getattr(user, "role", "") or ""),
        "customer_mode": "1" if conversation.mode == ConversationMode.CUSTOMER else "0",
        "conversation_id": str(conversation.id),
    }
