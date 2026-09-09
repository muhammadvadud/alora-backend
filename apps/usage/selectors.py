"""Usage statistikasi uchun murakkab o'qish so'rovlari."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from django.apps import apps
from django.db.models import QuerySet, Sum
from django.utils import timezone

from apps.usage.models import UsageDaily, UsageRecord

MONEY_DECIMAL_PLACES = 2


def get_usage_daily_queryset(tenant: Any, *, start: dt.date, end: dt.date) -> QuerySet[UsageDaily]:
    """Ma'lum muddat uchun `UsageDaily` querysetini qaytaradi.

    Statistika faqat rollup jadvalidan o'qiladi (xom `UsageRecord` dan emas).
    """

    return UsageDaily.objects.filter(tenant=tenant, date__gte=start, date__lte=end)


def get_summary(tenant: Any, *, period: str, user: Any | None = None) -> dict[str, Any]:
    """Kunlik / haftalik / oylik foydalanish xulosasi.

    `UsageDaily` rollup'i `created_at` dan emas, `date` maydoni bo'yicha yig'iladi.
    """

    today = timezone.localdate()
    if period == "week":
        start = today - dt.timedelta(days=today.weekday())
        end = today
    elif period == "month":
        start = today.replace(day=1)
        end = today
    else:
        start = today
        end = today

    queryset = get_usage_daily_queryset(tenant, start=start, end=end)
    if user is not None:
        queryset = queryset.filter(user=user)

    aggregate = queryset.aggregate(
        total_tokens=Sum("tokens"),
        total_cost=Sum("cost_uzs"),
        total_messages=Sum("messages_count"),
        total_conversations=Sum("conversations_count"),
    )
    return {
        "period": period,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "tokens": int(aggregate.get("total_tokens") or 0),
        "cost_uzs": _as_decimal(aggregate.get("total_cost")),
        "messages": int(aggregate.get("total_messages") or 0),
        "conversations": int(aggregate.get("total_conversations") or 0),
    }


def get_by_user(tenant: Any, *, period: str) -> list[dict[str, Any]]:
    """Xodimlar bo'yicha reyting — `UsageDaily` dan yig'iladi."""

    today = timezone.localdate()
    if period == "week":
        start = today - dt.timedelta(days=today.weekday())
        end = today
    elif period == "month":
        start = today.replace(day=1)
        end = today
    else:
        start = today
        end = today

    rows = (
        get_usage_daily_queryset(tenant, start=start, end=end)
        .values("user_id", "user__full_name")
        .annotate(
            tokens=Sum("tokens"),
            cost_uzs=Sum("cost_uzs"),
            messages=Sum("messages_count"),
            conversations=Sum("conversations_count"),
        )
        .order_by("-cost_uzs")
    )

    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "user_id": str(row["user_id"]),
                "full_name": row.get("user__full_name"),
                "tokens": int(row.get("tokens") or 0),
                "cost_uzs": _as_decimal(row.get("cost_uzs")),
                "messages": int(row.get("messages") or 0),
                "conversations": int(row.get("conversations") or 0),
            }
        )
    return result


def get_most_expensive_conversations(tenant: Any, *, limit: int = 20) -> list[dict[str, Any]]:
    """Eng qimmat suhbatlar — `UsageRecord` dan suhbat bo'yicha yig'iladi."""

    rows = (
        UsageRecord.objects.filter(tenant=tenant, conversation__isnull=False)
        .values("conversation")
        .annotate(cost_uzs=Sum("cost_uzs"), tokens=Sum("prompt_tokens") + Sum("completion_tokens"))
        .order_by("-cost_uzs")[:limit]
    )

    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "conversation_id": str(row["conversation"]),
                "cost_uzs": _as_decimal(row.get("cost_uzs")),
                "tokens": int(row.get("tokens") or 0),
                "messages": UsageRecord.objects.filter(
                    tenant=tenant, conversation=row["conversation"]
                ).count(),
            }
        )
    return result


def get_users_today_activity(tenant: Any, user_ids: list[Any]) -> dict[str, dict[str, Any]]:
    """Berilgan xodimlar uchun bugungi faollikni `UsageDaily` dan qaytaradi.

    Natija: `{user_id: {"tokens": int, "messages": int, "conversations": int}}`.
    Faollik yo'q bo'lgan xodim uchun nol qiymatlar qaytadi.
    """

    today = timezone.localdate()
    rows = (
        UsageDaily.objects.filter(tenant=tenant, user_id__in=user_ids, date=today)
        .values("user_id")
        .annotate(
            tokens=Sum("tokens"),
            messages=Sum("messages_count"),
            conversations=Sum("conversations_count"),
        )
    )
    activity: dict[str, dict[str, Any]] = {
        str(uid): {"tokens": 0, "messages": 0, "conversations": 0} for uid in user_ids
    }
    for row in rows:
        activity[str(row["user_id"])] = {
            "tokens": int(row.get("tokens") or 0),
            "messages": int(row.get("messages") or 0),
            "conversations": int(row.get("conversations") or 0),
        }
    return activity


def get_conversion_stats(tenant: Any) -> dict[str, Any]:
    """Suhbat → buyurtma konversiyasini qaytaradi.

    `orders.Order` va `chat.Conversation` modellari hali mavjud bo'lmasa
    bo'sh natija qaytadi (kech bog'lanish).
    """

    Order = apps.get_model("orders", "Order")
    Conversation = apps.get_model("chat", "Conversation")
    if Order is None or Conversation is None:
        return {
            "total_conversations": 0,
            "with_order": 0,
            "conversion_rate": "0.00",
        }

    total = Conversation.objects.filter(tenant=tenant).count()
    with_order = (
        Conversation.objects.filter(tenant=tenant, order__isnull=False).distinct().count()
        if any(field.name == "order" for field in Conversation._meta.get_fields())
        else 0
    )
    rate = Decimal(0)
    if total:
        rate = (Decimal(with_order) / Decimal(total) * Decimal(100)).quantize(
            Decimal("0.01")
        )
    return {
        "total_conversations": total,
        "with_order": with_order,
        "conversion_rate": str(rate),
    }


def _as_decimal(value: Any) -> str:
    """Sum ma'lumotini 2 kasrli matnga keltiradi."""

    if value is None:
        value = Decimal(0)
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(value.quantize(Decimal("0.01")))