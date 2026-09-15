"""Usage ilovasi uchun Celery tasklari — statistika va limit nazorati."""

from __future__ import annotations

import datetime as dt
import json
import uuid
from decimal import Decimal
from typing import Any

import structlog
from celery import shared_task
from django.apps import apps
from django.db.models import Count, F, Sum
from django.utils import timezone

from apps.usage.models import UsageDaily, UsageLimit, UsageRecord

logger = structlog.get_logger(__name__)

MONEY_PLACES = Decimal("0.01")


def _parse_json(raw: str, fallback: Any) -> Any:
    """JSON matnini xavfsiz parse qiladi."""
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return fallback


def _to_decimal(value: Any) -> Decimal:
    """Qiymatni 2 kasrli Decimal ga aylantiradi."""
    if isinstance(value, Decimal):
        return value.quantize(MONEY_PLACES)
    try:
        return Decimal(str(value)).quantize(MONEY_PLACES)
    except (TypeError, ValueError):
        return Decimal("0.00")


def _as_uuid(value: str) -> uuid.UUID | None:
    """Matndan UUID yasaydi; noto'g'ri bo'lsa None qaytaradi."""
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _parse_date(value: Any) -> dt.date | None:
    """ISO sana matni yoki date obyektidan sana qaytaradi."""
    if value in (None, ""):
        return None
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _user(backend_user_id: str) -> Any | None:
    """Foydalanuvchini o'sha id bo'yicha qaytaradi yoki None."""
    if not backend_user_id:
        return None
    User = apps.get_model("accounts", "User")
    return User.objects.filter(pk=backend_user_id).only("pk", "tenant_id", "role").first()


def _tenant_exists(backend_tenant_id: str) -> bool:
    """Tenant bazada mavjudligini tekshiradi."""
    if not backend_tenant_id:
        return False
    Tenant = apps.get_model("accounts", "Tenant")
    return Tenant.objects.filter(pk=backend_tenant_id).exists()


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def save_usage_record(
    self,
    *,
    session_id: str = "",
    user_id: str = "",
    tenant_id: str = "",
    conversation_id: str = "",
    message_id: str = "",
    provider: str = "",
    model: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_tokens: int = 0,
    reasoning_tokens: int = 0,
    stt_seconds: int = 0,
    tts_chars: int = 0,
    tool_calls_json: str = "[]",
    latency_ms: int = 0,
    cost_usd: float | Decimal = 0,
    cost_uzs: float | Decimal = 0,
) -> str | None:
    """AI javobidan keyin foydalanish qaydnomasini saqlaydi. · 13.1

    Idempotent: `message_id` berilganda u bo'yicha ilgari yozuv bo'lsa
    yangi yozuv yaratilmaydi, mavjud yozuv yangilanadi. Foydalanuvchi
    yoki tenant topilmasa hech narsa yozilmaydi (qaytadan urinishdan
    takror yozuv paydo bo'lmaydi).
    """
    user = _user(user_id)
    if user is None:
        logger.warning("usage_record_user_not_found", user_id=user_id, session_id=session_id)
        return None

    tenant_id = tenant_id or str(user.tenant_id or "")
    if not _tenant_exists(tenant_id):
        logger.warning("usage_record_tenant_not_found", tenant_id=tenant_id, session_id=session_id)
        return None

    defaults = {
        "conversation": _as_uuid(conversation_id),
        "message_id": _as_uuid(message_id),
        "provider": provider or "",
        "model": model or "",
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "cached_tokens": int(cached_tokens or 0),
        "reasoning_tokens": int(reasoning_tokens or 0),
        "stt_seconds": int(stt_seconds or 0),
        "tts_chars": int(tts_chars or 0),
        "tool_calls": _parse_json(tool_calls_json, []),
        "latency_ms": int(latency_ms or 0),
        "cost_usd": _to_decimal(cost_usd),
        "cost_uzs": _to_decimal(cost_uzs),
    }

    message_uuid = _as_uuid(message_id)
    if message_uuid:
        record, created = UsageRecord.objects.get_or_create(
            user=user,
            tenant_id=tenant_id,
            message_id=message_uuid,
            defaults=defaults,
        )
        if not created:
            for field, value in defaults.items():
                setattr(record, field, value)
            record.save()
        return str(record.pk)  # Celery natijasi JSON — model obyekti serializatsiya bo'lmaydi

    return str(UsageRecord.objects.create(user=user, tenant_id=tenant_id, **defaults).pk)


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def daily_usage_rollup(self, date: str | None = None, tenant_id: str = "") -> int:
    """`UsageRecord`'larni `UsageDaily` kunlik yig'masiga jamlaydi. · 13.4

    Sana berilmasa kecha hisoblanadi (beat 00:05 da yurgizadi). Idempotent:
    `update_or_create` orqali qayta hisoblash o'tkaziladi — ikki marta ishlasa
    ham bitta to'g'ri yozuv qoladi, takror yozuv yaratilmaydi.
    """
    target_date = _parse_date(date) or (timezone.localdate() - dt.timedelta(days=1))

    start = dt.datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        tzinfo=timezone.get_current_timezone(),
    )
    end = start + dt.timedelta(days=1)

    rows = (
        UsageRecord.objects.filter(created_at__gte=start, created_at__lt=end)
        .values("tenant_id", "user_id")
        .annotate(
            tokens=Sum(
                F("prompt_tokens")
                + F("completion_tokens")
                + F("cached_tokens")
                + F("reasoning_tokens")
            ),
            cost_uzs=Sum("cost_uzs"),
            messages_count=Count("id"),
            conversations_count=Count("conversation", distinct=True),
        )
    )
    if tenant_id:
        rows = rows.filter(tenant_id=tenant_id)

    updated = 0
    for row in rows:
        UsageDaily.objects.update_or_create(
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            date=target_date,
            defaults={
                "tokens": int(row["tokens"] or 0),
                "cost_uzs": _to_decimal(row["cost_uzs"]),
                "messages_count": int(row["messages_count"] or 0),
                "conversations_count": int(row["conversations_count"] or 0),
            },
        )
        updated += 1

    logger.info("usage_daily_rollup_done", date=str(target_date), rows=updated)
    return updated


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def check_limits_and_notify(self) -> dict[str, int]:
    """Har soatda limit oshgan xodimlarni aniqlab ogohlantiradi. · 13.6

    Ogohlantirish kanali (SMS/push) hozircha yo'q — `structlog` orqali
    warning darajasida e'lon qilinadi. Idempotent: faqat o'qish va log,
    ma'lumotlar bazasi yozuvlari o'zgarmaydi.
    """
    from django.apps import apps

    from apps.usage.services import check_usage_limit

    User = apps.get_model("accounts", "User")

    checked = 0
    blocked = 0
    seen: set[str] = set()

    limits = UsageLimit.objects.filter(is_active=True).select_related("user")
    for limit in limits:
        if limit.user_id:
            targets: list[Any] = [limit.user]
        elif limit.role:
            targets = list(User.objects.filter(role=limit.role, is_active=True).only("id"))
        else:
            targets = []

        for user in targets:
            if user is None or str(user.pk) in seen:
                continue
            seen.add(str(user.pk))
            checked += 1
            result = check_usage_limit(user)
            if result.blocked:
                blocked += 1
                logger.warning(
                    "usage_limit_exceeded",
                    user_id=str(user.pk),
                    period=result.period,
                    reason=result.reason,
                )

    logger.info("usage_limits_checked", checked=checked, blocked=blocked)
    return {"checked": checked, "blocked": blocked}
