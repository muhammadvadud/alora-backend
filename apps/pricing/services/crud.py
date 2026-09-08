from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.pricing.models import CalcRule, ServicePrice


def _as_decimal(value: Any) -> Decimal:
    """Qiymatni Decimal ga aylantiradi."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalized_items(items: Any) -> list[dict[str, Any]]:
    """PATCH payload ichidan elementlar ro'yxatini ajratadi."""

    if isinstance(items, Mapping):
        candidate = items.get("items", [items])
    else:
        candidate = items

    if candidate is None:
        return []
    if isinstance(candidate, list):
        return [dict(item) for item in candidate]
    if isinstance(candidate, tuple):
        return [dict(item) for item in candidate]
    if isinstance(candidate, Iterable) and not isinstance(candidate, (str, bytes)):
        return [dict(item) for item in candidate]
    return [dict(candidate)]


@transaction.atomic
def upsert_calc_rules(items: Any) -> list[CalcRule]:
    """Hisob qoidalarini yangilaydi yoki yaratadi."""

    normalized_items = _normalized_items(items)
    result: list[CalcRule] = []
    for item in normalized_items:
        key = str(item["key"])
        defaults = {
            "value": _as_decimal(item.get("value", Decimal("0"))),
            "unit": str(item.get("unit", "")),
            "description": str(item.get("description", "")),
            "applies_to": item.get("applies_to", {}) or {},
            "is_active": bool(item.get("is_active", True)),
        }
        rule, _ = CalcRule.objects.update_or_create(key=key, defaults=defaults)
        result.append(rule)
    return result


@transaction.atomic
def upsert_service_prices(items: Any) -> list[ServicePrice]:
    """Xizmat narxlarini yangilaydi yoki yaratadi."""

    normalized_items = _normalized_items(items)
    result: list[ServicePrice] = []
    for item in normalized_items:
        key = str(item["key"])
        defaults = {
            "name": str(item.get("name", "")),
            "price": _as_decimal(item.get("price", Decimal("0"))),
            "unit": str(item.get("unit", "")),
            "is_active": bool(item.get("is_active", True)),
        }
        service_price, _ = ServicePrice.objects.update_or_create(key=key, defaults=defaults)
        result.append(service_price)
    return result
