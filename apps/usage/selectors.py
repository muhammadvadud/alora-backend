"""Usage statistikasi uchun murakkab o'qish so'rovlari."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from django.apps import apps
from django.db.models import QuerySet, Sum
from django.db.models.functions import TruncDate
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
        rate = (Decimal(with_order) / Decimal(total) * Decimal(100)).quantize(Decimal("0.01"))
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


# --- Sotuv dashboard'i (16.8) -------------------------------------------------

# "Sotuv" — tasdiqlangan va undan keyingi bosqichdagi buyurtmalar (qoralama va
# bekor qilinganlar hisobga olinmaydi). Manager "bugun qancha sotildi" deganda
# aynan shu to'plamning summasini ko'radi.
SOLD_STATUSES: tuple[str, ...] = (
    "confirmed",
    "measuring",
    "production",
    "ready",
    "installing",
    "completed",
)
DASHBOARD_TOP_LIMIT = 5


def resolve_period(
    period: str, *, date_from: dt.date | None = None, date_to: dt.date | None = None
) -> tuple[dt.date, dt.date]:
    """Davr nomini (`day|week|month|custom`) sana oralig'iga aylantiradi.

    `custom` uchun `date_from`/`date_to` majburiy (validatsiya serializer'da);
    `date_to` berilmasa bugun olinadi.
    """

    today = timezone.localdate()
    if period == "custom" and date_from is not None:
        return date_from, date_to or today
    if period == "week":
        return today - dt.timedelta(days=today.weekday()), today
    if period == "month":
        return today.replace(day=1), today
    return today, today


def get_sales_dashboard(
    tenant: Any, *, period: str, date_from: dt.date | None = None, date_to: dt.date | None = None
) -> dict[str, Any]:
    """Menejer dashboard'i: buyurtmalar, sotuv summasi, suhbatlar, AI xarajati.

    Barcha bloklar bitta davr bo'yicha (`created_at` sanasi) yig'iladi va oldingi
    xuddi shunday uzunlikdagi davr bilan taqqoslanadi. AI xarajati `UsageDaily`
    rollup'idan olinadi (9.11 qoidasi), qolgani `orders`/`chat` modellaridan.
    """

    from django.db.models import Avg, Count, Q

    Order = apps.get_model("orders", "Order")
    OrderCurtainPart = apps.get_model("orders", "OrderCurtainPart")
    Conversation = apps.get_model("chat", "Conversation")

    start, end = resolve_period(period, date_from=date_from, date_to=date_to)
    length = (end - start).days + 1
    prev_start, prev_end = start - dt.timedelta(days=length), start - dt.timedelta(days=1)

    def orders_in(s: dt.date, e: dt.date) -> Any:
        return Order.objects.filter(tenant=tenant, created_at__date__gte=s, created_at__date__lte=e)

    def conversations_in(s: dt.date, e: dt.date) -> Any:
        return Conversation.objects.filter(
            tenant=tenant, created_at__date__gte=s, created_at__date__lte=e
        )

    orders_qs = orders_in(start, end)
    sold_qs = orders_qs.filter(status__in=SOLD_STATUSES)

    # Buyurtmalar: holatlar bo'yicha sonlar.
    by_status = {
        row["status"]: row["n"] for row in orders_qs.values("status").annotate(n=Count("id"))
    }
    orders_block = {
        "created": sum(by_status.values()),
        "sold": sold_qs.count(),
        "completed": by_status.get("completed", 0),
        "cancelled": by_status.get("cancelled", 0),
        "draft": by_status.get("draft", 0),
        "in_progress": sum(by_status.get(s, 0) for s in SOLD_STATUSES if s != "completed"),
        "by_status": by_status,
    }

    # Sotuv summalari.
    money = sold_qs.aggregate(
        revenue=Sum("total"),
        prepayment=Sum("prepayment"),
        balance=Sum("balance"),
        discount=Sum("discount_amount"),
        delivery=Sum("delivery_amount"),
        average=Avg("total"),
    )
    sales_block = {
        "revenue": _as_decimal(money["revenue"]),
        "prepayment": _as_decimal(money["prepayment"]),
        "balance_due": _as_decimal(money["balance"]),
        "discount_total": _as_decimal(money["discount"]),
        "delivery_total": _as_decimal(money["delivery"]),
        "average_check": _as_decimal(money["average"]),
    }

    # Suhbatlar va konversiya.
    conv_qs = conversations_in(start, end)
    conv_total = conv_qs.count()
    conv_with_order = conv_qs.filter(order__isnull=False).count()
    rate = Decimal(0)
    if conv_total:
        rate = (Decimal(conv_with_order) / Decimal(conv_total) * 100).quantize(Decimal("0.01"))
    conversations_block = {
        "total": conv_total,
        "with_order": conv_with_order,
        "conversion_rate": str(rate),
    }

    # AI xarajati — rollup jadvalidan.
    ai = get_usage_daily_queryset(tenant, start=start, end=end).aggregate(
        tokens=Sum("tokens"), cost=Sum("cost_uzs"), messages=Sum("messages_count")
    )
    ai_block = {
        "tokens": int(ai["tokens"] or 0),
        "cost_uzs": _as_decimal(ai["cost"]),
        "messages": int(ai["messages"] or 0),
    }

    # Eng ko'p sotilgan matolar (sotilgan buyurtmalardagi parda qismlari).
    top_products = [
        {
            "variant_id": str(row["variant_id"]),
            "sku": row["variant__sku"],
            "name": row["variant__product__name"],
            "color_name": row["variant__color_name"],
            "area_sqm": str(Decimal(row["area"] or 0).quantize(Decimal("0.001"))),
            "revenue": _as_decimal(row["revenue"]),
            "orders": row["orders"],
        }
        for row in OrderCurtainPart.objects.filter(measurement__order__in=sold_qs)
        .values("variant_id", "variant__sku", "variant__product__name", "variant__color_name")
        .annotate(
            area=Sum("area_sqm"),
            revenue=Sum("total"),
            orders=Count("measurement__order", distinct=True),
        )
        .order_by("-revenue")[:DASHBOARD_TOP_LIMIT]
    ]

    # Xodimlar bo'yicha: yaratgan buyurtmalari va sotuv summasi.
    by_user = [
        {
            "user_id": str(row["user_id"]),
            "full_name": row["user__full_name"],
            "orders": row["orders"],
            "sold": row["sold"],
            "revenue": _as_decimal(row["revenue"]),
        }
        for row in orders_qs.values("user_id", "user__full_name")
        .annotate(
            orders=Count("id"),
            sold=Count("id", filter=Q(status__in=SOLD_STATUSES)),
            revenue=Sum("total", filter=Q(status__in=SOLD_STATUSES)),
        )
        .order_by("-revenue", "-orders")
    ]

    # Kunlik qator (grafik uchun) — davr ichidagi har bir kun, bo'sh kunlar 0.
    daily_rows = {
        row["day"]: row
        for row in sold_qs.values(day=TruncDate("created_at"))
        .annotate(orders=Count("id"), revenue=Sum("total"))
        .order_by("day")
    }
    created_rows = {
        row["day"]: row["n"]
        for row in orders_qs.values(day=TruncDate("created_at")).annotate(n=Count("id"))
    }
    daily = []
    for i in range(length):
        day = start + dt.timedelta(days=i)
        row = daily_rows.get(day)
        daily.append(
            {
                "date": day.isoformat(),
                "orders_created": created_rows.get(day, 0),
                "orders_sold": row["orders"] if row else 0,
                "revenue": _as_decimal(row["revenue"] if row else None),
            }
        )

    # Oldingi davr bilan taqqoslash.
    prev_orders = orders_in(prev_start, prev_end)
    prev_money = prev_orders.filter(status__in=SOLD_STATUSES).aggregate(revenue=Sum("total"))
    prev_revenue = prev_money["revenue"] or Decimal(0)
    prev_orders_count = prev_orders.count()
    prev_block = {
        "date_from": prev_start.isoformat(),
        "date_to": prev_end.isoformat(),
        "orders_created": prev_orders_count,
        "revenue": _as_decimal(prev_revenue),
        "conversations": conversations_in(prev_start, prev_end).count(),
        "orders_change_pct": _change_pct(orders_block["created"], prev_orders_count),
        "revenue_change_pct": _change_pct(money["revenue"] or Decimal(0), prev_revenue),
    }

    return {
        "period": period,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "orders": orders_block,
        "sales": sales_block,
        "conversations": conversations_block,
        "ai": ai_block,
        "top_products": top_products,
        "by_user": by_user,
        "daily": daily,
        "previous": prev_block,
    }


def _change_pct(current: Any, previous: Any) -> str | None:
    """Oldingi davrga nisbatan o'zgarish foizi; oldingi 0 bo'lsa `None`."""

    previous = Decimal(str(previous or 0))
    if previous == 0:
        return None
    current = Decimal(str(current or 0))
    return str(((current - previous) / previous * 100).quantize(Decimal("0.01")))
