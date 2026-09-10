"""Buyurtma o'qish so'rovlari (selektorlar)."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from apps.orders.models import Order


def get_orders() -> QuerySet[Order]:
    """Buyurtmalarni N+1'siz yuklaydi.

    O'lchovlar, bo'laklar, aksessuarlar va xizmat qatorlari prefetch
    qilinadi; variant va foydalanuvchi ma'lumotlari select_related orqali.
    """

    return Order.objects.select_related("user", "conversation", "confirmed_by").prefetch_related(
        "measurements",
        "measurements__parts__variant__product",
        "measurements__accessories__variant__product",
        "items",
    )


def get_order(order_pk: Any) -> Order:
    """Bitta buyurtmani to'liq holda qaytaradi."""

    return get_orders().get(pk=order_pk)
