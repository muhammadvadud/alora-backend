"""Suhbat uchun Celery tasklari."""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

import structlog
from celery import shared_task
from django.apps import apps
from django.db import transaction
from django.utils import timezone

from apps.chat.models import Conversation, ConversationStatus, Message
from apps.common.choices import MessageRole

logger = structlog.get_logger(__name__)


def _parse_json(raw: str, fallback: Any) -> Any:
    """JSON matnini xavfsiz parse qiladi."""
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return fallback


def _find_conversation(conversation_id: str, session_id: str = "") -> Conversation | None:
    """Suhbatni id yoki sessiya bo'yicha topadi."""
    if conversation_id:
        conversation = Conversation.objects.filter(pk=conversation_id).first()
        if conversation is not None:
            return conversation
    if session_id:
        return Conversation.objects.filter(session_id=session_id).first()
    return None


def _title_max_len() -> int:
    """Sarlavha uzunligi chegarasini CalcRule'dan o'qiydi (topilmasa 60)."""
    try:
        CalcRule = apps.get_model("pricing", "CalcRule")
        rule = CalcRule.objects.filter(key="conversation_title_max_len", is_active=True).first()
        if rule is not None:
            return max(10, min(int(rule.value), 250))
    except (LookupError, TypeError, ValueError):
        pass
    return 60


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def save_message(
    self,
    *,
    session_id: str = "",
    conversation_id: str = "",
    role: str = "",
    content: str = "",
    tool_calls_json: str = "[]",
    tool_result_json: str = "{}",
    audio_url: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> Message | None:
    """Xabarni suhbatga saqlaydi. · 13.2

    Idempotent: bir xil xabar (suhbat, rol, matn, tokenlar) ikki marta kelsa
    yangi yozuv yaratilmaydi — avvalgi yozuv qaytariladi.
    """
    conversation = _find_conversation(conversation_id, session_id)
    if conversation is None:
        logger.warning(
            "message_conversation_not_found", conversation_id=conversation_id, session_id=session_id
        )
        return None

    msg_role = role or MessageRole.ASSISTANT
    defaults = {
        "tool_calls": _parse_json(tool_calls_json, []) or [],
        "tool_result": _parse_json(tool_result_json, {}) or {},
        "audio_url": audio_url or "",
    }

    message, created = Message.objects.get_or_create(
        conversation=conversation,
        role=msg_role,
        content=content or "",
        tokens_in=int(tokens_in or 0),
        tokens_out=int(tokens_out or 0),
        defaults=defaults,
    )

    if not created:
        for field, value in defaults.items():
            if getattr(message, field) != value:
                setattr(message, field, value)
                message.save(update_fields=list(defaults))
                break

    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=timezone.now())
    return message


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def generate_conversation_title(self, conversation_id: str, message_text: str = "") -> str | None:
    """Birinchi javobdan keyin suhbatga qisqa sarlavha qo'yadi. · 13.3

    Sarlavha allaqachon bor bo'lsa qayta yozilmaydi (idempotent). Uzunlik
    chegarasi `CalcRule.conversation_title_max_len` dan o'qiladi.
    """
    conversation = Conversation.objects.filter(pk=conversation_id).first()
    if conversation is None:
        return None
    if conversation.title.strip():
        return conversation.title

    text = (message_text or "").strip()
    if not text:
        first = (
            Message.objects.filter(conversation=conversation, role=MessageRole.USER)
            .order_by("created_at")
            .values_list("content", flat=True)
            .first()
        )
        text = (first or "").strip()
    if not text:
        return None

    title = " ".join(text.split())[:_title_max_len()]

    Conversation.objects.filter(pk=conversation.pk, title="").update(title=title)
    return title


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def archive_old_conversations(self, older_than_months: int = 6) -> int:
    """6 oydan eski suhbatlarni arxiv holatiga o'tkazadi. · 13.5

    Idempotent: `update` orqali faqat faol suhbatlar tanlanadi, arxivlangan
    suhbat qayta o'zgartirilmaydi.
    """
    cutoff = timezone.now() - dt.timedelta(days=older_than_months * 30)
    archived = Conversation.objects.filter(
        status=ConversationStatus.ACTIVE,
        last_message_at__lt=cutoff,
    ).update(status=ConversationStatus.ARCHIVED)
    logger.info("old_conversations_archived", count=archived)
    return archived


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def save_message_and_usage(
    self,
    conversation_id: str,
    user_message_content: str,
    ai_event_data: dict[str, Any],
    tenant_id: str,
) -> None:
    """SSE `done` event'idan keyin xabar va foydalanish qaydnomasini saqlaydi.

    Yagona manba qoidasiga ko'ra xabar `save_message`, statistika esa
    `save_usage_record` orqali yoziladi — bu yerda faqat orkestratsiya.
    """
    conversation = Conversation.objects.filter(pk=conversation_id).first()
    if conversation is None:
        logger.warning("save_conversation_not_found", conversation_id=conversation_id)
        return

    usage = ai_event_data.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}

    with transaction.atomic():
        if user_message_content:
            save_message(
                session_id=conversation.session_id,
                role=MessageRole.USER,
                content=user_message_content,
            )

        ai_message = save_message(
            session_id=conversation.session_id,
            role=MessageRole.ASSISTANT,
            content=ai_event_data.get("content", ""),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )

        generate_conversation_title(
            conversation_id=str(conversation.id),
            message_text=user_message_content,
        )

        if ai_message is None:
            return

        from apps.usage.services import calculate_cost
        from apps.usage.tasks import save_usage_record

        provider = ai_event_data.get("provider", "") or usage.get("provider", "")
        model = ai_event_data.get("model", "") or usage.get("model", "")
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        cached_tokens = int(usage.get("cached_tokens", 0))
        reasoning_tokens = int(usage.get("reasoning_tokens", 0))

        cost_usd, cost_uzs = calculate_cost(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            stt_seconds=int(usage.get("stt_seconds", 0)),
            tts_chars=int(usage.get("tts_chars", 0)),
        )

        save_usage_record(
            session_id=conversation.session_id,
            user_id=str(conversation.user_id),
            tenant_id=tenant_id or str(conversation.tenant_id),
            conversation_id=str(conversation.id),
            message_id=str(ai_message.id),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            stt_seconds=int(usage.get("stt_seconds", 0)),
            tts_chars=int(usage.get("tts_chars", 0)),
            tool_calls_json=json.dumps(ai_event_data.get("tool_calls", [])),
            latency_ms=int(usage.get("latency_ms", 0)),
            cost_usd=cost_usd,
            cost_uzs=cost_uzs,
        )